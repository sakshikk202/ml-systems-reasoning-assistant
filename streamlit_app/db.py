import os
import json
import psycopg
from psycopg.rows import dict_row

def get_db_url() -> str:
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        raise RuntimeError("DATABASE_URL is not set. Add it to Streamlit Secrets or local env.")
    return db_url

def get_conn():
    # Neon requires sslmode=require. Keep it in your DATABASE_URL.
    return psycopg.connect(get_db_url(), row_factory=dict_row)

def fetch_scenarios():
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, slug, title, description
                FROM scenarios
                ORDER BY created_at DESC
            """)
            return cur.fetchall()

def insert_diagnosis_run(scenario_id: str | None, prompt: str, diagnosis: dict):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO diagnosis_runs (scenario_id, input, diagnosis)
                VALUES (%s, %s, %s::jsonb)
                RETURNING id, created_at
                """,
                (scenario_id, prompt, json.dumps(diagnosis)),
            )
            row = cur.fetchone()
            conn.commit()
            return row

def fetch_recent_runs(limit: int = 30):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, scenario_id, input, diagnosis, created_at
                FROM diagnosis_runs
                ORDER BY created_at DESC
                LIMIT %s
                """,
                (limit,),
            )
            return cur.fetchall()