"""ETL loader for 2025 data — the richest year.

Sources:
- gp2025_registrations.xlsx (Data, BMHT+LMHT, YMHT, Bhakti, Rooms, Special Needs,
  Translation, Exceptions, AC-no-GP, GP-no-12)
- gp2025_food_preferences.xlsx (All Data — individual scans)
- gp2025_room_analysis.xlsx (Data — room details)
- gp2025_event_dashboard.xlsx (Report, Date wise Attendees)
"""

import logging
import json
from .db import get_cursor, get_or_create_event
from .xlsx_utils import (
    open_workbook, safe_str, safe_int, safe_float, safe_bool, safe_date,
    normalize_gender, normalize_food_pref, sheet_to_dicts,
)
from .seed import REGION_NAME_TO_CODE

log = logging.getLogger(__name__)


def _resolve_center_id(cur, center_name):
    if not center_name:
        return None
    cur.execute("SELECT center_id FROM ref_centers WHERE center_name = %s", (center_name,))
    row = cur.fetchone()
    return row[0] if row else None


def _resolve_region_id(cur, region_name):
    if not region_name:
        return None
    code = REGION_NAME_TO_CODE.get(region_name)
    if not code:
        return None
    cur.execute("SELECT region_id FROM ref_regions WHERE region_code = %s", (code,))
    row = cur.fetchone()
    return row[0] if row else None


def _resolve_food_pref_id(cur, raw_pref):
    if not raw_pref:
        return None
    code = normalize_food_pref(raw_pref)
    cur.execute("SELECT food_pref_id FROM ref_food_preferences WHERE code = %s", (code,))
    row = cur.fetchone()
    return row[0] if row else None


def _resolve_age_group_id(cur, age_group_str):
    if not age_group_str:
        return None
    s = str(age_group_str).strip()
    # Handle the date-formatted values (e.g. "2025-04-12 00:00:00") — these are LMHT kids
    if "2025" in s or "2024" in s:
        return None
    cur.execute("SELECT age_group_id FROM ref_age_groups WHERE group_code = %s", (s,))
    row = cur.fetchone()
    if row:
        return row[0]
    # Try mapping common strings
    mapping = {"<4": "LT4", "70+": "70PLUS"}
    mapped = mapping.get(s, s)
    cur.execute("SELECT age_group_id FROM ref_age_groups WHERE group_code = %s", (mapped,))
    row = cur.fetchone()
    return row[0] if row else None


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


def _upsert_person_2025(cur, d):
    """Insert or find a 2025 person by MahatmaID or FamilyID+name."""
    mahatma_id = safe_str(d.get("MahatmaID"))
    first_name = safe_str(d.get("FirstName"))
    last_name = safe_str(d.get("LastName"))
    family_id = safe_str(d.get("FamilyID"))

    if not first_name or not last_name:
        return None

    # Try MahatmaID first
    if mahatma_id:
        cur.execute("SELECT person_id FROM persons WHERE mahatma_id = %s", (mahatma_id,))
        row = cur.fetchone()
        if row:
            return row[0]

    # Try FamilyID + name
    if family_id:
        cur.execute(
            "SELECT person_id FROM persons WHERE family_id = %s AND LOWER(first_name) = LOWER(%s) AND LOWER(last_name) = LOWER(%s)",
            (family_id, first_name, last_name),
        )
        row = cur.fetchone()
        if row:
            # Backfill mahatma_id if missing
            if mahatma_id:
                cur.execute(
                    "UPDATE persons SET mahatma_id = %s WHERE person_id = %s AND mahatma_id IS NULL",
                    (mahatma_id, row[0]),
                )
            return row[0]

    # Create new
    center_id = _resolve_center_id(cur, safe_str(d.get("CenterName")))
    region_id = _resolve_region_id(cur, safe_str(d.get("Region")))

    cur.execute(
        """INSERT INTO persons (first_name, last_name, mahatma_id, family_id, member_id,
           gender, city, state, postal_code, country, address1, address2,
           center_id, region_id, gnan_taken)
           VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
           RETURNING person_id""",
        (
            first_name, last_name, mahatma_id, family_id,
            safe_str(d.get("MemberID")),
            normalize_gender(d.get("GenderMF")),
            safe_str(d.get("City")),
            safe_str(d.get("StateOrProvince")),
            safe_str(d.get("PostalCode")),
            safe_str(d.get("Country")) or "USA",
            safe_str(d.get("Address1")),
            safe_str(d.get("Address2")),
            center_id, region_id,
            safe_bool(d.get("HasGnanTaken")),
        ),
    )
    return cur.fetchone()[0]


def load_registrations_2025():
    """Load 2025 main registration data from 'Data' sheet."""
    filename = "gp2025_registrations.xlsx"
    log.info(f"Loading 2025 registrations from {filename} 'Data' sheet...")

    wb = open_workbook(filename)
    ws = wb['Data']
    rows = sheet_to_dicts(ws)
    wb.close()

    with get_cursor() as cur:
        event_id = get_or_create_event(2025)
        person_count = 0
        reg_count = 0

        for d in rows:
            person_id = _upsert_person_2025(cur, d)
            if not person_id:
                continue
            person_count += 1

            # Person contacts
            phone = safe_str(d.get("Phone"))
            whatsapp = safe_str(d.get("WhatsApp Number"))
            emergency_name = safe_str(d.get("Emergency Contact Name")) or safe_str(d.get("EmergencyContactName"))
            emergency_phone = safe_str(d.get("Emergency Contact Phone")) or safe_str(d.get("EmergencyContactPhone"))
            if phone or whatsapp or emergency_name:
                cur.execute("SELECT contact_id FROM person_contacts WHERE person_id = %s", (person_id,))
                if not cur.fetchone():
                    cur.execute(
                        """INSERT INTO person_contacts (person_id, phone1, whatsapp_number,
                           emergency_contact_name, emergency_contact_phone,
                           youth_cell_phone, youth_email)
                           VALUES (%s,%s,%s,%s,%s,%s,%s)""",
                        (
                            person_id, safe_str(phone, max_len=30),
                            safe_str(whatsapp, max_len=40),
                            safe_str(emergency_name, max_len=200),
                            safe_str(emergency_phone, max_len=30),
                            safe_str(d.get("Youth Cell Phone"), max_len=30),
                            safe_str(d.get("Youth Email Address"), max_len=200),
                        ),
                    )

            # Registration
            food_pref_id = _resolve_food_pref_id(cur, safe_str(d.get("Food Preference")))
            age_group_id = _resolve_age_group_id(cur, safe_str(d.get("AgeGroup")))

            cur.execute(
                """INSERT INTO registrations (event_id, person_id, event_year,
                   registration_date, registration_status, member_event_id,
                   household_relation, age_at_event, age_group_id, food_pref_id,
                   needs_mobility_aid, special_assistance, mode_of_transport,
                   translation_needed, dietary_restrictions,
                   source_file, source_sheet)
                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                   ON CONFLICT (event_id, person_id) DO NOTHING""",
                (
                    event_id, person_id, 2025,
                    safe_date(d.get("RegistrationDate")),
                    safe_int(d.get("RegistrationStatus")),
                    safe_str(d.get("MemberEventID")),
                    safe_str(d.get("HouseholdRelation")),
                    safe_int(d.get("AgeAtEvent")),
                    age_group_id, food_pref_id,
                    safe_bool(d.get("Need Mobility Aid")),
                    safe_str(d.get("Special Assistance")),
                    safe_str(d.get("Mode of Transport")),
                    safe_str(d.get("Translation")),
                    safe_str(d.get("Dietary Restrictions & Medical Conditions")),
                    filename, "Data",
                ),
            )
            reg_count += 1

            # Bhakti data (inline in main sheet)
            if safe_bool(d.get("Perform in Bhakti")) is not None:
                reg_id = _get_registration_id(cur, event_id, person_id)
                if reg_id:
                    cur.execute(
                        """INSERT INTO registration_bhakti
                           (registration_id, person_id, event_year,
                            perform_in_bhakti, previous_bhakti_audition,
                            other_audition_event, bhakti_activity, source_file)
                           VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
                           ON CONFLICT DO NOTHING""",
                        (
                            reg_id, person_id, 2025,
                            safe_bool(d.get("Perform in Bhakti")),
                            safe_str(d.get("Previous Bhakti Audition")),
                            safe_str(d.get("Other Audition / Performed Event")),
                            safe_str(d.get("Bhakti Activity")),
                            filename,
                        ),
                    )

            # Youth data (YMHT fields in main sheet)
            ymht_activities = safe_str(d.get("YMHT Activities"))
            if ymht_activities:
                reg_id = _get_registration_id(cur, event_id, person_id)
                if reg_id:
                    cur.execute(
                        """INSERT INTO registration_youth
                           (registration_id, ymht_activities, youth_cell_phone,
                            youth_email, photo_consent, tshirt_size, ymht_outing)
                           VALUES (%s,%s,%s,%s,%s,%s,%s)""",
                        (
                            reg_id, ymht_activities,
                            safe_str(d.get("Youth Cell Phone"), max_len=30),
                            safe_str(d.get("Youth Email Address"), max_len=200),
                            safe_bool(d.get("Photo Consent")),
                            safe_str(d.get("T-Shirt Size"), max_len=10),
                            safe_bool(d.get("YMHT Outing")),
                        ),
                    )

            # LMHT data
            lmht_seva = safe_str(d.get("LMHT Seva"))
            lmht_activities = safe_str(d.get("LMHT Activities"))
            if lmht_seva or lmht_activities:
                reg_id = _get_registration_id(cur, event_id, person_id)
                if reg_id:
                    cur.execute(
                        """INSERT INTO registration_lmht
                           (registration_id, seva, activities,
                            drop_off_person1_name, drop_off_person1_phone,
                            drop_off_person2_name, drop_off_person2_phone,
                            dietary_restrictions)
                           VALUES (%s,%s,%s,%s,%s,%s,%s,%s)""",
                        (
                            reg_id, lmht_seva, lmht_activities,
                            safe_str(d.get("Drop Off / Pick Up Person #1 - Name")),
                            safe_str(d.get("Drop Off / Pick Up Person #1 - Phone")),
                            safe_str(d.get("Drop Off / Pick Up Person #2 - Name")),
                            safe_str(d.get("Drop Off / Pick Up Person #2 - Phone")),
                            safe_str(d.get("LMHT Dietary Restrictions & Medical Conditions")),
                        ),
                    )

    log.info(f"  2025 main: {person_count} persons processed, {reg_count} registrations")


def _get_registration_id(cur, event_id, person_id):
    cur.execute(
        "SELECT registration_id FROM registrations WHERE event_id = %s AND person_id = %s",
        (event_id, person_id),
    )
    row = cur.fetchone()
    return row[0] if row else None


def load_youth_registrations_2025():
    """Load BMHT+LMHT and YMHT registration sheets."""
    filename = "gp2025_registrations.xlsx"
    log.info(f"Loading 2025 youth registrations from {filename}...")

    wb = open_workbook(filename)

    with get_cursor() as cur:
        event_id = get_or_create_event(2025)

        # BMHT+LMHT Registrations
        ws = wb['BMHT+LMHT Registrations']
        lmht_rows = sheet_to_dicts(ws)
        lmht_count = 0
        for d in lmht_rows:
            person_id = _upsert_person_2025(cur, d)
            if not person_id:
                continue

            cur.execute(
                """INSERT INTO registrations (event_id, person_id, event_year,
                   registration_status, age_at_event, source_file, source_sheet)
                   VALUES (%s,%s,%s,%s,%s,%s,%s)
                   ON CONFLICT (event_id, person_id) DO NOTHING""",
                (event_id, person_id, 2025, safe_int(d.get("RegistrationStatus")),
                 safe_int(d.get("AgeAtEvent")), filename, "BMHT+LMHT Registrations"),
            )

            reg_id = _get_registration_id(cur, event_id, person_id)
            if reg_id:
                cur.execute(
                    """INSERT INTO registration_lmht
                       (registration_id, seva, activities,
                        drop_off_person1_name, drop_off_person1_phone)
                       VALUES (%s,%s,%s,%s,%s)""",
                    (
                        reg_id,
                        safe_str(d.get("LMHT Seva")),
                        safe_str(d.get("LMHT Activities")),
                        safe_str(d.get("Drop Off / Pick Up Person #1 - Name")),
                        safe_str(d.get("Drop Off / Pick Up Person #1 - Phone")),
                    ),
                )
            lmht_count += 1

        # YMHT Registrations
        ws = wb['YMHT Registrations']
        ymht_rows = sheet_to_dicts(ws)
        ymht_count = 0
        for d in ymht_rows:
            person_id = _upsert_person_2025(cur, d)
            if not person_id:
                continue

            cur.execute(
                """INSERT INTO registrations (event_id, person_id, event_year,
                   registration_status, age_at_event, source_file, source_sheet)
                   VALUES (%s,%s,%s,%s,%s,%s,%s)
                   ON CONFLICT (event_id, person_id) DO NOTHING""",
                (event_id, person_id, 2025, safe_int(d.get("RegistrationStatus")),
                 safe_int(d.get("AgeAtEvent")), filename, "YMHT Registrations"),
            )

            reg_id = _get_registration_id(cur, event_id, person_id)
            if reg_id:
                cur.execute(
                    """INSERT INTO registration_youth
                       (registration_id, ymht_activities, youth_cell_phone,
                        youth_email, photo_consent, tshirt_size)
                       VALUES (%s,%s,%s,%s,%s,%s)""",
                    (
                        reg_id,
                        safe_str(d.get("YMHT Activities")),
                        safe_str(d.get("Youth Cell Phone")),
                        safe_str(d.get("Youth Email Address")),
                        safe_bool(d.get("Photo Consent")),
                        None,
                    ),
                )
            ymht_count += 1

    wb.close()
    log.info(f"  2025 youth: {lmht_count} LMHT + {ymht_count} YMHT registrations")


def load_bhakti_2025():
    """Load dedicated Bhakti Data Captured sheet."""
    filename = "gp2025_registrations.xlsx"
    log.info(f"Loading 2025 bhakti data from {filename}...")

    wb = open_workbook(filename)
    ws = wb['Bhakti Data Captured']
    rows = sheet_to_dicts(ws)
    wb.close()

    with get_cursor() as cur:
        event_id = get_or_create_event(2025)
        count = 0
        for d in rows:
            person_id = _upsert_person_2025(cur, d)
            if not person_id:
                continue
            reg_id = _get_registration_id(cur, event_id, person_id)
            # Check if we already have bhakti data for this person
            cur.execute(
                "SELECT bhakti_id FROM registration_bhakti WHERE person_id = %s AND event_year = 2025",
                (person_id,),
            )
            if cur.fetchone():
                continue
            cur.execute(
                """INSERT INTO registration_bhakti
                   (registration_id, person_id, event_year,
                    perform_in_bhakti, previous_bhakti_audition,
                    other_audition_event, bhakti_activity, source_file)
                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s)""",
                (
                    reg_id, person_id, 2025,
                    safe_bool(d.get("Perform in Bhakti")),
                    safe_str(d.get("Previous Bhakti Audition")),
                    safe_str(d.get("Other Audition / Performed Event")),
                    safe_str(d.get("Bhakti Activity")),
                    filename,
                ),
            )
            count += 1
    log.info(f"  2025 bhakti: {count} rows")


def load_special_needs_2025():
    """Load Special Needs Requests sheet."""
    filename = "gp2025_registrations.xlsx"
    log.info(f"Loading 2025 special needs from {filename}...")

    wb = open_workbook(filename)
    ws = wb['Special Needs Requests']
    rows = sheet_to_dicts(ws)
    wb.close()

    with get_cursor() as cur:
        event_id = get_or_create_event(2025)
        count = 0
        for d in rows:
            person_id = _upsert_person_2025(cur, d)
            if not person_id:
                continue
            reg_id = _get_registration_id(cur, event_id, person_id)
            cur.execute(
                """INSERT INTO special_needs_requests
                   (registration_id, person_id, event_year,
                    request_type, need_mobility_aid, rental_option,
                    accompanying, request_details, source_file)
                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                (
                    reg_id, person_id, 2025,
                    safe_str(d.get("Special Assistance")),
                    safe_bool(d.get("Need Mobility Aid")),
                    safe_str(d.get("Rental Option")),
                    safe_str(d.get("Who is Accompanying ?")),
                    safe_str(d.get("Food Preference")),
                    filename,
                ),
            )
            count += 1
    log.info(f"  2025 special needs: {count} rows")


def load_translation_2025():
    """Load Translation Requests sheet."""
    filename = "gp2025_registrations.xlsx"
    log.info(f"Loading 2025 translation requests from {filename}...")

    wb = open_workbook(filename)
    ws = wb['Translation Requests']
    rows = sheet_to_dicts(ws)
    wb.close()

    with get_cursor() as cur:
        event_id = get_or_create_event(2025)
        count = 0
        for d in rows:
            person_id = _upsert_person_2025(cur, d)
            if not person_id:
                continue

            # The translation language is derived from the "Translation" column
            # in the main Data sheet. In the Translation Requests sheet, there's
            # no separate language column — these are people who requested translation.
            reg_id = _get_registration_id(cur, event_id, person_id)
            cur.execute(
                """INSERT INTO translation_requests
                   (registration_id, person_id, event_year,
                    mode_of_transport, source_file)
                   VALUES (%s,%s,%s,%s,%s)""",
                (
                    reg_id, person_id, 2025,
                    safe_str(d.get("Mode of Transport")),
                    filename,
                ),
            )
            count += 1
    log.info(f"  2025 translation: {count} rows")


def load_exceptions_2025():
    """Load Exceptions, AC-no-GP, and GP-no-12 sheets."""
    filename = "gp2025_registrations.xlsx"
    log.info(f"Loading 2025 exceptions from {filename}...")

    wb = open_workbook(filename)
    count = 0

    with get_cursor() as cur:
        for sheet_name in ["Exceptions", "AC-no-GP", "GP-no-12"]:
            ws = wb[sheet_name]
            rows = sheet_to_dicts(ws)
            for d in rows:
                mahatma_id = safe_str(d.get("MahatmaID"))
                name_fl = safe_str(d.get("NameFL"))
                if not name_fl and not mahatma_id:
                    continue

                # Try to find person_id
                person_id = None
                if mahatma_id:
                    cur.execute("SELECT person_id FROM persons WHERE mahatma_id = %s", (mahatma_id,))
                    row = cur.fetchone()
                    if row:
                        person_id = row[0]

                cur.execute(
                    """INSERT INTO registration_exceptions
                       (person_id, event_year, reason_code, gp_checkout_date,
                        mahatma_id, name_fl, email, phone, center_name,
                        state, country, global_region,
                        source_sheet, source_file)
                       VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                    (
                        person_id, 2025,
                        safe_str(d.get("ReasonCode")),
                        safe_date(d.get("GPCheckOutDate")),
                        mahatma_id, name_fl,
                        safe_str(d.get("EmailAddress")),
                        safe_str(d.get("Phone")),
                        safe_str(d.get("CenterName")),
                        safe_str(d.get("StateOrProvince")),
                        safe_str(d.get("Country")),
                        safe_str(d.get("GlobalRegion")),
                        sheet_name, filename,
                    ),
                )
                count += 1

    wb.close()
    log.info(f"  2025 exceptions: {count} rows across 3 sheets")


def load_rooms_2025():
    """Load 2025 room data from registrations 'Rooms' sheet and room_analysis 'Data' sheet.

    The room_analysis file has more detail (MinAge, MaxAge, Country, CenterName, etc.)
    so we use it as the primary source and supplement from the registrations Rooms sheet.
    """
    log.info("Loading 2025 room data...")

    with get_cursor() as cur:
        event_id = get_or_create_event(2025)
        room_count = 0

        # Primary: gp2025_room_analysis.xlsx 'Data' sheet
        wb = open_workbook("gp2025_room_analysis.xlsx")
        ws = wb['Data']
        rows = sheet_to_dicts(ws)
        wb.close()

        room_ids_loaded = set()
        for d in rows:
            fer_id = safe_str(d.get("FamilyEventRoomID"))
            family_id = safe_str(d.get("FamilyID"))

            # Try to find primary room holder
            holder_name = safe_str(d.get("PrimaryRoomHolderName"))
            holder_id_raw = safe_str(d.get("PrimaryRoomHolderID"))
            primary_holder_person_id = None
            if holder_id_raw:
                cur.execute("SELECT person_id FROM persons WHERE mahatma_id = %s", (holder_id_raw,))
                row = cur.fetchone()
                if row:
                    primary_holder_person_id = row[0]

            room_type_req_id = _resolve_room_type_id(cur, safe_str(d.get("RoomTypeRequested")))
            room_type_asgn_id = _resolve_room_type_id(cur, safe_str(d.get("RoomTypeAssigned")))
            hotel_id = _resolve_hotel_id(cur, safe_str(d.get("HotelAssigned")))

            cur.execute(
                """INSERT INTO rooms (event_id, event_year, family_id, family_event_room_id,
                   primary_room_holder_id, room_type_requested_id, room_type_assigned_id,
                   num_rooms, room_occupancy, check_in_date, check_out_date,
                   room_requested_date, hotel_id, room_group_assigned,
                   room_status, is_room_booked,
                   is_accessible, is_rolling_shower, is_senior_not_sharing_beds,
                   special_needs_text, additional_comments,
                   invoiced_amount, paid_amount, payment_status, paid_by,
                   processing_fees, payment_net_amount,
                   min_age, max_age, occupants_info,
                   source_file, source_sheet)
                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                   RETURNING room_id""",
                (
                    event_id, 2025, family_id, fer_id,
                    primary_holder_person_id, room_type_req_id, room_type_asgn_id,
                    safe_int(d.get("NoOfRooms")),
                    safe_int(d.get("Occupants")),
                    safe_date(d.get("CheckInDate")), safe_date(d.get("CheckOutDate")),
                    safe_date(d.get("RoomRequestedDate")),
                    hotel_id, safe_str(d.get("RoomGroupAssigned")),
                    safe_str(d.get("RoomStatus")),
                    safe_bool(d.get("IsRoomBooked")),
                    safe_bool(d.get("IsAccessible")),
                    safe_bool(d.get("IsRollingShower")),
                    safe_bool(d.get("IsSeniorNotSharingBeds")),
                    safe_str(d.get("SpecialNeedsText")),
                    safe_str(d.get("AdditionalComments")),
                    safe_float(d.get("InvoicedAmount")),
                    safe_float(d.get("PaidAmount")),
                    safe_str(d.get("PaymentStatus")),
                    safe_str(d.get("PaidBy")),
                    safe_float(d.get("ProcessingFees")),
                    safe_float(d.get("PaymentNetAmount")),
                    safe_int(d.get("MinAge")), safe_int(d.get("MaxAge")),
                    safe_str(d.get("OccupantsInfo")),
                    "gp2025_room_analysis.xlsx", "Data",
                ),
            )
            room_id = cur.fetchone()[0]
            if fer_id:
                room_ids_loaded.add(fer_id)

            # Room occupants from O1Age-O4Age
            for pos in range(1, 5):
                occ_age = safe_int(d.get(f"O{pos}Age"))
                if occ_age is not None:
                    cur.execute(
                        """INSERT INTO room_occupants (room_id, occupant_age, occupant_position)
                           VALUES (%s,%s,%s)""",
                        (room_id, occ_age, pos),
                    )

            room_count += 1

        # Supplement: gp2025_registrations.xlsx 'Rooms' sheet
        # Only load rooms not already loaded from room_analysis
        wb = open_workbook("gp2025_registrations.xlsx")
        ws = wb['Rooms']
        reg_rooms = sheet_to_dicts(ws)
        wb.close()

        supplement_count = 0
        for d in reg_rooms:
            fer_id = safe_str(d.get("FamilyEventRoomID"))
            if fer_id and fer_id in room_ids_loaded:
                # Update with additional fields from registrations (FinalCheckIn/Out, HotelConfirmation)
                final_checkin = safe_date(d.get("FinalCheckInDate"))
                final_checkout = safe_date(d.get("FinalCheckOutDate"))
                hotel_conf = safe_str(d.get("FinalHotelConfirmationNumber"))
                if final_checkin or final_checkout or hotel_conf:
                    cur.execute(
                        """UPDATE rooms SET
                           final_check_in_date = COALESCE(final_check_in_date, %s),
                           final_check_out_date = COALESCE(final_check_out_date, %s),
                           hotel_confirmation_number = COALESCE(hotel_confirmation_number, %s)
                           WHERE family_event_room_id = %s AND event_year = 2025""",
                        (final_checkin, final_checkout, hotel_conf, fer_id),
                    )
                    supplement_count += 1
                continue

            # New room not in room_analysis
            family_id = safe_str(d.get("FamilyID"))
            holder_id_raw = safe_str(d.get("PrimaryRoomHolderID"))
            primary_holder_person_id = None
            if holder_id_raw:
                cur.execute("SELECT person_id FROM persons WHERE mahatma_id = %s", (holder_id_raw,))
                row = cur.fetchone()
                if row:
                    primary_holder_person_id = row[0]

            room_type_req_id = _resolve_room_type_id(cur, safe_str(d.get("RoomTypeRequested")))
            room_type_asgn_id = _resolve_room_type_id(cur, safe_str(d.get("RoomTypeAssigned")))
            hotel_id = _resolve_hotel_id(cur, safe_str(d.get("HotelAssigned")))

            cur.execute(
                """INSERT INTO rooms (event_id, event_year, family_id, family_event_room_id,
                   primary_room_holder_id, room_type_requested_id, room_type_assigned_id,
                   num_rooms, room_occupancy, check_in_date, check_out_date,
                   final_check_in_date, final_check_out_date,
                   hotel_confirmation_number,
                   room_requested_date, hotel_id, room_group_assigned,
                   room_status, is_room_booked,
                   is_accessible, is_rolling_shower, is_senior_not_sharing_beds,
                   special_needs_text, additional_comments,
                   invoiced_amount, paid_amount, payment_status, paid_by,
                   processing_fees, payment_net_amount, occupants_info,
                   source_file, source_sheet)
                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                   RETURNING room_id""",
                (
                    event_id, 2025, family_id, fer_id,
                    primary_holder_person_id, room_type_req_id, room_type_asgn_id,
                    safe_int(d.get("NoOfRooms")),
                    safe_int(d.get("Occupants")),
                    safe_date(d.get("CheckInDate")), safe_date(d.get("CheckOutDate")),
                    safe_date(d.get("FinalCheckInDate")), safe_date(d.get("FinalCheckOutDate")),
                    safe_str(d.get("FinalHotelConfirmationNumber")),
                    safe_date(d.get("RoomRequestedDate")),
                    hotel_id, safe_str(d.get("RoomGroupAssigned")),
                    safe_str(d.get("RoomStatus")),
                    safe_bool(d.get("IsRoomBooked")),
                    safe_bool(d.get("IsAccessible")),
                    safe_bool(d.get("IsRollingShower")),
                    safe_bool(d.get("IsSeniorNotSharingBeds")),
                    safe_str(d.get("SpecialNeedsText")),
                    safe_str(d.get("AdditionalComments")),
                    safe_float(d.get("InvoicedAmount")),
                    safe_float(d.get("PaidAmount")),
                    safe_str(d.get("PaymentStatus")),
                    safe_str(d.get("PaidBy")),
                    safe_float(d.get("ProcessingFees")),
                    safe_float(d.get("PaymentNetAmount")),
                    safe_str(d.get("OccupantsInfo")),
                    "gp2025_registrations.xlsx", "Rooms",
                ),
            )
            new_room_id = cur.fetchone()[0]

            # Occupants
            for pos in range(1, 5):
                occ_age = safe_int(d.get(f"O{pos}Age"))
                if occ_age is not None:
                    cur.execute(
                        "INSERT INTO room_occupants (room_id, occupant_age, occupant_position) VALUES (%s,%s,%s)",
                        (new_room_id, occ_age, pos),
                    )
            room_count += 1

    log.info(f"  2025 rooms: {room_count} total ({supplement_count} enriched from reg sheet)")


def load_food_2025():
    """Load 2025 individual meal scans from gp2025_food_preferences.xlsx 'All Data' sheet."""
    filename = "gp2025_food_preferences.xlsx"
    log.info(f"Loading 2025 food scans from {filename} 'All Data'...")

    wb = open_workbook(filename)
    ws = wb['All Data']

    with get_cursor() as cur:
        event_id = get_or_create_event(2025)
        count = 0
        batch = []

        # Headers: MahatmaID, NameFL, Phone, CenterName, StateOrProvince, Country,
        #          SessionTitle, ScannedTime, Tag, MMSMemberID, ScannedOnDate,
        #          TimeSlot15Min, DispOrder
        for i, row in enumerate(ws.iter_rows()):
            if i == 0:
                continue
            v = [c.value for c in row]

            session_title = safe_str(v[6])
            if not session_title:
                continue

            # Look up person_id by MahatmaID
            mahatma_id = safe_str(v[0])
            person_id = None
            if mahatma_id:
                cur.execute("SELECT person_id FROM persons WHERE mahatma_id = %s", (mahatma_id,))
                row_p = cur.fetchone()
                if row_p:
                    person_id = row_p[0]

            cur.execute(
                """INSERT INTO meal_scans (event_id, event_year, person_id,
                   session_title, session_date, time_slot, scanned_time,
                   tag, display_order, center_name, state_or_province, country,
                   mms_member_id, food_count,
                   source_file, source_sheet)
                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                (
                    event_id, 2025, person_id,
                    session_title,
                    safe_date(v[10]),
                    safe_str(v[11]),
                    v[7] if v[7] else None,  # ScannedTime as timestamp
                    safe_str(v[8]),
                    safe_int(v[12]),
                    safe_str(v[3]),
                    safe_str(v[4]),
                    safe_str(v[5]),
                    safe_str(v[9]),
                    1,
                    filename, "All Data",
                ),
            )
            count += 1

            if count % 10000 == 0:
                log.info(f"    ... {count} meal scans processed")

    wb.close()
    log.info(f"  2025 food: {count} individual meal scans loaded")


def load_food_aggregates_2025():
    """Load 2025 summarized food data into meal_aggregates."""
    filename = "gp2025_food_preferences.xlsx"
    log.info(f"Loading 2025 food aggregates from {filename} 'Summarized - 1'...")

    wb = open_workbook(filename)
    ws = wb['Summarized - 1']

    with get_cursor() as cur:
        event_id = get_or_create_event(2025)
        count = 0

        # Headers: ScannedOn, FoodConsumed, Breakfast, Lunch, Tea Break, Dinner, TOTAL
        for i, row in enumerate(ws.iter_rows()):
            if i == 0:
                continue
            v = [c.value for c in row]
            scanned_on = safe_date(v[0])
            food_type = safe_str(v[1])
            if not scanned_on or not food_type:
                continue

            cur.execute(
                """INSERT INTO meal_aggregates
                   (event_id, event_year, meal_date, food_type,
                    breakfast_count, lunch_count, tea_break_count, dinner_count,
                    total_count, source_file, source_sheet)
                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                (
                    event_id, 2025, scanned_on, food_type,
                    safe_int(v[2]), safe_int(v[3]),
                    safe_int(v[4]), safe_int(v[5]),
                    safe_int(v[6]),
                    filename, "Summarized - 1",
                ),
            )
            count += 1

    wb.close()
    log.info(f"  2025 food aggregates: {count} rows")


def load_dashboard_2025():
    """Load 2025 event dashboard snapshots."""
    filename = "gp2025_event_dashboard.xlsx"
    log.info(f"Loading 2025 dashboard from {filename}...")

    wb = open_workbook(filename)
    count = 0

    with get_cursor() as cur:
        for sheet_name in wb.sheetnames:
            ws = wb[sheet_name]
            all_rows = []
            for row in ws.iter_rows():
                all_rows.append([c.value for c in row])

            # Generic parsing: extract non-empty key-value pairs
            for row in all_rows:
                if not row or all(c is None for c in row):
                    continue
                dim_key = safe_str(row[0])
                if not dim_key:
                    continue
                for k in range(1, len(row)):
                    val = row[k]
                    if val is not None:
                        metric_val = None
                        if isinstance(val, (int, float)):
                            metric_val = float(val)
                        cur.execute(
                            """INSERT INTO dashboard_snapshots
                               (event_year, snapshot_type, dimension_key,
                                metric_name, metric_value, raw_json,
                                source_file, source_sheet)
                               VALUES (%s,%s,%s,%s,%s,%s,%s,%s)""",
                            (
                                2025, sheet_name[:100], dim_key[:200],
                                f"col_{k}", metric_val,
                                json.dumps(str(val)) if not isinstance(val, (int, float)) else None,
                                filename, sheet_name,
                            ),
                        )
                        count += 1

    wb.close()
    log.info(f"  2025 dashboard: {count} snapshot rows")


def load_year_2025():
    """Load all 2025 data."""
    load_registrations_2025()
    load_youth_registrations_2025()
    load_bhakti_2025()
    load_special_needs_2025()
    load_translation_2025()
    load_exceptions_2025()
    load_rooms_2025()
    load_food_2025()
    load_food_aggregates_2025()
    load_dashboard_2025()
