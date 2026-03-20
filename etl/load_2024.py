"""ETL loader for 2024 data.

2024 has no individual registration or room data — only:
- Dashboard snapshots (gp2024_event_dashboard.xlsx)
- Aggregated food scanning data (gp2024_scanning_analysis.xlsx)
"""

import logging
import json
from .db import get_cursor, get_or_create_event
from .xlsx_utils import open_workbook, safe_str, safe_int, safe_float, safe_date

log = logging.getLogger(__name__)


def load_dashboard_2024():
    """Load 2024 dashboard snapshots.

    The 2024 dashboard has complex multi-section layouts per sheet.
    We parse recognizable structures and store them as dashboard_snapshots.
    """
    filename = "gp2024_event_dashboard.xlsx"
    log.info(f"Loading 2024 dashboard from {filename}...")

    wb = open_workbook(filename)
    count = 0

    with get_cursor() as cur:
        for sheet_name in wb.sheetnames:
            ws = wb[sheet_name]
            rows = []
            for row in ws.iter_rows():
                rows.append([c.value for c in row])

            if not rows:
                continue

            # Parse each sheet as key-value pairs or table sections
            snapshot_rows = _parse_dashboard_sheet(rows, sheet_name)
            for sr in snapshot_rows:
                cur.execute(
                    """INSERT INTO dashboard_snapshots
                       (event_year, snapshot_type, snapshot_date, dimension_key,
                        dimension_value, metric_name, metric_value, raw_json,
                        source_file, source_sheet)
                       VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                    (
                        2024, sr["type"], sr.get("date"),
                        sr.get("dim_key"), sr.get("dim_value"),
                        sr["metric"], sr.get("value"),
                        json.dumps(sr.get("raw")) if sr.get("raw") else None,
                        filename, sheet_name,
                    ),
                )
                count += 1

    wb.close()
    log.info(f"  2024 dashboard: {count} snapshot rows loaded")


def _parse_dashboard_sheet(rows, sheet_name):
    """Parse a dashboard sheet into snapshot records.

    Strategy: walk rows, look for header-like rows (cells with text and adjacent
    cells with dates or numbers), then extract the data below them.
    """
    results = []
    i = 0
    while i < len(rows):
        row = rows[i]
        first_cell = row[0] if row else None

        if first_cell is None:
            i += 1
            continue

        cell_str = str(first_cell).strip()

        # Check if this row looks like a section header
        if cell_str and not _is_numeric(cell_str):
            # Try to find a small data table below this header
            section_rows = _extract_section(rows, i, sheet_name)
            results.extend(section_rows)

        i += 1

    return results


def _extract_section(rows, start_idx, sheet_name):
    """Extract a data section starting at start_idx."""
    results = []
    header_row = rows[start_idx]
    section_title = str(header_row[0]).strip() if header_row[0] else sheet_name

    # Look at next row for sub-headers or data
    for j in range(start_idx + 1, min(start_idx + 50, len(rows))):
        row = rows[j]
        if all(c is None for c in row):
            break

        # Extract non-None values as metric entries
        dim_key = safe_str(row[0])
        if not dim_key:
            continue

        for k in range(1, len(row)):
            val = row[k]
            if val is not None and _is_numeric_val(val):
                results.append({
                    "type": section_title[:100],
                    "dim_key": dim_key[:200],
                    "dim_value": None,
                    "metric": f"col_{k}",
                    "value": safe_float(val),
                    "date": safe_date(val) if not _is_numeric_val(val) else None,
                })

    return results


def _is_numeric(s):
    try:
        float(str(s).replace(",", ""))
        return True
    except (ValueError, TypeError):
        return False


def _is_numeric_val(v):
    if isinstance(v, (int, float)):
        return True
    return _is_numeric(v)


def load_scanning_2024():
    """Load 2024 food scanning analysis (aggregated meal counts).

    gp2024_scanning_analysis.xlsx has:
    - 'Food Consumed Stats - 1': daily meal counts by food type
    - 'Food Consumed Stats - 2': meal conflict matrices
    """
    filename = "gp2024_scanning_analysis.xlsx"
    log.info(f"Loading 2024 scanning analysis from {filename}...")

    wb = open_workbook(filename)
    count = 0

    with get_cursor() as cur:
        event_id = get_or_create_event(2024)

        # Sheet 1: Food Consumed Stats
        ws = wb['Food Consumed Stats - 1']
        all_rows = []
        for row in ws.iter_rows():
            all_rows.append([c.value for c in row])

        # Parse the repeated date-header blocks
        meal_rows = _parse_food_stats_1(all_rows)
        for mr in meal_rows:
            cur.execute(
                """INSERT INTO meal_aggregates
                   (event_id, event_year, meal_date, food_type,
                    breakfast_count, lunch_count, tea_break_count, dinner_count,
                    total_count, source_file, source_sheet)
                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                (
                    event_id, 2024, mr.get("date"), mr.get("food_type"),
                    mr.get("breakfast"), mr.get("lunch"),
                    mr.get("tea_break"), mr.get("dinner"),
                    mr.get("total"),
                    filename, "Food Consumed Stats - 1",
                ),
            )
            count += 1

        # Sheet 2: Meal conflict matrices
        ws = wb['Food Consumed Stats - 2']
        all_rows = []
        for row in ws.iter_rows():
            all_rows.append([c.value for c in row])

        conflict_rows = _parse_food_stats_2(all_rows)
        for cr in conflict_rows:
            cur.execute(
                """INSERT INTO meal_aggregates
                   (event_id, event_year, meal_date, food_type,
                    meal_conflicts, source_file, source_sheet)
                   VALUES (%s,%s,%s,%s,%s,%s,%s)""",
                (
                    event_id, 2024, cr.get("date"), cr.get("food_type"),
                    json.dumps(cr.get("conflicts")) if cr.get("conflicts") else None,
                    filename, "Food Consumed Stats - 2",
                ),
            )
            count += 1

    wb.close()
    log.info(f"  2024 scanning: {count} aggregate rows loaded")


def _parse_food_stats_1(rows):
    """Parse food consumed stats sheet 1.

    Format: repeated blocks with a header like "Food consumed by Meal for MM/DD/YYYY"
    followed by rows with food type and counts.
    """
    results = []
    current_date = None
    current_meal = None
    in_data = False

    for row in rows:
        if not row:
            continue
        first_val = str(row[0]).strip() if row[0] else ""

        # Check for date header
        if "Food consumed by Meal for" in first_val:
            try:
                date_str = first_val.split("for")[-1].strip()
                current_date = safe_date(date_str)
            except Exception:
                pass
            in_data = False
            continue

        # Check for meal type sub-header (Breakfast, Lunch, etc.)
        if first_val in ("Breakfast", "Lunch", "Tea Break", "Dinner"):
            current_meal = first_val
            in_data = True
            continue

        # Check for food type data row
        if in_data and current_date and first_val and first_val not in ("Total", "Grand Total", ""):
            food_type = first_val
            count = safe_int(row[1]) if len(row) > 1 else None
            if count is not None:
                entry = {
                    "date": current_date,
                    "food_type": food_type,
                    "total": count,
                }
                # Map meal type to the right column
                if current_meal == "Breakfast":
                    entry["breakfast"] = count
                elif current_meal == "Lunch":
                    entry["lunch"] = count
                elif current_meal == "Tea Break":
                    entry["tea_break"] = count
                elif current_meal == "Dinner":
                    entry["dinner"] = count
                results.append(entry)

        if first_val == "" or first_val == "Total":
            in_data = False

    return results


def _parse_food_stats_2(rows):
    """Parse meal conflict matrices from sheet 2."""
    results = []
    current_date = None
    current_meals = None
    header_row = None

    for row in rows:
        if not row:
            continue
        first_val = str(row[0]).strip() if row[0] else ""

        # Check for conflict header
        if "Meal Conflicts for" in first_val:
            parts = first_val.split("for")[-1].strip()
            try:
                # "MM/DD/YYYY - MealType"
                date_part = parts.split("-")[0].strip()
                current_date = safe_date(date_part)
                current_meals = parts.split("-")[-1].strip() if "-" in parts else None
            except Exception:
                pass
            header_row = None
            continue

        # The next row after header is the column labels
        if current_date and header_row is None and first_val:
            header_row = [str(c).strip() if c else "" for c in row]
            continue

        # Data rows
        if header_row and first_val and first_val not in ("", "Total"):
            conflicts = {}
            for k in range(1, len(row)):
                if k < len(header_row) and row[k] and header_row[k]:
                    conflicts[header_row[k]] = safe_int(row[k])
            if conflicts:
                results.append({
                    "date": current_date,
                    "food_type": first_val,
                    "conflicts": conflicts,
                })

    return results


def load_year_2024():
    """Load all 2024 data."""
    load_dashboard_2024()
    load_scanning_2024()
