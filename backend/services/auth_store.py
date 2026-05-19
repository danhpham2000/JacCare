from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional
import base64
import hashlib
import hmac
import os
import secrets
import sqlite3

from dotenv import load_dotenv
from neo4j import GraphDatabase


BASE_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BASE_DIR / ".env")

DB_PATH = Path(os.getenv("CAREROUTE_DB_PATH", str(BASE_DIR / "backend" / "careroute.db")))
AUTH_STORE = os.getenv("AUTH_STORE", "sqlite").strip().lower()

_AUTH_DRIVER = None


def using_neo4j() -> bool:
    return AUTH_STORE == "neo4j" and bool(os.getenv("NEO4J_URI") and os.getenv("NEO4J_USERNAME") and os.getenv("NEO4J_PASSWORD"))


def auth_driver():
    global _AUTH_DRIVER
    if not using_neo4j():
        return None
    if _AUTH_DRIVER is None:
        _AUTH_DRIVER = GraphDatabase.driver(
            os.getenv("NEO4J_URI"),
            auth=(os.getenv("NEO4J_USERNAME"), os.getenv("NEO4J_PASSWORD")),
        )
    return _AUTH_DRIVER


def auth_database() -> Optional[str]:
    return os.getenv("NEO4J_DATABASE") or None


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    if using_neo4j():
        driver = auth_driver()
        if driver is None:
            return
        with driver.session(database=auth_database()) as session:
            session.run("CREATE CONSTRAINT auth_user_id IF NOT EXISTS FOR (u:AuthUser) REQUIRE u.id IS UNIQUE")
            session.run("CREATE CONSTRAINT auth_user_email IF NOT EXISTS FOR (u:AuthUser) REQUIRE u.email IS UNIQUE")
            session.run("CREATE CONSTRAINT auth_session_token IF NOT EXISTS FOR (s:AuthSession) REQUIRE s.token IS UNIQUE")
            session.run("CREATE CONSTRAINT auth_profile_user_id IF NOT EXISTS FOR (p:AuthProfile) REQUIRE p.user_id IS UNIQUE")
            session.run("CREATE CONSTRAINT auth_route_run_id IF NOT EXISTS FOR (r:AuthRouteRun) REQUIRE r.id IS UNIQUE")
        return

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
        existing_columns = {row["name"] for row in conn.execute("PRAGMA table_info(profiles)").fetchall()}
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


def default_profile() -> dict[str, Any]:
    return {
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


def create_user(full_name: str, email: str, password: str) -> dict[str, Any]:
    password_hash = hash_password(password)
    normalized_email = email.strip().lower()

    if using_neo4j():
        driver = auth_driver()
        assert driver is not None
        with driver.session(database=auth_database()) as session:
            existing = session.run("MATCH (u:AuthUser {email: $email}) RETURN u.id AS id", email=normalized_email).single()
            if existing:
                raise sqlite3.IntegrityError("duplicate email")

            row = session.execute_write(
                _create_user_neo4j,
                full_name.strip(),
                normalized_email,
                password_hash,
            )
        return row

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


def _create_user_neo4j(tx, full_name: str, email: str, password_hash: str) -> dict[str, Any]:
    next_id = tx.run("MATCH (u:AuthUser) RETURN coalesce(max(u.id), 0) + 1 AS next_id").single()["next_id"]
    created_at = now_iso()
    tx.run(
        """
        CREATE (u:AuthUser {
            id: $id,
            full_name: $full_name,
            email: $email,
            password_hash: $password_hash,
            created_at: $created_at
        })
        CREATE (p:AuthProfile {
            user_id: $id,
            zip_code: '',
            insurance_status: 'uninsured',
            insurance_provider: '',
            insurance_plan: '',
            member_id: '',
            budget: 50,
            language: 'English',
            transport_mode: 'public_transit',
            care_need: '',
            urgency: 'today',
            household: ''
        })
        MERGE (u)-[:HAS_PROFILE]->(p)
        """,
        id=int(next_id),
        full_name=full_name,
        email=email,
        password_hash=password_hash,
        created_at=created_at,
    )
    return {"id": int(next_id), "full_name": full_name, "email": email, "created_at": created_at}


def authenticate_user(email: str, password: str) -> Optional[dict[str, Any]]:
    normalized_email = email.strip().lower()

    if using_neo4j():
        driver = auth_driver()
        assert driver is not None
        with driver.session(database=auth_database()) as session:
            row = session.run(
                """
                MATCH (u:AuthUser {email: $email})
                RETURN u.id AS id, u.full_name AS full_name, u.email AS email, u.created_at AS created_at, u.password_hash AS password_hash
                """,
                email=normalized_email,
            ).single()
        if not row:
            return None
        data = row.data()
        if not verify_password(password, data["password_hash"]):
            return None
        return {key: data[key] for key in ["id", "full_name", "email", "created_at"]}

    with connect() as conn:
        row = conn.execute("SELECT * FROM users WHERE email = ?", (normalized_email,)).fetchone()
    if not row:
        return None
    if not verify_password(password, row["password_hash"]):
        return None
    return {"id": row["id"], "full_name": row["full_name"], "email": row["email"], "created_at": row["created_at"]}


def create_session(user_id: int) -> str:
    token = secrets.token_urlsafe(32)

    if using_neo4j():
        driver = auth_driver()
        assert driver is not None
        with driver.session(database=auth_database()) as session:
            session.run(
                """
                CREATE (s:AuthSession {token: $token, user_id: $user_id, created_at: $created_at})
                """,
                token=token,
                user_id=int(user_id),
                created_at=now_iso(),
            )
        return token

    with connect() as conn:
        conn.execute("INSERT INTO sessions (token, user_id) VALUES (?, ?)", (token, user_id))
    return token


def delete_session(token: str) -> None:
    if using_neo4j():
        driver = auth_driver()
        assert driver is not None
        with driver.session(database=auth_database()) as session:
            session.run("MATCH (s:AuthSession {token: $token}) DETACH DELETE s", token=token)
        return

    with connect() as conn:
        conn.execute("DELETE FROM sessions WHERE token = ?", (token,))


def user_for_token(token: str) -> Optional[dict[str, Any]]:
    if using_neo4j():
        driver = auth_driver()
        assert driver is not None
        with driver.session(database=auth_database()) as session:
            row = session.run(
                """
                MATCH (s:AuthSession {token: $token})
                MATCH (u:AuthUser {id: s.user_id})
                RETURN u.id AS id, u.full_name AS full_name, u.email AS email, u.created_at AS created_at
                """,
                token=token,
            ).single()
        return row.data() if row else None

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
    if using_neo4j():
        driver = auth_driver()
        assert driver is not None
        with driver.session(database=auth_database()) as session:
            row = session.run(
                """
                MATCH (p:AuthProfile {user_id: $user_id})
                RETURN p.zip_code AS zip_code,
                       p.insurance_status AS insurance_status,
                       p.insurance_provider AS insurance_provider,
                       p.insurance_plan AS insurance_plan,
                       p.member_id AS member_id,
                       p.budget AS budget,
                       p.language AS language,
                       p.transport_mode AS transport_mode,
                       p.care_need AS care_need,
                       p.urgency AS urgency,
                       p.household AS household
                """,
                user_id=int(user_id),
            ).single()
        return row.data() if row else default_profile()

    with connect() as conn:
        row = conn.execute(
            """
            SELECT zip_code, insurance_status, insurance_provider, insurance_plan, member_id, budget, language, transport_mode, care_need, urgency, household
            FROM profiles WHERE user_id = ?
            """,
            (user_id,),
        ).fetchone()
    return dict(row) if row else default_profile()


def save_profile(user_id: int, profile: dict[str, Any]) -> dict[str, Any]:
    if using_neo4j():
        driver = auth_driver()
        assert driver is not None
        payload = default_profile()
        payload.update(profile)
        payload.pop("user_id", None)
        with driver.session(database=auth_database()) as session:
            session.run(
                """
                MERGE (p:AuthProfile {user_id: $user_id})
                SET p.zip_code = $zip_code,
                    p.insurance_status = $insurance_status,
                    p.insurance_provider = $insurance_provider,
                    p.insurance_plan = $insurance_plan,
                    p.member_id = $member_id,
                    p.budget = $budget,
                    p.language = $language,
                    p.transport_mode = $transport_mode,
                    p.care_need = $care_need,
                    p.urgency = $urgency,
                    p.household = $household
                WITH p
                MATCH (u:AuthUser {id: $user_id})
                MERGE (u)-[:HAS_PROFILE]->(p)
                """,
                user_id=int(user_id),
                **payload,
            )
        return get_profile(user_id)

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
    if using_neo4j():
        driver = auth_driver()
        assert driver is not None
        with driver.session(database=auth_database()) as session:
            record = session.execute_write(
                _save_route_run_neo4j,
                int(user_id),
                payload_json,
                result_json,
                summary,
                recommended_clinic,
                backup_clinic,
            )
        return int(record["id"])

    with connect() as conn:
        cursor = conn.execute(
            """
            INSERT INTO route_runs (user_id, summary, recommended_clinic, backup_clinic, payload_json, result_json)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (user_id, summary, recommended_clinic, backup_clinic, payload_json, result_json),
        )
        return int(cursor.lastrowid)


def _save_route_run_neo4j(
    tx,
    user_id: int,
    payload_json: str,
    result_json: str,
    summary: str,
    recommended_clinic: Optional[str],
    backup_clinic: Optional[str],
) -> dict[str, Any]:
    next_id = tx.run("MATCH (r:AuthRouteRun) RETURN coalesce(max(r.id), 0) + 1 AS next_id").single()["next_id"]
    created_at = now_iso()
    tx.run(
        """
        CREATE (r:AuthRouteRun {
            id: $id,
            user_id: $user_id,
            summary: $summary,
            recommended_clinic: $recommended_clinic,
            backup_clinic: $backup_clinic,
            payload_json: $payload_json,
            result_json: $result_json,
            created_at: $created_at
        })
        WITH r
        MATCH (u:AuthUser {id: $user_id})
        MERGE (u)-[:HAS_ROUTE_RUN]->(r)
        """,
        id=int(next_id),
        user_id=user_id,
        summary=summary,
        recommended_clinic=recommended_clinic,
        backup_clinic=backup_clinic,
        payload_json=payload_json,
        result_json=result_json,
        created_at=created_at,
    )
    return {"id": int(next_id)}


def list_route_runs(user_id: int, limit: int = 10) -> list[dict[str, Any]]:
    if using_neo4j():
        driver = auth_driver()
        assert driver is not None
        with driver.session(database=auth_database()) as session:
            result = session.run(
                """
                MATCH (r:AuthRouteRun {user_id: $user_id})
                RETURN r.id AS id,
                       r.summary AS summary,
                       r.recommended_clinic AS recommended_clinic,
                       r.backup_clinic AS backup_clinic,
                       r.payload_json AS payload_json,
                       r.created_at AS created_at
                ORDER BY r.created_at DESC, r.id DESC
                LIMIT $limit
                """,
                user_id=int(user_id),
                limit=int(limit),
            )
            return [record.data() for record in result]

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
