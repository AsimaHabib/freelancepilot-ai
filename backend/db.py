import json
import sqlite3
from contextlib import closing
from datetime import datetime, timedelta, timezone
from pathlib import Path

# The database file is created next to this script on first run
DB_PATH = Path(__file__).parent / "freelancepilot.db"


def _connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def init_db():
    with closing(_connect()) as conn, conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL UNIQUE,
                name TEXT NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS sessions (
                token_hash TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL,
                expires_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                kind TEXT NOT NULL,
                title TEXT NOT NULL,
                input_json TEXT NOT NULL,
                result_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        # Older databases (before login) have no user_id column
        columns = [row["name"] for row in conn.execute("PRAGMA table_info(history)")]
        if "user_id" not in columns:
            conn.execute("ALTER TABLE history ADD COLUMN user_id INTEGER")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_history_user ON history (user_id, id)")


# ---------- users and sessions ----------

def create_user(email: str, name: str, password_hash: str) -> int:
    """Raises ValueError if the email is already used."""
    with closing(_connect()) as conn, conn:
        first_user = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 0
        try:
            cur = conn.execute(
                "INSERT INTO users (email, name, password_hash, created_at) VALUES (?, ?, ?, ?)",
                (email, name, password_hash, _now()),
            )
        except sqlite3.IntegrityError:
            raise ValueError("email exists")
        user_id = cur.lastrowid
        if first_user:
            # History saved before login existed belongs to the first person who signs up
            conn.execute("UPDATE history SET user_id = ? WHERE user_id IS NULL", (user_id,))
        return user_id


def get_user_by_email(email: str):
    with closing(_connect()) as conn:
        row = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    return dict(row) if row else None


def create_session(user_id: int, token_hash: str, days: int = 30) -> None:
    expires = (datetime.now(timezone.utc) + timedelta(days=days)).isoformat()
    with closing(_connect()) as conn, conn:
        conn.execute("DELETE FROM sessions WHERE expires_at < ?", (_now(),))
        conn.execute(
            "INSERT INTO sessions (token_hash, user_id, expires_at) VALUES (?, ?, ?)",
            (token_hash, user_id, expires),
        )


def get_session_user(token_hash: str):
    with closing(_connect()) as conn:
        row = conn.execute(
            "SELECT users.id, users.name, users.email FROM sessions "
            "JOIN users ON users.id = sessions.user_id "
            "WHERE sessions.token_hash = ? AND sessions.expires_at > ?",
            (token_hash, _now()),
        ).fetchone()
    return dict(row) if row else None


def delete_session(token_hash: str) -> None:
    with closing(_connect()) as conn, conn:
        conn.execute("DELETE FROM sessions WHERE token_hash = ?", (token_hash,))


# ---------- history (every query is limited to one user) ----------

def save_record(user_id: int, kind: str, title: str, input_data: dict, result: dict) -> int:
    with closing(_connect()) as conn, conn:
        cur = conn.execute(
            "INSERT INTO history (user_id, kind, title, input_json, result_json, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (user_id, kind, title, json.dumps(input_data), json.dumps(result), _now()),
        )
        return cur.lastrowid


def list_records(user_id: int, limit: int = 100) -> list:
    with closing(_connect()) as conn:
        rows = conn.execute(
            "SELECT id, kind, title, result_json, created_at FROM history "
            "WHERE user_id = ? ORDER BY id DESC LIMIT ?",
            (user_id, limit),
        ).fetchall()

    items = []
    for row in rows:
        result = json.loads(row["result_json"])
        if row["kind"] in ("analyze", "proposal"):
            summary = result.get("project_type")
        else:
            summary = result.get("verdict")
        items.append(
            {
                "id": row["id"],
                "kind": row["kind"],
                "title": row["title"],
                "summary": summary,
                "created_at": row["created_at"],
            }
        )
    return items


def get_record(user_id: int, record_id: int):
    with closing(_connect()) as conn:
        row = conn.execute(
            "SELECT * FROM history WHERE id = ? AND user_id = ?", (record_id, user_id)
        ).fetchone()
    if row is None:
        return None
    return {
        "id": row["id"],
        "kind": row["kind"],
        "title": row["title"],
        "input": json.loads(row["input_json"]),
        "result": json.loads(row["result_json"]),
        "created_at": row["created_at"],
    }


def delete_record(user_id: int, record_id: int) -> bool:
    with closing(_connect()) as conn, conn:
        cur = conn.execute(
            "DELETE FROM history WHERE id = ? AND user_id = ?", (record_id, user_id)
        )
        return cur.rowcount > 0