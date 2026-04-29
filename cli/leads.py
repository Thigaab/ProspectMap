"""Lead-tracking operations on the local SQLite DB.

User-owned data (status + notes per prospect) — distinct from the API cache
in cache.py but living in the same SQLite file. The `lead_status` table
itself is created by `cache.Cache` on init.
"""
import sqlite3
from datetime import datetime, timezone
from typing import Optional

VALID_STATUSES = ("NEW", "CONTACTED", "QUALIFIED", "WON", "LOST")


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def get_status(conn: sqlite3.Connection, place_id: str) -> Optional[dict]:
    row = conn.execute(
        "SELECT status, notes, updated_at FROM lead_status WHERE place_id = ?",
        (place_id,),
    ).fetchone()
    if not row:
        return None
    return {
        "status": row["status"],
        "notes": row["notes"],
        "updated_at": row["updated_at"],
    }


def set_status(
    conn: sqlite3.Connection,
    place_id: str,
    status: str,
    notes: Optional[str] = None,
) -> dict:
    if status not in VALID_STATUSES:
        raise ValueError(
            f"Invalid status '{status}'. Must be one of: {VALID_STATUSES}"
        )
    now = _utcnow_iso()
    conn.execute(
        "INSERT INTO lead_status (place_id, status, notes, updated_at) "
        "VALUES (?, ?, ?, ?) "
        "ON CONFLICT(place_id) DO UPDATE SET "
        "status = excluded.status, "
        "notes = excluded.notes, "
        "updated_at = excluded.updated_at",
        (place_id, status, notes, now),
    )
    conn.commit()
    return {"status": status, "notes": notes, "updated_at": now}


def list_statuses(conn: sqlite3.Connection) -> dict[str, dict]:
    """Return {place_id: {status, notes, updated_at}} for all tracked leads."""
    rows = conn.execute(
        "SELECT place_id, status, notes, updated_at FROM lead_status"
    ).fetchall()
    return {
        r["place_id"]: {
            "status": r["status"],
            "notes": r["notes"],
            "updated_at": r["updated_at"],
        }
        for r in rows
    }
