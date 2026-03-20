"""Seed reference tables and data_availability from xlsx data."""

import logging
from .db import get_cursor, get_or_create_event
from .xlsx_utils import (
    open_workbook, safe_str, normalize_food_pref, normalize_gender,
)

log = logging.getLogger(__name__)

# Region mapping: legacy numeric IDs → region codes/names
# Derived from cross-referencing 2022 numeric regionIDs with 2025 string regions
REGION_MAP = {
    101: ("NC", "North Central"),
    102: ("NE", "North East"),
    103: ("SC", "South Central"),
    104: ("SE", "South East"),
    105: ("W", "Western USA"),
    106: ("CA", "Canada"),
    107: ("ROW", "ROW"),  # Rest of World
}

# 2025 string regions → codes
REGION_NAME_TO_CODE = {
    "North Central": "NC",
    "North East": "NE",
    "South Central": "SC",
    "South East": "SE",
    "Western USA": "W",
    "Canada": "CA",
    "India": "IN",
    "ROW": "ROW",
}

FOOD_PREF_MAP = {
    "R": ("R", "Regular Indian"),
    "J": ("J", "Jain Indian"),
    "RW": ("RW", "Regular Western"),
    "JW": ("JW", "Jain Western"),
    "W": ("W", "Western"),
    # Long-form 2022 values
    "Regular Indian Food (Lunch & Dinner)": ("R", "Regular Indian"),
    "Jain Indian Food - Mild Spice (Lunch & Dinner)": ("J", "Jain Indian"),
    "Western Food (Dinner) & Jain Indian Food - Mild Spice (Lunch)": ("JW", "Jain Western"),
    "Western Food (Dinner) & Regular Indian Food (Lunch)": ("RW", "Regular Western"),
}

AGE_GROUP_MAP = {
    # 2025 string groups
    "<4": ("LT4", 0, 3, "Under 4"),
    "4-12": ("4-12", 4, 12, "BMHT/LMHT (4-12)"),
    "13-17": ("13-17", 13, 17, "YMHT (13-17)"),
    "18-34": ("18-34", 18, 34, "Young Adult (18-34)"),
    "35-59": ("35-59", 35, 59, "Adult (35-59)"),
    "60-70": ("60-70", 60, 70, "Senior (60-70)"),
    "70+": ("70PLUS", 70, 120, "Senior 70+"),
    # 2022 pivot codes
    "BMHT": ("BMHT", 0, 5, "Baby MHT"),
    "LMHT": ("LMHT", 4, 12, "Little MHT"),
    "YMHT": ("YMHT", 13, 17, "Young MHT"),
    "YMHTPlus": ("YMHT+", 18, 34, "Young MHT Plus"),
    "MHT": ("MHT", 35, 59, "Mahatma"),
    "SMHT": ("SMHT", 60, 70, "Senior MHT"),
    "SMHTPlus": ("SMHT+", 70, 120, "Senior MHT Plus"),
}


def seed_regions(cur):
    """Seed ref_regions from the known region mapping."""
    log.info("Seeding ref_regions...")
    count = 0
    all_regions = {}
    for legacy_id, (code, name) in REGION_MAP.items():
        all_regions[code] = (name, legacy_id)
    # Add India (not in legacy)
    if "IN" not in all_regions:
        all_regions["IN"] = ("India", None)

    for code, (name, legacy_id) in all_regions.items():
        cur.execute(
            "INSERT INTO ref_regions (region_code, region_name, legacy_id) "
            "VALUES (%s, %s, %s) ON CONFLICT (region_code) DO NOTHING",
            (code, name, legacy_id),
        )
        count += 1
    log.info(f"  Seeded {count} regions")


def seed_food_preferences(cur):
    """Seed ref_food_preferences."""
    log.info("Seeding ref_food_preferences...")
    seen = set()
    count = 0
    for raw, (code, label) in FOOD_PREF_MAP.items():
        if code in seen:
            continue
        seen.add(code)
        cur.execute(
            "INSERT INTO ref_food_preferences (code, label) "
            "VALUES (%s, %s) ON CONFLICT (code) DO NOTHING",
            (code, label),
        )
        count += 1
    log.info(f"  Seeded {count} food preferences")


def seed_age_groups(cur):
    """Seed ref_age_groups."""
    log.info("Seeding ref_age_groups...")
    seen = set()
    count = 0
    for raw, (code, mn, mx, label) in AGE_GROUP_MAP.items():
        if code in seen:
            continue
        seen.add(code)
        cur.execute(
            "INSERT INTO ref_age_groups (group_code, min_age, max_age, label) "
            "VALUES (%s, %s, %s, %s) ON CONFLICT (group_code) DO NOTHING",
            (code, mn, mx, label),
        )
        count += 1
    log.info(f"  Seeded {count} age groups")


def seed_room_types_from_data(cur):
    """Seed ref_room_types by scanning xlsx data for distinct values."""
    log.info("Seeding ref_room_types from xlsx data...")
    room_types = set()

    # 2025 rooms
    wb = open_workbook("gp2025_registrations.xlsx")
    ws = wb['Rooms']
    for i, row in enumerate(ws.iter_rows()):
        if i == 0:
            continue
        vals = [c.value for c in row]
        if vals[5]:
            room_types.add(str(vals[5]).strip())
        if vals[19]:
            room_types.add(str(vals[19]).strip())
    wb.close()

    # 2025 room analysis
    wb = open_workbook("gp2025_room_analysis.xlsx")
    ws = wb['Data']
    for i, row in enumerate(ws.iter_rows()):
        if i == 0:
            continue
        vals = [c.value for c in row]
        if vals[5]:
            room_types.add(str(vals[5]).strip())
        if vals[16]:
            room_types.add(str(vals[16]).strip())
    wb.close()

    # 2022 registrations
    wb = open_workbook("gp2022_registrations_and_room_pickups.xlsx")
    ws = wb['Registration-CheckIn-RoomAcc by']
    for i, row in enumerate(ws.iter_rows()):
        if i == 0:
            continue
        vals = [c.value for c in row]
        if vals[46]:
            room_types.add(str(vals[46]).strip())
        if vals[51]:
            room_types.add(str(vals[51]).strip())
    wb.close()

    # 2023 registrations
    wb = open_workbook("gp2023_event_registrations_and_room_pickups.xlsx")
    ws = wb['Registration-CheckIn-RoomAcc by']
    for i, row in enumerate(ws.iter_rows()):
        if i == 0:
            continue
        vals = [c.value for c in row]
        if vals[46]:
            room_types.add(str(vals[46]).strip())
        if vals[51]:
            room_types.add(str(vals[51]).strip())
    wb.close()

    count = 0
    for rt in sorted(room_types):
        code = rt[:50]
        cur.execute(
            "INSERT INTO ref_room_types (type_code, type_name) "
            "VALUES (%s, %s) ON CONFLICT (type_code) DO NOTHING",
            (code, rt),
        )
        count += 1
    log.info(f"  Seeded {count} room types")


def seed_hotels_from_data(cur):
    """Seed ref_hotels by scanning xlsx data for distinct hotel names."""
    log.info("Seeding ref_hotels from xlsx data...")
    hotels = set()

    # 2025
    wb = open_workbook("gp2025_registrations.xlsx")
    ws = wb['Rooms']
    for i, row in enumerate(ws.iter_rows()):
        if i == 0:
            continue
        vals = [c.value for c in row]
        if vals[20]:
            hotels.add(str(vals[20]).strip())
    wb.close()

    wb = open_workbook("gp2025_room_analysis.xlsx")
    ws = wb['Data']
    for i, row in enumerate(ws.iter_rows()):
        if i == 0:
            continue
        vals = [c.value for c in row]
        if vals[17]:
            hotels.add(str(vals[17]).strip())
    wb.close()

    # 2022
    wb = open_workbook("gp2022_registrations_and_room_pickups.xlsx")
    ws = wb['Room Stats - Booked vs Pickedup']
    for i, row in enumerate(ws.iter_rows()):
        if i == 0:
            continue
        vals = [c.value for c in row]
        if vals[13]:
            hotels.add(str(vals[13]).strip())
    wb.close()

    # 2023
    wb = open_workbook("gp2023_event_registrations_and_room_pickups.xlsx")
    ws = wb['Room Stats - Booked vs Pickedup']
    for i, row in enumerate(ws.iter_rows()):
        if i == 0:
            continue
        vals = [c.value for c in row]
        if vals[13]:
            hotels.add(str(vals[13]).strip())
    wb.close()

    count = 0
    for h in sorted(hotels):
        cur.execute(
            "INSERT INTO ref_hotels (hotel_name) VALUES (%s) ON CONFLICT (hotel_name) DO NOTHING",
            (h,),
        )
        count += 1
    log.info(f"  Seeded {count} hotels")


def seed_centers_from_data(cur):
    """Seed ref_centers by scanning xlsx data for distinct center names."""
    log.info("Seeding ref_centers from xlsx data...")
    # center_name -> (state, region_name)
    centers = {}

    # 2025 has center + state + region
    wb = open_workbook("gp2025_registrations.xlsx")
    ws = wb['Data']
    for i, row in enumerate(ws.iter_rows()):
        if i == 0:
            continue
        vals = [c.value for c in row]
        cname = safe_str(vals[5])
        state = safe_str(vals[12])
        region = safe_str(vals[15])
        if cname and cname not in centers:
            centers[cname] = (state, region)
    wb.close()

    # 2022
    wb = open_workbook("gp2022_registrations_and_room_pickups.xlsx")
    ws = wb['Registration-CheckIn-RoomAcc by']
    for i, row in enumerate(ws.iter_rows()):
        if i == 0:
            continue
        vals = [c.value for c in row]
        cname = safe_str(vals[33])  # CenterName
        state = safe_str(vals[16])  # State
        if cname and cname not in centers:
            centers[cname] = (state, None)
    wb.close()

    # 2023
    wb = open_workbook("gp2023_event_registrations_and_room_pickups.xlsx")
    ws = wb['Registration-CheckIn-RoomAcc by']
    for i, row in enumerate(ws.iter_rows()):
        if i == 0:
            continue
        vals = [c.value for c in row]
        cname = safe_str(vals[33])
        state = safe_str(vals[16])
        if cname and cname not in centers:
            centers[cname] = (state, None)
    wb.close()

    count = 0
    for cname, (state, region_name) in sorted(centers.items()):
        region_id = None
        if region_name:
            rcode = REGION_NAME_TO_CODE.get(region_name)
            if rcode:
                cur.execute("SELECT region_id FROM ref_regions WHERE region_code = %s", (rcode,))
                r = cur.fetchone()
                if r:
                    region_id = r[0]
        cur.execute(
            "INSERT INTO ref_centers (center_name, region_id, state) "
            "VALUES (%s, %s, %s) ON CONFLICT (center_name) DO NOTHING",
            (cname, region_id, state),
        )
        count += 1
    log.info(f"  Seeded {count} centers")


def seed_events(cur):
    """Create event rows for all 4 years."""
    log.info("Seeding events...")
    events_data = [
        (2022, "Guru Purnima 2022", "2022-07-07", "2022-07-13", True, True, True, False),
        (2023, "Guru Purnima 2023", "2023-07-01", "2023-07-04", True, True, False, False),
        (2024, "Guru Purnima 2024", "2024-07-16", "2024-07-21", False, False, True, True),
        (2025, "Guru Purnima 2025", "2025-07-05", "2025-07-12", True, True, True, True),
    ]
    for year, name, start, end, has_reg, has_room, has_food, has_dash in events_data:
        cur.execute(
            """INSERT INTO events (event_year, event_name, start_date, end_date,
               has_registration_data, has_room_data, has_food_data, has_dashboard_data)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
               ON CONFLICT (event_year) DO NOTHING""",
            (year, name, start, end, has_reg, has_room, has_food, has_dash),
        )
    log.info("  Seeded 4 events")


def seed_data_availability(cur):
    """Populate data_availability to document what's present per year."""
    log.info("Seeding data_availability...")
    rows = [
        # 2022
        (2022, "registration", "individual", ["gp2022_registrations_and_room_pickups.xlsx"], 2657, None),
        (2022, "room", "individual", ["gp2022_registrations_and_room_pickups.xlsx"], 828, "Room stats sheet"),
        (2022, "food", "aggregated", ["gp2022_food_preferences.xlsx"], 6015, "Pivot data, no person link"),
        # 2023
        (2023, "registration", "individual", ["gp2023_event_registrations_and_room_pickups.xlsx"], 3574, None),
        (2023, "room", "individual", ["gp2023_event_registrations_and_room_pickups.xlsx"], 886, "Room stats sheet"),
        (2023, "food", "none", [], 0, "No food data collected for 2023"),
        # 2024
        (2024, "registration", "summary", ["gp2024_event_dashboard.xlsx"], None, "Dashboard aggregates only"),
        (2024, "room", "summary", ["gp2024_event_dashboard.xlsx"], None, "Dashboard aggregates only"),
        (2024, "food", "aggregated", ["gp2024_scanning_analysis.xlsx"], 216, "Daily meal totals"),
        (2024, "dashboard", "available", ["gp2024_event_dashboard.xlsx"], None, None),
        # 2025
        (2025, "registration", "individual", ["gp2025_registrations.xlsx"], 7229, "Includes youth + LMHT"),
        (2025, "room", "individual", ["gp2025_registrations.xlsx", "gp2025_room_analysis.xlsx"], 1344, "Two overlapping sources"),
        (2025, "food", "individual", ["gp2025_food_preferences.xlsx"], 46755, "Per-scan records with person link"),
        (2025, "dashboard", "available", ["gp2025_event_dashboard.xlsx"], None, None),
    ]
    for year, entity, level, files, count, notes in rows:
        cur.execute(
            """INSERT INTO data_availability (event_year, entity_type, data_level, source_files, row_count, notes)
               VALUES (%s, %s, %s, %s, %s, %s)
               ON CONFLICT (event_year, entity_type) DO NOTHING""",
            (year, entity, level, files, count, notes),
        )
    log.info(f"  Seeded {len(rows)} data_availability rows")


def run_seed():
    """Run all seed functions."""
    log.info("Starting reference data seeding...")
    with get_cursor() as cur:
        seed_regions(cur)
        seed_food_preferences(cur)
        seed_age_groups(cur)
        seed_events(cur)
        seed_data_availability(cur)
        # These scan xlsx files:
        seed_room_types_from_data(cur)
        seed_hotels_from_data(cur)
        seed_centers_from_data(cur)
    log.info("Reference data seeding complete.")
