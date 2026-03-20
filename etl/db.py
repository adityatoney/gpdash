"""Database connection and helper utilities."""

import os
import psycopg2
import psycopg2.extras
from contextlib import contextmanager
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://gpdash:gpdash_dev@localhost:5433/gpdash")


def get_connection():
    return psycopg2.connect(DATABASE_URL)


@contextmanager
def get_cursor(commit=True):
    conn = get_connection()
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        yield cur
        if commit:
            conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()


def execute_sql_file(filepath):
    """Execute a .sql file against the database."""
    with open(filepath, "r") as f:
        sql = f.read()
    with get_cursor() as cur:
        cur.execute(sql)


def bulk_insert(table, columns, rows):
    """Insert multiple rows using execute_values for performance."""
    if not rows:
        return 0
    cols = ", ".join(columns)
    template = "(" + ", ".join(["%s"] * len(columns)) + ")"
    sql = f"INSERT INTO {table} ({cols}) VALUES %s ON CONFLICT DO NOTHING"
    with get_cursor() as cur:
        psycopg2.extras.execute_values(cur, sql, rows, template=template)
        return len(rows)


def upsert_ref(table, unique_col, unique_val, extra_cols=None):
    """Insert-or-get for reference tables. Returns the PK id."""
    extra_cols = extra_cols or {}
    with get_cursor() as cur:
        cur.execute(f"SELECT {table.replace('ref_', '')}_{unique_col.replace('_code', '_id').replace('_name', '_id')} FROM {table} WHERE {unique_col} = %s", (unique_val,))
        row = cur.fetchone()
        if row:
            return row[0]
        cols = [unique_col] + list(extra_cols.keys())
        vals = [unique_val] + list(extra_cols.values())
        placeholders = ", ".join(["%s"] * len(cols))
        col_str = ", ".join(cols)
        pk_col = table.replace("ref_", "") + "_id"
        cur.execute(
            f"INSERT INTO {table} ({col_str}) VALUES ({placeholders}) RETURNING {pk_col}",
            vals,
        )
        return cur.fetchone()[0]


def get_or_create_event(year):
    """Get or create an event row, return event_id."""
    with get_cursor() as cur:
        cur.execute("SELECT event_id FROM events WHERE event_year = %s", (year,))
        row = cur.fetchone()
        if row:
            return row[0]
        cur.execute(
            "INSERT INTO events (event_year, event_name) VALUES (%s, %s) RETURNING event_id",
            (year, f"Guru Purnima {year}"),
        )
        return cur.fetchone()[0]


def get_or_create_person(cur, *, mahatma_id=None, family_id=None, first_name, last_name, **kwargs):
    """Find or create a person. Returns person_id.

    Matching priority:
    1. mahatma_id (if provided and not None)
    2. family_id + lowercase name match
    3. Create new
    """
    if mahatma_id:
        cur.execute("SELECT person_id FROM persons WHERE mahatma_id = %s", (mahatma_id,))
        row = cur.fetchone()
        if row:
            return row[0]

    if family_id and first_name and last_name:
        cur.execute(
            "SELECT person_id FROM persons WHERE family_id = %s AND LOWER(first_name) = LOWER(%s) AND LOWER(last_name) = LOWER(%s)",
            (family_id, first_name, last_name),
        )
        row = cur.fetchone()
        if row:
            return row[0]

    # Create new person
    cols = ["first_name", "last_name"]
    vals = [first_name, last_name]

    if mahatma_id:
        cols.append("mahatma_id")
        vals.append(mahatma_id)
    if family_id:
        cols.append("family_id")
        vals.append(family_id)

    for k, v in kwargs.items():
        if v is not None:
            cols.append(k)
            vals.append(v)

    col_str = ", ".join(cols)
    placeholders = ", ".join(["%s"] * len(cols))
    cur.execute(
        f"INSERT INTO persons ({col_str}) VALUES ({placeholders}) RETURNING person_id",
        vals,
    )
    return cur.fetchone()[0]
