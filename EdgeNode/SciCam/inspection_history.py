from __future__ import annotations

import sqlite3
from contextlib import closing
from pathlib import Path

from .app_paths import application_root

PROJECT_ROOT = application_root()
DEFAULT_DATABASE = PROJECT_ROOT / "data" / "inspection_history.db"
DEFAULT_IMAGE_DIR = PROJECT_ROOT / "data" / "evidence"


class EventHistoryStore:
    """Persistent SQLite storage for AI-camera detection events."""

    def __init__(self, database_path: Path = DEFAULT_DATABASE) -> None:
        self.database_path = Path(database_path)
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        DEFAULT_IMAGE_DIR.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self):
        return sqlite3.connect(self.database_path)

    def _initialize(self) -> None:
        with closing(self._connect()) as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_date TEXT NOT NULL,
                    event_name TEXT NOT NULL,
                    evidence_path TEXT NOT NULL
                )
                """
            )
            connection.commit()

    def add(self, record: dict) -> None:
        with closing(self._connect()) as connection:
            connection.execute(
                """
                INSERT INTO events (
                    event_date, event_name, evidence_path
                ) VALUES (?, ?, ?)
                """,
                (
                    record["event_date"],
                    record["event_name"],
                    record["evidence_path"],
                ),
            )
            record["rowid"] = connection.execute(
                "SELECT last_insert_rowid()"
            ).fetchone()[0]
            connection.commit()

    def all_newest_first(self) -> list[dict]:
        with closing(self._connect()) as connection:
            connection.row_factory = sqlite3.Row
            rows = connection.execute(
                """
                SELECT id AS rowid, event_date, event_name, evidence_path
                FROM events
                ORDER BY event_date DESC, id DESC
                """
            ).fetchall()
        return [dict(row) for row in rows]

    def clear(self) -> int:
        """Delete all event rows while preserving saved evidence files."""
        with closing(self._connect()) as connection:
            count = connection.execute(
                "SELECT COUNT(*) FROM events"
            ).fetchone()[0]
            connection.execute("DELETE FROM events")
            connection.execute(
                "DELETE FROM sqlite_sequence WHERE name = 'events'"
            )
            connection.commit()
        return count


# Backward-compatible import for older integrations.
InspectionHistoryStore = EventHistoryStore
