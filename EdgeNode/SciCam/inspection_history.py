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
                    image_path TEXT NOT NULL,
                    average_rgb TEXT NOT NULL DEFAULT '0,0,0',
                    average_lab TEXT NOT NULL DEFAULT '0,0,0',
                    brightness REAL NOT NULL DEFAULT 0
                )
                """
            )
            columns = {
                row[1] for row in connection.execute(
                    "PRAGMA table_info(inspections)"
                ).fetchall()
            }
            migrations = {
                "average_rgb": "TEXT NOT NULL DEFAULT '0,0,0'",
                "average_lab": "TEXT NOT NULL DEFAULT '0,0,0'",
                "brightness": "REAL NOT NULL DEFAULT 0",
            }
            for name, declaration in migrations.items():
                if name not in columns:
                    connection.execute(
                        f"ALTER TABLE inspections ADD COLUMN {name} {declaration}"
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
                    record["brown_percentage"],
                    record["fermentation_status"],
                    record["tea_quality"],
                    record["confidence"],
                    record["processing_ms"],
                    record["image_path"],
                    ",".join(str(value) for value in record["average_rgb"]),
                    ",".join(str(value) for value in record["average_lab"]),
                    record["brightness"],
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
                       processing_ms, image_path, average_rgb, average_lab,
                       brightness
                FROM inspections
                ORDER BY captured_at DESC, id DESC
                """
            ).fetchall()
        records = []
        for row in rows:
            record = dict(row)
            record["average_rgb"] = tuple(
                int(float(value)) for value in record["average_rgb"].split(",")
            )
            record["average_lab"] = tuple(
                float(value) for value in record["average_lab"].split(",")
            )
            records.append(record)
        return records
