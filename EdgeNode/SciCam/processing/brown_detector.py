from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path

import cv2
import numpy as np

from SciCam.app_paths import application_root


DEFAULT_CALIBRATION_PATH = (
    application_root()
    / "config"
    / "brown_calibration.json"
)


@dataclass
class BrownDetectionResult:
    mask: np.ndarray
    percentage: float
    confidence: float


class BrownCalibration:
    """Convert measured tea colour strength into calibrated brown percent."""

    def __init__(self, path: Path = DEFAULT_CALIBRATION_PATH) -> None:
        self.path = Path(path)
        self.reference_light = BrownDetector.LIGHT_TEA_RGB.copy()
        self.reference_brown = BrownDetector.FULL_BROWN_RGB.copy()
        self.gamma = BrownDetector.STRENGTH_GAMMA
        self.samples: list[dict] = []
        self.coefficients: list[float] | None = None
        self.model_type = "polynomial"
        self.points: list[tuple[float, float]] = []
        self.feature_min = 0.0
        self.feature_max = 100.0
        self.load()

    def load(self) -> None:
        if not self.path.exists():
            return
        with self.path.open("r", encoding="utf-8") as file:
            data = json.load(file)
        references = data.get("references", {})
        if "light_tea_rgb" in references:
            self.reference_light = np.array(
                references["light_tea_rgb"],
                dtype=np.float32,
            )
        if "full_brown_rgb" in references:
            self.reference_brown = np.array(
                references["full_brown_rgb"],
                dtype=np.float32,
            )
        self.gamma = float(data.get("strength_gamma", self.gamma))
        self.samples = list(data.get("samples", []))
        model = data.get("model", {})
        self.model_type = str(model.get("type", "polynomial"))
        coefficients = model.get("coefficients")
        if coefficients:
            self.coefficients = [float(value) for value in coefficients]
        points = model.get("points")
        if points:
            self.points = sorted(
                (
                    (float(point["feature"]), float(point["brown_percentage"]))
                    for point in points
                ),
                key=lambda point: point[0],
            )
        feature_range = model.get("feature_range")
        if feature_range and len(feature_range) == 2:
            self.feature_min = float(feature_range[0])
            self.feature_max = float(feature_range[1])

    def strength_percentage(
        self,
        frame: np.ndarray,
        roi_mask: np.ndarray | None = None,
    ) -> float:
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mean_rgb = np.array(
            cv2.mean(rgb, mask=roi_mask)[:3],
            dtype=np.float32,
        )
        brown_vector = self.reference_brown - self.reference_light
        denominator = float(np.dot(brown_vector, brown_vector))
        if denominator == 0.0:
            return 0.0
        strength = (
            np.dot(mean_rgb - self.reference_light, brown_vector)
            / denominator
        )
        strength = float(np.clip(strength, 0.0, 1.0))
        return (strength ** self.gamma) * 100.0

    def apply(self, feature: float) -> float:
        if self.model_type == "piecewise_linear" and self.points:
            features = [point[0] for point in self.points]
            labels = [point[1] for point in self.points]
            value = float(np.interp(feature, features, labels))
            return float(np.clip(value, 0.0, 100.0))
        if not self.coefficients:
            return float(np.clip(feature, 0.0, 100.0))
        value = float(np.polyval(self.coefficients, feature))
        return float(np.clip(value, 0.0, 100.0))

    def confidence(self, feature: float, area_percentage: float) -> float:
        confidence = 100.0
        if self.samples and self.feature_max > self.feature_min:
            if feature < self.feature_min:
                distance = self.feature_min - feature
            elif feature > self.feature_max:
                distance = feature - self.feature_max
            else:
                distance = 0.0
            span = self.feature_max - self.feature_min
            confidence -= min(45.0, (distance / span) * 100.0)
        elif not self.samples:
            confidence -= 25.0

        if area_percentage < 1.0 and feature > 5.0:
            confidence -= 20.0
        return float(np.clip(confidence, 0.0, 100.0))


class BrownDetector:
    """
    Estimate brown content from the selected ROI.

    The mask remains HSV-based for visualization, but the displayed
    percentage is a colour-strength estimate. The 0-to-100 validation images
    are uniform colour samples rather than mixed brown/non-brown areas, so a
    pure pixel-area threshold collapses most of them to 100%.
    """

    LIGHT_TEA_RGB = np.array([239.5, 235.5, 232.0], dtype=np.float32)
    FULL_BROWN_RGB = np.array([52.2, 31.7, 18.7], dtype=np.float32)
    STRENGTH_GAMMA = 1.15

    def __init__(
        self,
        calibration: BrownCalibration | None = None,
    ) -> None:
        self.calibration = calibration or BrownCalibration()

    def process(
        self,
        frame: np.ndarray,
        roi_mask: np.ndarray | None = None,
    ) -> BrownDetectionResult:

        hsv = cv2.cvtColor(
            frame,
            cv2.COLOR_BGR2HSV,
        )

        lower = np.array(
            [5, 40, 30],
            dtype=np.uint8,
        )

        upper = np.array(
            [30, 255, 255],
            dtype=np.uint8,
        )

        mask = cv2.inRange(
            hsv,
            lower,
            upper,
        )

        kernel = np.ones(
            (5, 5),
            np.uint8,
        )

        mask = cv2.morphologyEx(
            mask,
            cv2.MORPH_OPEN,
            kernel,
        )

        mask = cv2.morphologyEx(
            mask,
            cv2.MORPH_CLOSE,
            kernel,
        )

        if roi_mask is not None:
            mask = cv2.bitwise_and(mask, roi_mask)

        brown_pixels = cv2.countNonZero(mask)

        total_pixels = (
            cv2.countNonZero(roi_mask)
            if roi_mask is not None
            else mask.shape[0] * mask.shape[1]
        )

        area_percentage = (
            (brown_pixels / total_pixels) * 100.0
            if total_pixels
            else 0.0
        )
        raw_strength = self.calibration.strength_percentage(frame, roi_mask)
        percentage = self.calibration.apply(raw_strength)
        if percentage < 0.5 and area_percentage > 0.0:
            percentage = area_percentage
        confidence = self.calibration.confidence(
            raw_strength,
            area_percentage,
        )

        return BrownDetectionResult(
            mask=mask,
            percentage=percentage,
            confidence=confidence,
        )
