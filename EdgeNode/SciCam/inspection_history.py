from __future__ import annotations

import sqlite3
from contextlib import closing
from pathlib import Path
import ast
import json

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


class InspectionHistoryStore:
    """Persistent SQLite storage for TeaVision inspection metrics."""

    def __init__(self, database_path: Path = DEFAULT_DATABASE) -> None:
        self.database_path = Path(database_path)
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self):
        return sqlite3.connect(self.database_path)

    def _initialize(self) -> None:
        with closing(self._connect()) as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS inspections (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    captured_at TEXT NOT NULL,
                    sample_id TEXT NOT NULL,
                    brown_percentage REAL NOT NULL,
                    fermentation_status TEXT NOT NULL,
                    tea_quality TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    processing_ms REAL NOT NULL,
                    image_path TEXT NOT NULL,
                    average_rgb TEXT NOT NULL,
                    average_lab TEXT NOT NULL,
                    brightness REAL NOT NULL
                )
                """
            )
            connection.commit()

    def add(self, record: dict) -> None:
        with closing(self._connect()) as connection:
            connection.execute(
                """
                INSERT INTO inspections (
                    captured_at, sample_id, brown_percentage,
                    fermentation_status, tea_quality, confidence,
                    processing_ms, image_path, average_rgb, average_lab,
                    brightness
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record["captured_at"],
                    record["sample_id"],
                    float(record["brown_percentage"]),
                    record["fermentation_status"],
                    record.get("tea_quality", ""),
                    float(record["confidence"]),
                    float(record["processing_ms"]),
                    record["image_path"],
                    json.dumps(tuple(record.get("average_rgb", (0, 0, 0)))),
                    json.dumps(
                        tuple(record.get("average_lab", (0.0, 0.0, 0.0)))
                    ),
                    float(record.get("brightness", 0.0)),
                ),
            )
            record["rowid"] = connection.execute(
                "SELECT last_insert_rowid()"
            ).fetchone()[0]
            connection.commit()

    @staticmethod
    def _parse_tuple(value, default):
        if value in (None, ""):
            return default
        if isinstance(value, (list, tuple)):
            return tuple(value)
        for parser in (json.loads, ast.literal_eval):
            try:
                parsed = parser(value)
            except (SyntaxError, ValueError, TypeError, json.JSONDecodeError):
                continue
            if isinstance(parsed, (list, tuple)):
                return tuple(parsed)
        return default

    def all_newest_first(self) -> list[dict]:
        with closing(self._connect()) as connection:
            connection.row_factory = sqlite3.Row
            rows = connection.execute(
                """
                SELECT id AS rowid, captured_at, sample_id, brown_percentage,
                       fermentation_status, tea_quality, confidence,
                       processing_ms, image_path, average_rgb, average_lab,
                       brightness
                FROM inspections
                ORDER BY captured_at DESC, id DESC
                """
            ).fetchall()
        records = []
        for row in rows:
            record = dict(row)
            record["average_rgb"] = self._parse_tuple(
                record["average_rgb"],
                (0, 0, 0),
            )
            record["average_lab"] = self._parse_tuple(
                record["average_lab"],
                (0.0, 0.0, 0.0),
            )
            records.append(record)
        return records

    def clear(self) -> int:
        with closing(self._connect()) as connection:
            count = connection.execute(
                "SELECT COUNT(*) FROM inspections"
            ).fetchone()[0]
            connection.execute("DELETE FROM inspections")
            connection.execute(
                "DELETE FROM sqlite_sequence WHERE name = 'inspections'"
            )
            connection.commit()
        return count
