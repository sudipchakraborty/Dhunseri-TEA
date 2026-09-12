from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np


@dataclass
class BrownDetectionResult:
    mask: np.ndarray
    percentage: float


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
        percentage = self._brown_strength_percentage(frame, roi_mask)
        if percentage < 0.5 and area_percentage > 0.0:
            percentage = area_percentage

        return BrownDetectionResult(
            mask=mask,
            percentage=percentage,
        )

    def _brown_strength_percentage(
        self,
        frame: np.ndarray,
        roi_mask: np.ndarray | None = None,
    ) -> float:
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mean_rgb = np.array(
            cv2.mean(rgb, mask=roi_mask)[:3],
            dtype=np.float32,
        )
        brown_vector = self.FULL_BROWN_RGB - self.LIGHT_TEA_RGB
        denominator = float(np.dot(brown_vector, brown_vector))
        if denominator == 0.0:
            return 0.0
        strength = (
            np.dot(mean_rgb - self.LIGHT_TEA_RGB, brown_vector)
            / denominator
        )
        strength = float(np.clip(strength, 0.0, 1.0))
        calibrated = strength ** self.STRENGTH_GAMMA
        return calibrated * 100.0
