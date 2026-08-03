from __future__ import annotations

import json
from pathlib import Path

from SciCam.app_paths import application_root

DEFAULT_CONFIG_PATH = (
    application_root()
    / "config"
    / "analysis_metrics.json"
)

DEFAULT_FERMENTATION = {
    "under_poor": {"from": 0.0, "to": 81.0},
    "under_moderate": {"from": 82.0, "to": 84.0},
    "good": {"from": 85.0, "to": 87.0},
    "over_moderate": {"from": 88.0, "to": 90.0},
    "over_poor": {"from": 91.0, "to": 100.0},
}

FERMENTATION_LABELS = {
    "under_poor": "Under Fermented (Poor)",
    "under_moderate": "Under Fermented (Moderate)",
    "good": "Good Fermentation",
    "over_moderate": "Over Fermented (Moderate)",
    "over_poor": "Over Fermented (Poor)",
}


class AnalysisMetrics:
    """Load, validate, save, and apply brown-content classifications."""

    def __init__(self, path: Path = DEFAULT_CONFIG_PATH) -> None:
        self.path = Path(path)
        self.data = {}
        self.load()

    def load(self) -> None:
        with self.path.open("r", encoding="utf-8") as file:
            data = json.load(file)
        fermentation = data.get("fermentation", {})
        uses_shared_boundaries = (
            "under_poor" in fermentation
            and fermentation["under_poor"].get("to")
            == fermentation.get("under_moderate", {}).get("from")
        )
        if "under_poor" not in fermentation or uses_shared_boundaries:
            data = {"fermentation": dict(DEFAULT_FERMENTATION)}
            self.save(data)
            return
        self.validate(data)
        self.data = data

    def save(self, data: dict) -> None:
        self.validate(data)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("w", encoding="utf-8") as file:
            json.dump(data, file, indent=2)
            file.write("\n")
        self.data = data

    @staticmethod
    def validate(data: dict) -> None:
        fermentation = data["fermentation"]
        keys = list(FERMENTATION_LABELS)
        ranges = []
        for key in keys:
            range_data = fermentation[key]
            start = float(range_data["from"])
            end = float(range_data["to"])
            if not 0 <= start < end <= 100:
                raise ValueError(
                    f"{FERMENTATION_LABELS[key]} must have From below To."
                )
            ranges.append((start, end))

        if ranges[0][0] != 0 or ranges[-1][1] != 100:
            raise ValueError(
                "Fermentation ranges must cover from 0 to 100."
            )
        for previous, current in zip(ranges, ranges[1:]):
            if previous[1] + 1 != current[0]:
                raise ValueError(
                    "Each From value must follow the previous To value."
                )

    def classify_fermentation(self, brown: float) -> str:
        value = int(max(0.0, min(100.0, float(brown))) + 0.5)
        fermentation = self.data["fermentation"]
        for key in FERMENTATION_LABELS:
            range_data = fermentation[key]
            start = float(range_data["from"])
            end = float(range_data["to"])
            if start <= value <= end:
                return FERMENTATION_LABELS[key]
        raise ValueError("Reading is outside the configured ranges.")
