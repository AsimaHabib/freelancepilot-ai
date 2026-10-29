import json
import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path

# The database file is created next to this script on first run
DB_PATH = Path(__file__).parent / "freelancepilot.db"


def _connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with closing(_connect()) as conn, conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                kind TEXT NOT NULL,
                title TEXT NOT NULL,
                input_json TEXT NOT NULL,
                result_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )


def save_record(kind: str, title: str, input_data: dict, result: dict) -> int:
    with closing(_connect()) as conn, conn:
        cur = conn.execute(
            "INSERT INTO history (kind, title, input_json, result_json, created_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (
                kind,
                title,
                json.dumps(input_data),
                json.dumps(result),
                datetime.now(timezone.utc).isoformat(),
            ),
        )
        return cur.lastrowid


def list_records(limit: int = 100) -> list:
    with closing(_connect()) as conn:
        rows = conn.execute(
            "SELECT id, kind, title, result_json, created_at FROM history "
            "ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()

    items = []
    for row in rows:
        result = json.loads(row["result_json"])
        summary = result.get("project_type") if row["kind"] in ("analyze", "proposal") else result.get("verdict")
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


def get_record(record_id: int):
    with closing(_connect()) as conn:
        row = conn.execute("SELECT * FROM history WHERE id = ?", (record_id,)).fetchone()
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


def delete_record(record_id: int) -> bool:
    with closing(_connect()) as conn, conn:
        cur = conn.execute("DELETE FROM history WHERE id = ?", (record_id,))
        return cur.rowcount > 0