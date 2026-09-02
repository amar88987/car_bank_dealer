import os
from pathlib import Path
import psycopg
from psycopg.rows import dict_row
from config import DATABASE_URL


def get_connection():
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL is not configured. Put your Supabase PostgreSQL URL in .env")
    return psycopg.connect(DATABASE_URL, row_factory=dict_row)


def initialize_database():
    """Create required tables and demo data without deleting existing data."""
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL is not configured")
    schema_path = Path(__file__).resolve().parent.parent / "database" / "schema.sql"
    sql = schema_path.read_text(encoding="utf-8")
    # psycopg can execute the whole schema in one call for PostgreSQL.
    with get_connection() as conn:
        conn.execute(sql)
        conn.commit()

def get_cars():
    with get_connection() as conn:
        return conn.execute("""
            SELECT id, brand, model, year, price::float AS price, color, status
            FROM cars ORDER BY id
        """).fetchall()

def get_customers():
    with get_connection() as conn:
        return conn.execute("""
            SELECT id, name, phone, email, national_id
            FROM customers ORDER BY id
        """).fetchall()

def create_financing_request(customer_id, car_id, amount, months, loan_id, status, bank_message):
    with get_connection() as conn:
        return conn.execute("""
            INSERT INTO financing_requests
            (customer_id, car_id, amount, months, loan_id, status, bank_message)
            VALUES (%s,%s,%s,%s,%s,%s,%s)
            RETURNING id
        """, (customer_id, car_id, amount, months, loan_id, status, bank_message)).fetchone()["id"]

def get_financing_requests():
    with get_connection() as conn:
        return conn.execute("""
            SELECT fr.id, fr.customer_id, c.name AS customer_name,
                   fr.car_id, CONCAT(cars.brand, ' ', cars.model) AS car_name,
                   fr.amount::float AS amount, fr.months, fr.loan_id,
                   fr.status, fr.bank_message, fr.created_at::text AS created_at
            FROM financing_requests fr
            JOIN customers c ON c.id = fr.customer_id
            JOIN cars ON cars.id = fr.car_id
            ORDER BY fr.id DESC
        """).fetchall()
