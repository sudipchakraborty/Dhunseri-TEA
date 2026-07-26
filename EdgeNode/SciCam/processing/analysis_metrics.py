from __future__ import annotations

import json
from pathlib import Path

from SciCam.app_paths import application_root

DEFAULT_CONFIG_PATH = (
    application_root()
    / "config"
    / "analysis_metrics.json"
)


class AnalysisMetrics:
    """Load, validate, save, and apply brown-content classifications."""

    def __init__(self, path: Path = DEFAULT_CONFIG_PATH) -> None:
        self.path = Path(path)
        self.data = {}
        self.load()

    def load(self) -> None:
        with self.path.open("r", encoding="utf-8") as file:
            data = json.load(file)
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
        quality = data["tea_quality"]

        fermentation_limits = [
            float(fermentation["under_fermented_max"]),
            float(fermentation["perfect_max"]),
        ]
        quality_limits = [
            float(quality["poor_max"]),
            float(quality["moderate_max"]),
            float(quality["good_max"]),
        ]

        if not (
            0 <= fermentation_limits[0]
            < fermentation_limits[1]
            <= 100
        ):
            raise ValueError(
                "Fermentation limits must increase between 0 and 100."
            )

        if not (
            0 <= quality_limits[0]
            < quality_limits[1]
            < quality_limits[2]
            <= 100
        ):
            raise ValueError(
                "Tea-quality limits must increase between 0 and 100."
            )

    def classify_fermentation(self, brown: float) -> str:
        limits = self.data["fermentation"]
        if brown <= limits["under_fermented_max"]:
            return "Under Fermented"
        if brown <= limits["perfect_max"]:
            return "Perfect"
        return "Over Fermented"

    def classify_quality(self, brown: float) -> str:
        limits = self.data["tea_quality"]
        if brown <= limits["poor_max"]:
            return "Poor Quality"
        if brown <= limits["moderate_max"]:
            return "Moderate Quality"
        if brown <= limits["good_max"]:
            return "Good"
        return "Premium"
