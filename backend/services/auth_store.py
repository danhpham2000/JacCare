from __future__ import annotations

from pathlib import Path
from typing import Any, Optional
import base64
import hashlib
import hmac
import os
import secrets
import sqlite3


BASE_DIR = Path(__file__).resolve().parents[2]
DB_PATH = BASE_DIR / "backend" / "careroute.db"


def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with connect() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS sessions (
                token TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS profiles (
                user_id INTEGER PRIMARY KEY,
                zip_code TEXT NOT NULL DEFAULT '',
                insurance_status TEXT NOT NULL DEFAULT 'uninsured',
                budget INTEGER NOT NULL DEFAULT 50,
                language TEXT NOT NULL DEFAULT 'English',
                transport_mode TEXT NOT NULL DEFAULT 'public_transit',
                care_need TEXT NOT NULL DEFAULT '',
                urgency TEXT NOT NULL DEFAULT 'today',
                household TEXT NOT NULL DEFAULT '',
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS route_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                summary TEXT NOT NULL,
                recommended_clinic TEXT,
                backup_clinic TEXT,
                payload_json TEXT NOT NULL,
                result_json TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
            );
            """
        )
        existing_columns = {
            row["name"]
            for row in conn.execute("PRAGMA table_info(profiles)").fetchall()
        }
        for column_name, column_sql in [
            ("insurance_provider", "TEXT NOT NULL DEFAULT ''"),
            ("insurance_plan", "TEXT NOT NULL DEFAULT ''"),
            ("member_id", "TEXT NOT NULL DEFAULT ''"),
        ]:
            if column_name not in existing_columns:
                conn.execute(f"ALTER TABLE profiles ADD COLUMN {column_name} {column_sql}")


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 120000)
    return f"{base64.b64encode(salt).decode()}:{base64.b64encode(digest).decode()}"


def verify_password(password: str, password_hash: str) -> bool:
    salt_encoded, digest_encoded = password_hash.split(":", 1)
    salt = base64.b64decode(salt_encoded.encode())
    expected = base64.b64decode(digest_encoded.encode())
    candidate = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 120000)
    return hmac.compare_digest(candidate, expected)


def serialize_row(row: Optional[sqlite3.Row]) -> Optional[dict[str, Any]]:
    return dict(row) if row else None


def create_user(full_name: str, email: str, password: str) -> dict[str, Any]:
    password_hash = hash_password(password)
    normalized_email = email.strip().lower()
    with connect() as conn:
        cursor = conn.execute(
            "INSERT INTO users (full_name, email, password_hash) VALUES (?, ?, ?)",
            (full_name.strip(), normalized_email, password_hash),
        )
        user_id = cursor.lastrowid
        conn.execute(
            """
            INSERT INTO profiles (user_id, zip_code, insurance_status, insurance_provider, insurance_plan, member_id, budget, language, transport_mode, care_need, urgency, household)
            VALUES (?, '', 'uninsured', '', '', '', 50, 'English', 'public_transit', '', 'today', '')
            """,
            (user_id,),
        )
        row = conn.execute(
            "SELECT id, full_name, email, created_at FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()
    return dict(row)


def authenticate_user(email: str, password: str) -> Optional[dict[str, Any]]:
    normalized_email = email.strip().lower()
    with connect() as conn:
        row = conn.execute("SELECT * FROM users WHERE email = ?", (normalized_email,)).fetchone()
    if not row:
        return None
    if not verify_password(password, row["password_hash"]):
        return None
    return {
        "id": row["id"],
        "full_name": row["full_name"],
        "email": row["email"],
        "created_at": row["created_at"],
    }


def create_session(user_id: int) -> str:
    token = secrets.token_urlsafe(32)
    with connect() as conn:
        conn.execute("INSERT INTO sessions (token, user_id) VALUES (?, ?)", (token, user_id))
    return token


def delete_session(token: str) -> None:
    with connect() as conn:
        conn.execute("DELETE FROM sessions WHERE token = ?", (token,))


def user_for_token(token: str) -> Optional[dict[str, Any]]:
    with connect() as conn:
        row = conn.execute(
            """
            SELECT users.id, users.full_name, users.email, users.created_at
            FROM sessions
            JOIN users ON users.id = sessions.user_id
            WHERE sessions.token = ?
            """,
            (token,),
        ).fetchone()
    return serialize_row(row)


def get_profile(user_id: int) -> dict[str, Any]:
    with connect() as conn:
        row = conn.execute(
            """
            SELECT zip_code, insurance_status, insurance_provider, insurance_plan, member_id, budget, language, transport_mode, care_need, urgency, household
            FROM profiles WHERE user_id = ?
            """,
            (user_id,),
        ).fetchone()
    return dict(row) if row else {
        "zip_code": "",
        "insurance_status": "uninsured",
        "insurance_provider": "",
        "insurance_plan": "",
        "member_id": "",
        "budget": 50,
        "language": "English",
        "transport_mode": "public_transit",
        "care_need": "",
        "urgency": "today",
        "household": "",
    }


def save_profile(user_id: int, profile: dict[str, Any]) -> dict[str, Any]:
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO profiles (user_id, zip_code, insurance_status, insurance_provider, insurance_plan, member_id, budget, language, transport_mode, care_need, urgency, household)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                zip_code = excluded.zip_code,
                insurance_status = excluded.insurance_status,
                insurance_provider = excluded.insurance_provider,
                insurance_plan = excluded.insurance_plan,
                member_id = excluded.member_id,
                budget = excluded.budget,
                language = excluded.language,
                transport_mode = excluded.transport_mode,
                care_need = excluded.care_need,
                urgency = excluded.urgency,
                household = excluded.household
            """,
            (
                user_id,
                profile["zip_code"],
                profile["insurance_status"],
                profile.get("insurance_provider", ""),
                profile.get("insurance_plan", ""),
                profile.get("member_id", ""),
                profile["budget"],
                profile["language"],
                profile["transport_mode"],
                profile["care_need"],
                profile["urgency"],
                profile["household"],
            ),
        )
    return get_profile(user_id)


def save_route_run(
    user_id: int,
    payload_json: str,
    result_json: str,
    summary: str,
    recommended_clinic: Optional[str],
    backup_clinic: Optional[str],
) -> int:
    with connect() as conn:
        cursor = conn.execute(
            """
            INSERT INTO route_runs (user_id, summary, recommended_clinic, backup_clinic, payload_json, result_json)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (user_id, summary, recommended_clinic, backup_clinic, payload_json, result_json),
        )
        return int(cursor.lastrowid)


def list_route_runs(user_id: int, limit: int = 10) -> list[dict[str, Any]]:
    with connect() as conn:
        rows = conn.execute(
            """
            SELECT id, summary, recommended_clinic, backup_clinic, payload_json, created_at
            FROM route_runs
            WHERE user_id = ?
            ORDER BY created_at DESC, id DESC
            LIMIT ?
            """,
            (user_id, limit),
        ).fetchall()
    return [dict(row) for row in rows]
