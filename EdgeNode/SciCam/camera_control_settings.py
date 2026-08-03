from __future__ import annotations

import json
from pathlib import Path

from .app_paths import application_root


DEFAULT_CONTROL_CONFIG = (
    application_root() / "config" / "camera_controls.json"
)

DEFAULT_VALUES = {
    "exposure": 50,
    "gain": 50,
    "brightness": 50,
    "contrast": 50,
    "saturation": 50,
    "gamma": 50,
    "temperature": 50,
    "tint": 50,
    "averaging_window": 20,
    "auto_exposure": False,
    "auto_white_balance": False,
    "auto_focus": False,
}


class CameraControlSettings:
    """Load and save persistent camera calibration controls."""

    def __init__(self, path: Path = DEFAULT_CONTROL_CONFIG) -> None:
        self.path = Path(path)
        self.values = DEFAULT_VALUES.copy()
        self.load()

    @staticmethod
    def _validated(data: dict) -> dict:
        values = DEFAULT_VALUES.copy()
        for name in (
            "exposure", "gain", "brightness", "contrast", "saturation",
            "gamma", "temperature", "tint",
        ):
            if name in data:
                values[name] = max(0, min(100, int(data[name])))
        if "averaging_window" in data:
            values["averaging_window"] = max(
                1, min(100, int(data["averaging_window"]))
            )
        for name in (
            "auto_exposure", "auto_white_balance", "auto_focus",
        ):
            if name in data:
                values[name] = bool(data[name])
        return values

    def load(self) -> dict:
        if self.path.exists():
            try:
                with self.path.open("r", encoding="utf-8") as file:
                    self.values = self._validated(json.load(file))
            except (OSError, TypeError, ValueError, json.JSONDecodeError):
                self.values = DEFAULT_VALUES.copy()
        return self.values.copy()

    def save(self, values: dict) -> None:
        self.values = self._validated(values)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary_path = self.path.with_suffix(self.path.suffix + ".tmp")
        with temporary_path.open("w", encoding="utf-8") as file:
            json.dump(self.values, file, indent=2)
            file.write("\n")
        temporary_path.replace(self.path)
