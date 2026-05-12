import sqlite3
import json
from pathlib import Path
from datetime import datetime, timezone


DB_PATH = "data/applications.db"


def _get_conn() -> sqlite3.Connection:
    """Get a database connection with row factory for dict-like access."""
    Path("data").mkdir(exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create the applications table if it doesn't exist."""
    conn = _get_conn()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS applications (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            company     TEXT NOT NULL,
            role        TEXT NOT NULL,
            location    TEXT,
            fit_score   INTEGER NOT NULL,
            status      TEXT NOT NULL DEFAULT 'To Apply',
            cover_letter TEXT NOT NULL,
            cv_notes    TEXT NOT NULL,
            company_brief TEXT NOT NULL,
            quality_flags TEXT NOT NULL DEFAULT '[]',
            red_flags   TEXT NOT NULL DEFAULT '[]',
            required_skills TEXT NOT NULL DEFAULT '[]',
            raw_text    TEXT,
            created_at  TEXT NOT NULL,
            cv_chunks   TEXT NOT NULL DEFAULT '[]'
        )
    """)
    conn.commit()
    conn.close()


def save_application(package_data: dict) -> int:
    """
    Save a completed application package to SQLite.
    Returns the new row ID.
    """
    conn = _get_conn()
    cursor = conn.execute("""
        INSERT INTO applications (
            company, role, location, fit_score, status,
            cover_letter, cv_notes, company_brief,
            quality_flags, red_flags, required_skills,
            raw_text, created_at, cv_chunks
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        package_data["company_name"],
        package_data["role_title"],
        package_data.get("location", ""),
        package_data["fit_score"],
        package_data.get("status", "To Apply"),
        package_data["cover_letter"],
        json.dumps(package_data["cv_notes"]),
        package_data["company_brief"],
        json.dumps(package_data.get("quality_flags", [])),
        json.dumps(package_data.get("red_flags", [])),
        json.dumps(package_data.get("required_skills", [])),
        package_data.get("raw_text", ""),
        datetime.now(timezone.utc).isoformat(),
        json.dumps(package_data.get("cv_chunks", []))
    ))
    conn.commit()
    row_id = cursor.lastrowid
    conn.close()
    return row_id


def get_all_applications() -> list[dict]:
    """
    Return all applications ordered by date descending.
    """
    conn = _get_conn()
    rows = conn.execute("""
        SELECT id, company, role, fit_score, status, created_at
        FROM applications
        ORDER BY created_at DESC
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_application(app_id: int) -> dict | None:
    """
    Return a single full application package by ID.
    """
    conn = _get_conn()
    row = conn.execute(
        "SELECT * FROM applications WHERE id = ?", (app_id,)
    ).fetchone()
    conn.close()

    if not row:
        return None

    data = dict(row)
    data["cv_notes"] = json.loads(data["cv_notes"])
    data["quality_flags"] = json.loads(data["quality_flags"])
    data["red_flags"] = json.loads(data["red_flags"])
    data["required_skills"] = json.loads(data["required_skills"])
    data["cv_chunks"] = json.loads(data["cv_chunks"])
    return data


def update_status(app_id: int, status: str) -> bool:
    """
    Update the status of an application.
    Returns True if a row was updated.
    """
    conn = _get_conn()
    cursor = conn.execute(
        "UPDATE applications SET status = ? WHERE id = ?",
        (status, app_id)
    )
    conn.commit()
    updated = cursor.rowcount > 0
    conn.close()
    return updated