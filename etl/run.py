#!/usr/bin/env python3
"""Main ETL runner — orchestrates schema creation, seeding, and data loading.

Usage:
    python -m etl.run                    # Full ETL (all years)
    python -m etl.run --year 2022        # Single year
    python -m etl.run --seed-only        # Only seed reference tables
    python -m etl.run --schema-only      # Only create schema
    python -m etl.run --verify           # Run verification queries
    python -m etl.run --reset            # Drop and recreate all tables
"""

import argparse
import logging
import os
import sys
import uuid
from datetime import datetime

from .db import get_cursor, execute_sql_file, get_connection
from .seed import run_seed
from .load_2022_2023 import load_year as load_2022_2023
from .load_2024 import load_year_2024
from .load_2025 import load_year_2025

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("etl")

SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "..", "db", "schema.sql")


def create_schema():
    """Execute the schema DDL."""
    log.info("Creating schema from db/schema.sql...")
    execute_sql_file(SCHEMA_PATH)
    log.info("Schema created successfully.")


def reset_schema():
    """Drop all tables and recreate."""
    log.info("Resetting database — dropping all tables...")
    with get_cursor() as cur:
        cur.execute("""
            DO $$ DECLARE
                r RECORD;
            BEGIN
                FOR r IN (SELECT tablename FROM pg_tables WHERE schemaname = 'public') LOOP
                    EXECUTE 'DROP TABLE IF EXISTS public.' || quote_ident(r.tablename) || ' CASCADE';
                END LOOP;
            END $$;
        """)
    log.info("All tables dropped.")
    create_schema()


def load_year(year):
    """Load data for a specific year."""
    if year in (2022, 2023):
        load_2022_2023(year)
    elif year == 2024:
        load_year_2024()
    elif year == 2025:
        load_year_2025()
    else:
        log.error(f"Unknown year: {year}")
        sys.exit(1)


def load_all():
    """Load all years in order."""
    for year in [2022, 2023, 2024, 2025]:
        log.info(f"\n{'='*60}")
        log.info(f"Loading {year} data...")
        log.info(f"{'='*60}")
        load_year(year)


def update_event_totals():
    """Update the events table with actual counts from loaded data."""
    log.info("Updating event totals...")
    with get_cursor() as cur:
        cur.execute("""
            UPDATE events e SET
                total_registrations = (SELECT COUNT(*) FROM registrations r WHERE r.event_id = e.event_id),
                total_room_bookings = (SELECT COUNT(*) FROM rooms r WHERE r.event_id = e.event_id),
                total_meal_scans = (SELECT COUNT(*) FROM meal_scans m WHERE m.event_id = e.event_id),
                updated_at = NOW()
        """)
    log.info("Event totals updated.")


def verify():
    """Run verification queries to check data integrity."""
    log.info("\n" + "=" * 60)
    log.info("VERIFICATION")
    log.info("=" * 60)

    with get_cursor(commit=False) as cur:
        # Table row counts
        tables = [
            "events", "persons", "person_contacts", "registrations",
            "rooms", "room_occupants", "meal_scans",
            "registration_youth", "registration_lmht", "registration_bhakti",
            "special_needs_requests", "translation_requests", "registration_exceptions",
            "dashboard_snapshots", "meal_aggregates", "data_availability",
            "ref_regions", "ref_centers", "ref_food_preferences",
            "ref_room_types", "ref_age_groups", "ref_hotels",
        ]
        log.info("\nTable row counts:")
        for t in tables:
            cur.execute(f"SELECT COUNT(*) FROM {t}")
            count = cur.fetchone()[0]
            log.info(f"  {t:35s} {count:>8,d}")

        # Registrations per year
        log.info("\nRegistrations per year:")
        cur.execute("SELECT event_year, COUNT(*) FROM registrations GROUP BY event_year ORDER BY event_year")
        for row in cur.fetchall():
            log.info(f"  {row[0]}: {row[1]:,d}")

        # Rooms per year
        log.info("\nRooms per year:")
        cur.execute("SELECT event_year, COUNT(*) FROM rooms GROUP BY event_year ORDER BY event_year")
        for row in cur.fetchall():
            log.info(f"  {row[0]}: {row[1]:,d}")

        # Meal scans per year
        log.info("\nMeal scans per year:")
        cur.execute("SELECT event_year, COUNT(*) FROM meal_scans GROUP BY event_year ORDER BY event_year")
        for row in cur.fetchall():
            log.info(f"  {row[0]}: {row[1]:,d}")

        # Returning attendees (persons registered in multiple years)
        log.info("\nReturning attendees (registered in 2+ years):")
        cur.execute("""
            SELECT COUNT(*) FROM (
                SELECT person_id FROM registrations GROUP BY person_id HAVING COUNT(DISTINCT event_year) >= 2
            ) x
        """)
        log.info(f"  {cur.fetchone()[0]:,d} persons attended 2+ years")

        # Data availability
        log.info("\nData availability matrix:")
        cur.execute("SELECT event_year, entity_type, data_level, row_count FROM data_availability ORDER BY event_year, entity_type")
        for row in cur.fetchall():
            log.info(f"  {row[0]} {row[1]:15s} {row[2]:12s} {row[3] or '-':>8}")

    log.info("\nVerification complete.")


def main():
    parser = argparse.ArgumentParser(description="GP Event Data ETL Pipeline")
    parser.add_argument("--year", type=int, choices=[2022, 2023, 2024, 2025], help="Load a specific year only")
    parser.add_argument("--seed-only", action="store_true", help="Only seed reference tables")
    parser.add_argument("--schema-only", action="store_true", help="Only create schema")
    parser.add_argument("--verify", action="store_true", help="Run verification queries only")
    parser.add_argument("--reset", action="store_true", help="Drop and recreate all tables")
    parser.add_argument("--no-seed", action="store_true", help="Skip reference seeding")
    args = parser.parse_args()

    if args.verify:
        verify()
        return

    if args.reset:
        reset_schema()
        if not args.seed_only and not args.schema_only:
            run_seed()
            load_all()
            update_event_totals()
            verify()
        return

    if args.schema_only:
        create_schema()
        return

    if args.seed_only:
        run_seed()
        return

    # Default: full ETL
    if not args.no_seed:
        run_seed()

    if args.year:
        load_year(args.year)
    else:
        load_all()

    update_event_totals()
    verify()


if __name__ == "__main__":
    main()
