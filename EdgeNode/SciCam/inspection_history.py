from __future__ import annotations

import sqlite3
from contextlib import closing
from pathlib import Path

from .app_paths import application_root

PROJECT_ROOT = application_root()
DEFAULT_DATABASE = PROJECT_ROOT / "data" / "inspection_history.db"
DEFAULT_IMAGE_DIR = PROJECT_ROOT / "data" / "sample_images"


class InspectionHistoryStore:
    """Persistent SQLite storage for saved sample inspections."""

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
                CREATE TABLE IF NOT EXISTS inspections (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    captured_at TEXT NOT NULL,
                    sample_id TEXT NOT NULL,
                    brown_percentage REAL NOT NULL,
                    fermentation_status TEXT NOT NULL,
                    tea_quality TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    processing_ms REAL NOT NULL,
                    image_path TEXT NOT NULL
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
                    processing_ms, image_path
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record["captured_at"],
                    record["sample_id"],
                    record["brown_percentage"],
                    record["fermentation_status"],
                    record["tea_quality"],
                    record["confidence"],
                    record["processing_ms"],
                    record["image_path"],
                ),
            )
            connection.commit()

    def all_newest_first(self) -> list[dict]:
        with closing(self._connect()) as connection:
            connection.row_factory = sqlite3.Row
            rows = connection.execute(
                """
                SELECT captured_at, sample_id, brown_percentage,
                       fermentation_status, tea_quality, confidence,
                       processing_ms, image_path
                FROM inspections
                ORDER BY captured_at DESC, id DESC
                """
            ).fetchall()
        return [dict(row) for row in rows]
