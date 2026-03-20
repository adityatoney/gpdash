#!/usr/bin/env python3
"""Generate realistic mock data to fill database gaps.

All mock rows are tagged with source_file = 'mock_data_generated' for easy cleanup.

Gaps filled:
  P1: 2024 registrations (~3,800 rows)
  P2: 2024 rooms (~2,000 rows)
  P3: 2023 meal_scans (~8,000 rows)
  P4: Age group backfill for 2022-2023 registrations
  P5: Persons NULL region/center backfill
"""

import logging
import random
import uuid
from datetime import date, timedelta

import psycopg2.extras

from .db import get_cursor

log = logging.getLogger("etl.mock")

MOCK_SOURCE = "mock_data_generated"

# ── Synthetic name pools (no PII — generic common names) ──────────────────

FIRST_NAMES = [
    "Aarav", "Aditi", "Akash", "Amita", "Anil", "Anita", "Arjun", "Asha",
    "Bhavesh", "Chandra", "Darshan", "Deepa", "Devang", "Diya", "Gaurav",
    "Geeta", "Hari", "Hema", "Jayesh", "Jyoti", "Kailash", "Kamla", "Karan",
    "Kavita", "Kunal", "Lakshmi", "Mahesh", "Mamta", "Manish", "Meena",
    "Mohan", "Nandini", "Naresh", "Neha", "Nikhil", "Nisha", "Pankaj",
    "Pallavi", "Pradeep", "Priya", "Rahul", "Rajesh", "Rakesh", "Rani",
    "Ravi", "Rekha", "Rohit", "Rupa", "Sachin", "Sangeeta", "Sanjay",
    "Sapna", "Satish", "Seema", "Shailesh", "Shanti", "Shivani", "Sudhir",
    "Sunita", "Suresh", "Swati", "Tarun", "Uma", "Usha", "Varun", "Veena",
    "Vijay", "Vinod", "Yogesh", "Anand", "Bindu", "Chirag", "Dimple",
    "Ekta", "Firoz", "Gauri", "Hemal", "Ishaan", "Janki", "Kishore",
    "Lata", "Mukesh", "Naina", "Omkar", "Padma", "Ramesh", "Suman",
    "Tara", "Urmila", "Vandana", "Yash", "Amit", "Bharat", "Chandni",
    "Dinesh", "Falguni", "Girish", "Hansa", "Indira", "Jagdish", "Komal",
]

LAST_NAMES = [
    "Patel", "Shah", "Desai", "Mehta", "Joshi", "Rao", "Kumar", "Singh",
    "Sharma", "Gupta", "Verma", "Agarwal", "Bhatt", "Chauhan", "Dalal",
    "Gandhi", "Iyer", "Jain", "Kapoor", "Malhotra", "Nair", "Pandey",
    "Reddy", "Sinha", "Trivedi", "Vyas", "Yadav", "Bhatia", "Chopra",
    "Das", "Goel", "Hegde", "Kulkarni", "Menon", "Naik", "Parmar",
    "Rathod", "Saxena", "Thakur", "Upadhyay", "Varma", "Wagh", "Zaveri",
    "Amin", "Barot", "Doshi", "Raval", "Solanki", "Modi", "Chokshi",
    "Dave", "Gajjar", "Kakadia", "Limbani", "Mistry", "Parekh", "Randeria",
    "Soni", "Thakor", "Vasani", "Bhavsar", "Contractor", "Darji",
    "Engineer", "Fadia", "Goswami", "Jobanputra", "Kansara", "Lakhani",
    "Majmudar", "Panchal", "Rawal", "Sanghvi", "Talati", "Vakharia",
    "Bhagat", "Dhruv", "Gathani", "Hariani", "Jethalal", "Kothari",
    "Lalwani", "Mandavia", "Nagda", "Oswal", "Padia", "Rangwala",
    "Savla", "Topiwala", "Udani", "Wadhwa", "Ashar", "Bajaj", "Chadha",
    "Dalwadi", "Garg", "Haria", "Israni", "Jhaveri", "Khatri", "Lulla",
]

# ── Helpers ───────────────────────────────────────────────────────────────

def _weighted_choices(population, weights, k):
    """random.choices wrapper that returns a list of k items."""
    return random.choices(population, weights=weights, k=k)


def _weighted_sample_no_replace(population, weights, k):
    """Weighted sampling WITHOUT replacement. Used where unique person_ids needed."""
    pop = list(population)
    wts = list(weights)
    result = []
    for _ in range(k):
        if not pop:
            break
        chosen = random.choices(range(len(pop)), weights=wts, k=1)[0]
        result.append(pop[chosen])
        pop.pop(chosen)
        wts.pop(chosen)
    return result


def _random_date_in_range(start: date, end: date) -> date:
    delta = (end - start).days
    return start + timedelta(days=random.randint(0, max(delta, 0)))


# ── Distribution loader ──────────────────────────────────────────────────

def load_distributions(cur) -> dict:
    """Query existing data to build realistic weight distributions."""
    dist = {}

    # Region weights (from 2025 registrations)
    cur.execute("""
        SELECT p.region_id, COUNT(*) FROM registrations r
        JOIN persons p ON r.person_id = p.person_id
        WHERE r.event_year = 2025 AND p.region_id IS NOT NULL
        GROUP BY p.region_id
    """)
    rows = cur.fetchall()
    dist["region_ids"] = [r[0] for r in rows]
    dist["region_weights"] = [r[1] for r in rows]

    # Center weights (top centers by usage)
    cur.execute("""
        SELECT center_id, COUNT(*) FROM persons
        WHERE center_id IS NOT NULL
        GROUP BY center_id ORDER BY COUNT(*) DESC
    """)
    rows = cur.fetchall()
    dist["center_ids"] = [r[0] for r in rows]
    dist["center_weights"] = [r[1] for r in rows]

    # Center → region mapping
    cur.execute("SELECT center_id, region_id FROM ref_centers WHERE region_id IS NOT NULL")
    dist["center_region_map"] = {r[0]: r[1] for r in cur.fetchall()}

    # Food pref weights (from 2025)
    cur.execute("""
        SELECT food_pref_id, COUNT(*) FROM registrations
        WHERE event_year = 2025 AND food_pref_id IS NOT NULL
        GROUP BY food_pref_id
    """)
    rows = cur.fetchall()
    dist["food_pref_ids"] = [r[0] for r in rows]
    dist["food_pref_weights"] = [r[1] for r in rows]

    # Age group weights (from 2025)
    cur.execute("""
        SELECT age_group_id, COUNT(*) FROM registrations
        WHERE event_year = 2025 AND age_group_id IS NOT NULL
        GROUP BY age_group_id
    """)
    rows = cur.fetchall()
    dist["age_group_ids"] = [r[0] for r in rows]
    dist["age_group_weights"] = [r[1] for r in rows]

    # Age group mapping (for backfill by age_at_event)
    cur.execute("SELECT age_group_id, min_age, max_age FROM ref_age_groups")
    dist["age_group_ranges"] = [(r[0], r[1], r[2]) for r in cur.fetchall()]

    # Room type weights (from 2022-2023, by individual room_type_id)
    cur.execute("""
        SELECT room_type_assigned_id, COUNT(*) FROM rooms
        WHERE room_type_assigned_id IS NOT NULL AND event_year IN (2022, 2023)
        GROUP BY room_type_assigned_id
    """)
    rows = cur.fetchall()
    dist["room_type_ids"] = [r[0] for r in rows]
    dist["room_type_weights"] = [r[1] for r in rows]

    # Hotel weights
    cur.execute("""
        SELECT hotel_id, COUNT(*) FROM rooms
        WHERE hotel_id IS NOT NULL
        GROUP BY hotel_id
    """)
    rows = cur.fetchall()
    dist["hotel_ids"] = [r[0] for r in rows]
    dist["hotel_weights"] = [r[1] for r in rows]

    # Gender ratio
    cur.execute("SELECT gender, COUNT(*) FROM persons GROUP BY gender")
    rows = cur.fetchall()
    dist["genders"] = [r[0] for r in rows]
    dist["gender_weights"] = [r[1] for r in rows]

    # 2022 meal scan dimensions
    cur.execute("""
        SELECT DISTINCT age_group_code, gender, food_consumed
        FROM meal_scans WHERE event_year = 2022
    """)
    dist["meal_dimensions"] = [(r[0], r[1], r[2]) for r in cur.fetchall()]

    # 2022 meal scan relative weights per dimension combo
    cur.execute("""
        SELECT age_group_code, gender, food_consumed, SUM(food_count) as total
        FROM meal_scans WHERE event_year = 2022
        GROUP BY age_group_code, gender, food_consumed
    """)
    rows = cur.fetchall()
    dist["meal_dim_keys"] = [(r[0], r[1], r[2]) for r in rows]
    dist["meal_dim_weights"] = [r[3] for r in rows]

    # Existing person_ids from 2022/2023 registrations (for returning attendees)
    cur.execute("""
        SELECT DISTINCT person_id FROM registrations
        WHERE event_year IN (2022, 2023)
    """)
    dist["existing_person_ids"] = [r[0] for r in cur.fetchall()]

    # Event info
    cur.execute("SELECT event_id, event_year, start_date, end_date FROM events ORDER BY event_year")
    dist["events"] = {r[1]: {"event_id": r[0], "start": r[2], "end": r[3]} for r in cur.fetchall()}

    log.info(f"Loaded distributions: {len(dist['existing_person_ids'])} existing persons, "
             f"{len(dist['region_ids'])} regions, {len(dist['room_type_ids'])} room types")
    return dist


# ── P1: Generate 2024 registrations ──────────────────────────────────────

def generate_2024_registrations(cur, dist):
    """Generate ~3,800 registrations for 2024."""
    TARGET = 3800
    RETURNING_RATIO = 0.65
    n_returning = int(TARGET * RETURNING_RATIO)
    n_new = TARGET - n_returning

    ev = dist["events"][2024]
    event_id = ev["event_id"]
    event_start = ev["start"]
    event_end = ev["end"]

    log.info(f"Generating {TARGET} registrations for 2024 (event_id={event_id})...")

    # --- Returning attendees: sample from existing persons ---
    existing = dist["existing_person_ids"]
    if len(existing) < n_returning:
        n_returning = len(existing)
        n_new = TARGET - n_returning
    returning_ids = random.sample(existing, n_returning)

    # --- New synthetic persons ---
    new_person_ids = []
    person_rows = []
    for _ in range(n_new):
        first = random.choice(FIRST_NAMES)
        last = random.choice(LAST_NAMES)
        gender = _weighted_choices(dist["genders"], dist["gender_weights"], 1)[0]
        center_id = _weighted_choices(dist["center_ids"], dist["center_weights"], 1)[0]
        region_id = dist["center_region_map"].get(center_id)
        if region_id is None:
            region_id = _weighted_choices(dist["region_ids"], dist["region_weights"], 1)[0]
        mahatma_id = f"MOCK_{uuid.uuid4().hex[:8].upper()}"

        person_rows.append((
            mahatma_id, first, last, gender, center_id, region_id
        ))

    # Bulk insert persons and collect their IDs
    if person_rows:
        cols = "mahatma_id, first_name, last_name, gender, center_id, region_id"
        template = "(%s, %s, %s, %s, %s, %s)"
        sql = f"INSERT INTO persons ({cols}) VALUES %s RETURNING person_id"
        result = psycopg2.extras.execute_values(cur, sql, person_rows, template=template, fetch=True)
        new_person_ids = [r[0] for r in result]
        log.info(f"  Created {len(new_person_ids)} new synthetic persons")

    all_person_ids = returning_ids + new_person_ids

    # --- Build registration rows ---
    reg_rows = []
    event_duration = (event_end - event_start).days
    reg_window_start = event_start - timedelta(days=75)

    for pid in all_person_ids:
        is_returning = pid in set(returning_ids)
        food_pref = _weighted_choices(dist["food_pref_ids"], dist["food_pref_weights"], 1)[0]
        age_group = _weighted_choices(dist["age_group_ids"], dist["age_group_weights"], 1)[0]

        # Registration date: bell curve peaking ~3 weeks before event
        reg_offset = int(random.gauss(50, 15))
        reg_offset = max(1, min(reg_offset, 75))
        reg_date = event_start - timedelta(days=reg_offset)

        # Arrival: weighted toward day 1
        arrival_weights = [50, 25, 15, 5, 3, 2]
        arrival_day = _weighted_choices(range(event_duration + 1), arrival_weights[:event_duration + 1], 1)[0]
        arrival = event_start + timedelta(days=arrival_day)

        # Departure: 2-6 days after arrival, capped at event end
        stay = random.choices([2, 3, 4, 5, 6], weights=[5, 10, 15, 40, 30], k=1)[0]
        departure = min(arrival + timedelta(days=stay), event_end)
        los = (departure - arrival).days

        checked_in = random.random() < 0.90

        reg_rows.append((
            event_id, pid, 2024, reg_date, 1,  # registration_status=1
            age_group, food_pref,
            arrival, departure, los,
            checked_in, is_returning,
            MOCK_SOURCE, "generated",
        ))

    cols = ("event_id, person_id, event_year, registration_date, registration_status, "
            "age_group_id, food_pref_id, arrival_date, departure_date, length_of_stay, "
            "is_checked_in, is_returning, source_file, source_sheet")
    template = "(" + ", ".join(["%s"] * 14) + ")"
    sql = f"INSERT INTO registrations ({cols}) VALUES %s ON CONFLICT (event_id, person_id) DO NOTHING"
    psycopg2.extras.execute_values(cur, sql, reg_rows, template=template)
    log.info(f"  Inserted {len(reg_rows)} registrations for 2024")

    return all_person_ids


# ── P2: Generate 2024 rooms ──────────────────────────────────────────────

def generate_2024_rooms(cur, dist):
    """Generate ~2,000 rooms for 2024."""
    TARGET = 2000

    ev = dist["events"][2024]
    event_id = ev["event_id"]
    event_start = ev["start"]
    event_end = ev["end"]

    # Get person_ids registered for 2024
    cur.execute("""
        SELECT person_id, arrival_date, departure_date
        FROM registrations WHERE event_year = 2024
    """)
    reg_rows = cur.fetchall()
    if len(reg_rows) < TARGET:
        TARGET = len(reg_rows)

    sampled = random.sample(reg_rows, TARGET)

    log.info(f"Generating {TARGET} rooms for 2024...")

    room_rows = []
    for (pid, arrival, departure) in sampled:
        room_type = _weighted_choices(dist["room_type_ids"], dist["room_type_weights"], 1)[0]
        # 80% get what they requested
        req_type = room_type if random.random() < 0.80 else _weighted_choices(
            dist["room_type_ids"], dist["room_type_weights"], 1)[0]
        hotel = _weighted_choices(dist["hotel_ids"], dist["hotel_weights"], 1)[0]
        occupancy = random.choices([1, 2, 3, 4], weights=[15, 40, 30, 15], k=1)[0]

        check_in = arrival if arrival else event_start
        check_out = departure if departure else event_end
        nights = (check_out - check_in).days
        if nights <= 0:
            nights = 1
            check_out = check_in + timedelta(days=1)

        room_rows.append((
            event_id, 2024, pid,
            req_type, room_type,
            1,  # num_rooms
            occupancy,
            check_in, check_out, nights,
            hotel,
            True,  # room_requested
            random.random() < 0.85,  # room_picked_up
            True,  # is_room_booked
            MOCK_SOURCE, "generated",
        ))

    cols = ("event_id, event_year, primary_room_holder_id, "
            "room_type_requested_id, room_type_assigned_id, "
            "num_rooms, room_occupancy, check_in_date, check_out_date, night_count, "
            "hotel_id, room_requested, room_picked_up, is_room_booked, "
            "source_file, source_sheet")
    template = "(" + ", ".join(["%s"] * 16) + ")"
    sql = f"INSERT INTO rooms ({cols}) VALUES %s"
    psycopg2.extras.execute_values(cur, sql, room_rows, template=template)
    log.info(f"  Inserted {len(room_rows)} rooms for 2024")


# ── P3: Generate 2023 meal scans ─────────────────────────────────────────

def generate_2023_meal_scans(cur, dist):
    """Generate ~8,000 aggregated meal scans for 2023 (matching 2022 pivot pattern)."""
    ev = dist["events"][2023]
    event_id = ev["event_id"]
    event_start = ev["start"]
    event_end = ev["end"]

    sessions = ["Breakfast", "Lunch", "Tea Break", "Dinner"]
    session_times = {
        "Breakfast": "07:30:00",
        "Lunch": "12:00:00",
        "Tea Break": "16:00:00",
        "Dinner": "19:30:00",
    }

    # Scale from 2022: 2023 had 3572/2657 = 1.344x more registrations
    # 2022 average daily food total ~ 5,800 (excluding special sessions)
    # Target per day for 2023: ~7,800
    DAILY_TARGET = 7800

    # Get dimension weights from 2022
    dim_keys = dist["meal_dim_keys"]
    dim_weights = dist["meal_dim_weights"]
    total_dim_weight = sum(dim_weights)

    # Session weight ratios (from 2022 data patterns)
    session_weight = {"Breakfast": 0.22, "Lunch": 0.28, "Tea Break": 0.15, "Dinner": 0.35}

    event_days = []
    d = event_start
    while d <= event_end:
        event_days.append(d)
        d += timedelta(days=1)

    log.info(f"Generating meal scans for 2023 ({len(event_days)} days)...")

    rows = []
    for day in event_days:
        for session in sessions:
            session_total = int(DAILY_TARGET * session_weight[session])

            # Distribute session_total across dimension combos
            for i, (age_code, gender, food_consumed) in enumerate(dim_keys):
                proportion = dim_weights[i] / total_dim_weight
                count = max(1, int(session_total * proportion + random.gauss(0, 0.5)))

                rows.append((
                    event_id, 2023,
                    None,  # person_id (NULL — aggregated pattern)
                    session, "Food", day,
                    session_times[session],
                    None,  # scanned_time
                    None,  # tag
                    None,  # display_order
                    age_code, gender,
                    None,  # food_pref_selected
                    food_consumed,
                    None,  # is_new_mahatma
                    count,  # food_count
                    None, None, None,  # center_name, state, country
                    None,  # mms_member_id
                    MOCK_SOURCE, "generated",
                ))

    cols = ("event_id, event_year, person_id, "
            "session_title, session_type, session_date, "
            "time_slot, scanned_time, tag, display_order, "
            "age_group_code, gender, food_pref_selected, food_consumed, "
            "is_new_mahatma, food_count, "
            "center_name, state_or_province, country, mms_member_id, "
            "source_file, source_sheet")
    template = "(" + ", ".join(["%s"] * 22) + ")"
    sql = f"INSERT INTO meal_scans ({cols}) VALUES %s"
    psycopg2.extras.execute_values(cur, sql, rows, template=template)
    log.info(f"  Inserted {len(rows)} meal scan rows for 2023")


# ── P4: Backfill age groups for 2022-2023 ────────────────────────────────

def backfill_age_groups(cur, dist):
    """Fill NULL age_group_id for 2022-2023 registrations."""
    log.info("Backfilling age_group_id for 2022-2023 registrations...")

    # First: rows that have age_at_event — map to correct age group
    age_ranges = dist["age_group_ranges"]
    # Use the first set (IDs 1-7 which are the numeric ranges, not the code-based 8-14)
    numeric_ranges = [(gid, lo, hi) for gid, lo, hi in age_ranges if gid <= 7]

    updated = 0
    for gid, lo, hi in numeric_ranges:
        cur.execute("""
            UPDATE registrations SET age_group_id = %s
            WHERE event_year IN (2022, 2023)
              AND age_group_id IS NULL
              AND age_at_event IS NOT NULL
              AND age_at_event >= %s AND age_at_event <= %s
        """, (gid, lo, hi))
        updated += cur.rowcount

    log.info(f"  Mapped {updated} rows via age_at_event")

    # Second: remaining NULLs — assign weighted random
    cur.execute("""
        SELECT registration_id FROM registrations
        WHERE event_year IN (2022, 2023) AND age_group_id IS NULL
    """)
    null_ids = [r[0] for r in cur.fetchall()]

    if null_ids:
        age_groups = _weighted_choices(
            dist["age_group_ids"], dist["age_group_weights"], len(null_ids)
        )
        # Batch update
        data = list(zip(age_groups, null_ids))
        psycopg2.extras.execute_batch(cur, """
            UPDATE registrations SET age_group_id = %s WHERE registration_id = %s
        """, data)
        log.info(f"  Randomly assigned {len(null_ids)} remaining rows")


# ── P5: Backfill persons NULLs ───────────────────────────────────────────

def backfill_persons_nulls(cur, dist):
    """Fill NULL region_id and center_id in persons table."""
    log.info("Backfilling persons NULL region_id and center_id...")

    # region_id from center_id lookup
    cur.execute("""
        UPDATE persons p SET region_id = c.region_id
        FROM ref_centers c
        WHERE p.center_id = c.center_id
          AND p.region_id IS NULL
          AND c.region_id IS NOT NULL
    """)
    log.info(f"  Set region_id from center lookup: {cur.rowcount} rows")

    # Remaining NULL center_id — assign weighted random center
    cur.execute("SELECT person_id FROM persons WHERE center_id IS NULL")
    null_center_ids = [r[0] for r in cur.fetchall()]
    if null_center_ids:
        centers = _weighted_choices(
            dist["center_ids"], dist["center_weights"], len(null_center_ids)
        )
        data = list(zip(centers, null_center_ids))
        psycopg2.extras.execute_batch(cur, """
            UPDATE persons SET center_id = %s WHERE person_id = %s
        """, data)
        log.info(f"  Assigned center_id to {len(null_center_ids)} persons")

    # Now fill remaining NULL region_id from their (possibly new) center_id
    cur.execute("""
        UPDATE persons p SET region_id = c.region_id
        FROM ref_centers c
        WHERE p.center_id = c.center_id
          AND p.region_id IS NULL
          AND c.region_id IS NOT NULL
    """)
    log.info(f"  Set region_id from center (2nd pass): {cur.rowcount} rows")

    # Any still NULL region? Assign weighted random
    cur.execute("SELECT person_id FROM persons WHERE region_id IS NULL")
    null_region_ids = [r[0] for r in cur.fetchall()]
    if null_region_ids:
        regions = _weighted_choices(
            dist["region_ids"], dist["region_weights"], len(null_region_ids)
        )
        data = list(zip(regions, null_region_ids))
        psycopg2.extras.execute_batch(cur, """
            UPDATE persons SET region_id = %s WHERE person_id = %s
        """, data)
        log.info(f"  Assigned region_id to {len(null_region_ids)} remaining persons")


# ── Cleanup & metadata ───────────────────────────────────────────────────

def clean_mock_data(cur):
    """Remove all mock-generated data. Order matters for FK constraints."""
    log.info("Cleaning previous mock data...")

    # Delete rooms first (FK to persons)
    cur.execute(f"DELETE FROM rooms WHERE source_file = %s", (MOCK_SOURCE,))
    log.info(f"  Deleted {cur.rowcount} mock rooms")

    # Delete meal scans
    cur.execute(f"DELETE FROM meal_scans WHERE source_file = %s", (MOCK_SOURCE,))
    log.info(f"  Deleted {cur.rowcount} mock meal_scans")

    # Delete registrations (FK to persons)
    cur.execute(f"DELETE FROM registrations WHERE source_file = %s", (MOCK_SOURCE,))
    log.info(f"  Deleted {cur.rowcount} mock registrations")

    # Delete orphaned mock persons (those not referenced by any real data)
    cur.execute("""
        DELETE FROM persons
        WHERE mahatma_id LIKE 'MOCK_%%'
          AND person_id NOT IN (SELECT person_id FROM registrations)
          AND person_id NOT IN (SELECT DISTINCT person_id FROM meal_scans WHERE person_id IS NOT NULL)
          AND person_id NOT IN (SELECT DISTINCT primary_room_holder_id FROM rooms WHERE primary_room_holder_id IS NOT NULL)
    """)
    log.info(f"  Deleted {cur.rowcount} orphaned mock persons")


def update_metadata(cur):
    """Update events totals and data_availability after mock generation."""
    log.info("Updating event totals and metadata...")

    # Update event flags (totals are handled by run.py's update_event_totals)
    cur.execute("""
        UPDATE events SET
            has_registration_data = true,
            has_room_data = true,
            updated_at = NOW()
        WHERE event_year = 2024
    """)

    # Update data_availability for 2024 registration
    cur.execute("""
        INSERT INTO data_availability (event_year, entity_type, data_level, row_count, notes)
        VALUES (2024, 'registration', 'individual', (SELECT COUNT(*) FROM registrations WHERE event_year = 2024), 'Mock data generated')
        ON CONFLICT (event_year, entity_type)
        DO UPDATE SET data_level = 'individual',
                      row_count = EXCLUDED.row_count,
                      notes = 'Mock data generated'
    """)

    # Update data_availability for 2024 room
    cur.execute("""
        INSERT INTO data_availability (event_year, entity_type, data_level, row_count, notes)
        VALUES (2024, 'room', 'individual', (SELECT COUNT(*) FROM rooms WHERE event_year = 2024), 'Mock data generated')
        ON CONFLICT (event_year, entity_type)
        DO UPDATE SET data_level = 'individual',
                      row_count = EXCLUDED.row_count,
                      notes = 'Mock data generated'
    """)

    # Update data_availability for 2023 food
    cur.execute("""
        INSERT INTO data_availability (event_year, entity_type, data_level, row_count, notes)
        VALUES (2023, 'food', 'aggregated', (SELECT COUNT(*) FROM meal_scans WHERE event_year = 2023), 'Mock data generated')
        ON CONFLICT (event_year, entity_type)
        DO UPDATE SET data_level = 'aggregated',
                      row_count = EXCLUDED.row_count,
                      notes = 'Mock data generated'
    """)

    log.info("  Metadata updated.")


# ── Main entry point ─────────────────────────────────────────────────────

def generate_all_mock():
    """Generate all mock data. Idempotent — cleans previous mock data first."""
    log.info("=" * 60)
    log.info("MOCK DATA GENERATION")
    log.info("=" * 60)

    with get_cursor() as cur:
        # Clean previous mock data
        clean_mock_data(cur)

        # Load distributions from existing data
        dist = load_distributions(cur)

        # P1: 2024 registrations
        generate_2024_registrations(cur, dist)

        # P2: 2024 rooms
        generate_2024_rooms(cur, dist)

        # P3: 2023 meal scans
        generate_2023_meal_scans(cur, dist)

        # P4: Backfill age groups
        backfill_age_groups(cur, dist)

        # P5: Backfill persons NULLs
        backfill_persons_nulls(cur, dist)

        # Update metadata
        update_metadata(cur)

    log.info("=" * 60)
    log.info("Mock data generation complete!")
    log.info("=" * 60)
