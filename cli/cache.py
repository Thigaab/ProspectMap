"""SQLite cache for Google Places results — avoids redundant API calls.

Two-level cache:
- `searches` keyed by (city, type_filter, radius) with a TTL.
- `prospects` keyed by `place_id`, storing the raw Place Details JSON.
- `search_results` is the link table between both.

A cache hit on `searches` rehydrates the full prospect list straight from
SQLite, skipping the geocoding, nearby-search and place-details API calls.
"""
import json
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

SCHEMA = """
CREATE TABLE IF NOT EXISTS searches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    city TEXT NOT NULL,
    type_filter TEXT NOT NULL,
    radius INTEGER NOT NULL,
    fetched_at TEXT NOT NULL,
    UNIQUE(city, type_filter, radius)
);

CREATE TABLE IF NOT EXISTS search_results (
    search_id INTEGER NOT NULL,
    place_id TEXT NOT NULL,
    PRIMARY KEY (search_id, place_id),
    FOREIGN KEY (search_id) REFERENCES searches(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS prospects (
    place_id TEXT PRIMARY KEY,
    raw TEXT NOT NULL,
    fetched_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS lead_status (
    place_id TEXT PRIMARY KEY,
    status TEXT NOT NULL DEFAULT 'NEW',
    notes TEXT,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (place_id) REFERENCES prospects(place_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS web_audits (
    url TEXT PRIMARY KEY,
    raw TEXT NOT NULL,
    fetched_at TEXT NOT NULL
);
"""


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Cache:
    def __init__(self, path: Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(self.path))
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.conn.executescript(SCHEMA)
        self.conn.commit()

    def __enter__(self) -> "Cache":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def close(self) -> None:
        self.conn.close()

    def get_search(
        self, city: str, type_filter: str, radius: int, ttl_days: int
    ) -> Optional[tuple[list[dict], datetime]]:
        """Return (places, fetched_at) if a fresh entry exists, else None."""
        row = self.conn.execute(
            "SELECT id, fetched_at FROM searches "
            "WHERE city = ? AND type_filter = ? AND radius = ?",
            (city, type_filter, radius),
        ).fetchone()
        if not row:
            return None

        fetched_at = datetime.fromisoformat(row["fetched_at"])
        if _utcnow() - fetched_at > timedelta(days=ttl_days):
            return None

        rows = self.conn.execute(
            "SELECT p.raw FROM prospects p "
            "JOIN search_results sr ON sr.place_id = p.place_id "
            "WHERE sr.search_id = ?",
            (row["id"],),
        ).fetchall()
        places = [json.loads(r["raw"]) for r in rows]
        return places, fetched_at

    def delete_prospect(self, place_id: str) -> bool:
        """Hard-delete a prospect and every trace of it.

        Removes search_results rows pointing at it (no FK on place_id, so
        we clean them ourselves) and the prospects row (which cascades to
        lead_status). Returns True if a row was removed.
        """
        cur = self.conn.cursor()
        cur.execute("DELETE FROM search_results WHERE place_id = ?", (place_id,))
        cur.execute("DELETE FROM prospects WHERE place_id = ?", (place_id,))
        removed = cur.rowcount > 0
        self.conn.commit()
        return removed

    def delete_search(self, search_id: int) -> Optional[int]:
        """Hard-delete a search and every prospect that belonged to it.

        Per the user's intent: prospects are removed even if they also
        belonged to other searches. Cascades:
        - search row → search_results (FK ON DELETE CASCADE)
        - prospects row → lead_status (FK ON DELETE CASCADE)
        - search_results rows from *other* searches that referenced the
          now-deleted prospects are cleaned up explicitly.

        Returns the number of prospects deleted, or None if the search
        doesn't exist.
        """
        cur = self.conn.cursor()
        if not cur.execute(
            "SELECT 1 FROM searches WHERE id = ?", (search_id,)
        ).fetchone():
            return None

        place_ids = [
            row["place_id"]
            for row in cur.execute(
                "SELECT place_id FROM search_results WHERE search_id = ?",
                (search_id,),
            ).fetchall()
        ]

        cur.execute("DELETE FROM searches WHERE id = ?", (search_id,))
        if place_ids:
            placeholders = ",".join("?" for _ in place_ids)
            cur.execute(
                f"DELETE FROM search_results WHERE place_id IN ({placeholders})",
                place_ids,
            )
            cur.execute(
                f"DELETE FROM prospects WHERE place_id IN ({placeholders})",
                place_ids,
            )
        self.conn.commit()
        return len(place_ids)

    def save_search(
        self, city: str, type_filter: str, radius: int, places: list[dict]
    ) -> None:
        """Upsert the search row, the prospect rows, and the link table."""
        now_iso = _utcnow().isoformat()
        cur = self.conn.cursor()

        cur.execute(
            "INSERT OR IGNORE INTO searches (city, type_filter, radius, fetched_at) "
            "VALUES (?, ?, ?, ?)",
            (city, type_filter, radius, now_iso),
        )
        cur.execute(
            "UPDATE searches SET fetched_at = ? "
            "WHERE city = ? AND type_filter = ? AND radius = ?",
            (now_iso, city, type_filter, radius),
        )
        search_id = cur.execute(
            "SELECT id FROM searches "
            "WHERE city = ? AND type_filter = ? AND radius = ?",
            (city, type_filter, radius),
        ).fetchone()["id"]

        cur.execute("DELETE FROM search_results WHERE search_id = ?", (search_id,))

        for place in places:
            place_id = place.get("place_id")
            if not place_id:
                continue
            cur.execute(
                "INSERT INTO prospects (place_id, raw, fetched_at) "
                "VALUES (?, ?, ?) "
                "ON CONFLICT(place_id) DO UPDATE SET "
                "raw = excluded.raw, fetched_at = excluded.fetched_at",
                (place_id, json.dumps(place, ensure_ascii=False), now_iso),
            )
            cur.execute(
                "INSERT OR IGNORE INTO search_results (search_id, place_id) "
                "VALUES (?, ?)",
                (search_id, place_id),
            )
        self.conn.commit()
