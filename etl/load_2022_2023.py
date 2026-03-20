"""ETL loader for 2022 and 2023 registration + room + food data.

2022 and 2023 share identical column structures for registrations.
2022 also has food pivot data; 2023 has no food data.
"""

import logging
from .db import get_cursor, get_or_create_event
from .xlsx_utils import (
    open_workbook, safe_str, safe_int, safe_bool, safe_date,
    normalize_gender, normalize_food_pref,
)
from .seed import FOOD_PREF_MAP

log = logging.getLogger(__name__)

# Column indexes for Registration-CheckIn-RoomAcc sheet (same for 2022 & 2023)
# 0:FirstName, 1:MiddleName, 2:LastName, 3:RegistrationDate, 4:ConfirmationNumber,
# 5:Gender, 6:BirthMonth, 7:BirthYear, 8:AgeWhenEventStarts, 9:MedicalCondition,
# 10:WheelChairRequest, 11:Translationlang, 12:HospitalityPref, 13:FoodPref,
# 14:IsSevarthiFamilyMember, 15:City, 16:State, 17:Zipcode, 18:Country,
# 19:Comments, 20:FamilyEmailAddress, 21:Phone1, 22:Phone2,
# 23:ArrivalDate, 24:DepartureDate, 25:Occupancy, 26:CustomField,
# 27:PaymentAmount, 28:IsPaymentReceived, 29:IsCheckedIn,
# 30:GnanTaken, 31:GnanLanguage, 32:GnanDate, 33:CenterName,
# 34:WMHTID, 35:RequestedHotelRoom, 36:BookedHotelRoom,
# 37:EventFamilyMemberID, 38:FamilyMemberID, 39:FamilyID,
# 40:SatsangCenterID, 41:regionID, 42:RegiNumber, 43:CheckedInTime,
# 44:RoomRequested, 45:RoomPickedUp, 46:RoomReuqested, 47:RoomOccupancy,
# 48:RoomTypePickedUp, 49:RoomCheckInDate, 50:RoomCheckOutDate,
# 51:PickedUpRoomType, 52:EventFamilyRoomID, 53:EventFamilyRoomConfirmationID


def _resolve_food_pref_id(cur, raw_pref):
    """Look up food_pref_id from raw value."""
    if not raw_pref:
        return None
    code = normalize_food_pref(raw_pref)
    # Try direct code match
    cur.execute("SELECT food_pref_id FROM ref_food_preferences WHERE code = %s", (code,))
    row = cur.fetchone()
    if row:
        return row[0]
    # Try the long-form mapping
    mapped = FOOD_PREF_MAP.get(raw_pref)
    if mapped:
        cur.execute("SELECT food_pref_id FROM ref_food_preferences WHERE code = %s", (mapped[0],))
        row = cur.fetchone()
        if row:
            return row[0]
    return None


def _resolve_center_id(cur, center_name):
    if not center_name:
        return None
    cur.execute("SELECT center_id FROM ref_centers WHERE center_name = %s", (center_name,))
    row = cur.fetchone()
    return row[0] if row else None


def _resolve_region_id(cur, legacy_id):
    if not legacy_id:
        return None
    lid = safe_int(legacy_id)
    if lid:
        cur.execute("SELECT region_id FROM ref_regions WHERE legacy_id = %s", (lid,))
        row = cur.fetchone()
        if row:
            return row[0]
    return None


def _resolve_room_type_id(cur, type_name):
    if not type_name:
        return None
    code = str(type_name).strip()[:50]
    cur.execute("SELECT room_type_id FROM ref_room_types WHERE type_code = %s", (code,))
    row = cur.fetchone()
    return row[0] if row else None


def _resolve_hotel_id(cur, hotel_name):
    if not hotel_name:
        return None
    cur.execute("SELECT hotel_id FROM ref_hotels WHERE hotel_name = %s", (str(hotel_name).strip(),))
    row = cur.fetchone()
    return row[0] if row else None


def load_registrations(year):
    """Load registration data for 2022 or 2023."""
    if year == 2022:
        filename = "gp2022_registrations_and_room_pickups.xlsx"
    elif year == 2023:
        filename = "gp2023_event_registrations_and_room_pickups.xlsx"
    else:
        raise ValueError(f"This loader only handles 2022/2023, got {year}")

    log.info(f"Loading {year} registrations from {filename}...")
    wb = open_workbook(filename)
    ws = wb['Registration-CheckIn-RoomAcc by']

    with get_cursor() as cur:
        event_id = get_or_create_event(year)

        person_count = 0
        reg_count = 0
        room_count = 0
        skip_count = 0

        for i, row in enumerate(ws.iter_rows()):
            if i == 0:
                continue
            v = [c.value for c in row]

            first_name = safe_str(v[0])
            last_name = safe_str(v[2])
            if not first_name or not last_name:
                skip_count += 1
                continue

            family_id = safe_str(v[39])
            gender = normalize_gender(v[5])
            center_name = safe_str(v[33])
            center_id = _resolve_center_id(cur, center_name)
            region_id = _resolve_region_id(cur, v[41])

            # Upsert person
            cur.execute(
                "SELECT person_id FROM persons WHERE family_id = %s AND LOWER(first_name) = LOWER(%s) AND LOWER(last_name) = LOWER(%s)",
                (family_id, first_name, last_name),
            )
            existing = cur.fetchone()
            if existing:
                person_id = existing[0]
            else:
                cur.execute(
                    """INSERT INTO persons (first_name, last_name, family_id, gender,
                       birth_month, birth_year, city, state, postal_code, country,
                       center_id, region_id, gnan_taken, gnan_language, gnan_date)
                       VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                       RETURNING person_id""",
                    (
                        first_name, last_name, family_id, gender,
                        safe_int(v[6]), safe_int(v[7]),
                        safe_str(v[15], max_len=100), safe_str(v[16], max_len=100),
                        safe_str(v[17], max_len=50),
                        safe_str(v[18], max_len=100) or "USA",
                        center_id, region_id,
                        safe_bool(v[30]), safe_str(v[31], max_len=50), safe_date(v[32]),
                    ),
                )
                person_id = cur.fetchone()[0]
                person_count += 1

            # Person contacts
            phone1 = safe_str(v[21], max_len=30)
            phone2 = safe_str(v[22], max_len=30)
            family_email = safe_str(v[20], max_len=250)
            if phone1 or phone2 or family_email:
                cur.execute(
                    "SELECT contact_id FROM person_contacts WHERE person_id = %s",
                    (person_id,),
                )
                if not cur.fetchone():
                    cur.execute(
                        "INSERT INTO person_contacts (person_id, phone1, phone2, family_email) VALUES (%s,%s,%s,%s)",
                        (person_id, phone1, phone2, family_email),
                    )

            # Registration
            food_pref_id = _resolve_food_pref_id(cur, safe_str(v[13]))
            cur.execute(
                """INSERT INTO registrations (event_id, person_id, event_year,
                   registration_date, confirmation_number, age_at_event,
                   food_pref_id, needs_mobility_aid, arrival_date, departure_date,
                   is_checked_in, checked_in_time, translation_needed,
                   source_file, source_sheet)
                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                   ON CONFLICT (event_id, person_id) DO NOTHING""",
                (
                    event_id, person_id, year,
                    safe_date(v[3]), safe_str(v[4], max_len=50), safe_int(v[8]),
                    food_pref_id, safe_bool(v[10]),
                    safe_date(v[23]), safe_date(v[24]),
                    safe_bool(v[29]), safe_date(v[43]),
                    safe_str(v[11], max_len=100),
                    filename, "Registration-CheckIn-RoomAcc by",
                ),
            )
            reg_count += 1

            # Room data (cols 44-53)
            room_requested = safe_bool(v[44])
            room_type_req = safe_str(v[46])
            room_family_id = safe_str(v[52])
            if room_requested or room_type_req or room_family_id:
                room_type_req_id = _resolve_room_type_id(cur, room_type_req)
                picked_up_type = safe_str(v[51]) or safe_str(v[48])
                room_type_asgn_id = _resolve_room_type_id(cur, picked_up_type)
                cur.execute(
                    """INSERT INTO rooms (event_id, event_year, family_id, family_event_room_id,
                       primary_room_holder_id, room_type_requested_id, room_type_assigned_id,
                       room_occupancy, check_in_date, check_out_date,
                       room_requested, room_picked_up,
                       hotel_confirmation_number,
                       source_file, source_sheet)
                       VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                    (
                        event_id, year, family_id, room_family_id,
                        person_id, room_type_req_id, room_type_asgn_id,
                        safe_int(v[47]),
                        safe_date(v[49]), safe_date(v[50]),
                        room_requested, safe_bool(v[45]),
                        safe_str(v[53]),
                        filename, "Registration-CheckIn-RoomAcc by",
                    ),
                )
                room_count += 1

        # Enrich rooms with hotel info from "Room Stats" sheet
        _enrich_rooms_from_stats(cur, wb, year, event_id, filename)

    wb.close()
    log.info(f"  {year}: {person_count} new persons, {reg_count} registrations, {room_count} rooms, {skip_count} skipped")


def _enrich_rooms_from_stats(cur, wb, year, event_id, filename):
    """Add hotel name and confirmation from the Room Stats sheet."""
    ws = wb['Room Stats - Booked vs Pickedup']
    enriched = 0
    for i, row in enumerate(ws.iter_rows()):
        if i == 0:
            continue
        v = [c.value for c in row]
        hotel_name = safe_str(v[13])
        hotel_conf = safe_str(v[19])
        if not hotel_name:
            continue

        first_name = safe_str(v[0])
        last_name = safe_str(v[2])
        if not first_name or not last_name:
            continue

        hotel_id = _resolve_hotel_id(cur, hotel_name)

        # Match room by person name
        cur.execute(
            """UPDATE rooms SET hotel_id = %s, hotel_confirmation_number = COALESCE(hotel_confirmation_number, %s)
               WHERE event_id = %s AND primary_room_holder_id IN (
                   SELECT person_id FROM persons
                   WHERE LOWER(first_name) = LOWER(%s) AND LOWER(last_name) = LOWER(%s)
               ) AND hotel_id IS NULL""",
            (hotel_id, hotel_conf, event_id, first_name, last_name),
        )
        enriched += cur.rowcount

    log.info(f"  Enriched {enriched} rooms with hotel info from stats sheet")


def load_food_2022():
    """Load 2022 food pivot data (aggregated, no person link)."""
    filename = "gp2022_food_preferences.xlsx"
    log.info(f"Loading 2022 food data from {filename}...")

    wb = open_workbook(filename)
    count = 0

    with get_cursor() as cur:
        event_id = get_or_create_event(2022)

        # Pivot Data - ALL: SessionType, SessionTitle, SessionDate, TimeSlot,
        #                   AgeGroupCode, Gender, FoodPrefSelected, FoodConsumed,
        #                   NewMahatma, FoodCount
        ws = wb['Pivot Data - ALL']
        for i, row in enumerate(ws.iter_rows()):
            if i == 0:
                continue
            v = [c.value for c in row]
            session_type = safe_str(v[0])
            session_title = safe_str(v[1])
            if not session_title:
                continue

            cur.execute(
                """INSERT INTO meal_scans (event_id, event_year, session_type, session_title,
                   session_date, time_slot, age_group_code, gender,
                   food_pref_selected, food_consumed, is_new_mahatma, food_count,
                   source_file, source_sheet)
                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                (
                    event_id, 2022, session_type, session_title,
                    safe_date(v[2]), safe_str(v[3]),
                    safe_str(v[4]), normalize_gender(v[5]),
                    safe_str(v[6]), safe_str(v[7]),
                    safe_bool(v[8]), safe_int(v[9]) or 1,
                    filename, "Pivot Data - ALL",
                ),
            )
            count += 1

        # Also load Guru Pujan pivot data
        ws = wb['Pivot Data - Gurupujan']
        for i, row in enumerate(ws.iter_rows()):
            if i == 0:
                continue
            v = [c.value for c in row]
            session_title = safe_str(v[1])
            if not session_title:
                continue
            cur.execute(
                """INSERT INTO meal_scans (event_id, event_year, session_type, session_title,
                   session_date, time_slot, age_group_code, gender,
                   food_pref_selected, food_consumed, is_new_mahatma, food_count,
                   source_file, source_sheet)
                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                (
                    event_id, 2022, safe_str(v[0]), session_title,
                    safe_date(v[2]), safe_str(v[3]),
                    safe_str(v[4]), normalize_gender(v[5]),
                    safe_str(v[6]), safe_str(v[7]),
                    safe_bool(v[8]), safe_int(v[9]) or 1,
                    filename, "Pivot Data - Gurupujan",
                ),
            )
            count += 1

    wb.close()
    log.info(f"  2022 food: {count} meal scan rows loaded")


def load_year(year):
    """Load all data for a given year (2022 or 2023)."""
    load_registrations(year)
    if year == 2022:
        load_food_2022()
    # 2023 has no food data
