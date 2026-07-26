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
    Detect brown regions using HSV thresholds.

    Version 1:
    - Simple HSV threshold
    - Morphological cleanup
    """

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

        percentage = (
            (brown_pixels / total_pixels) * 100.0
            if total_pixels
            else 0.0
        )

        return BrownDetectionResult(
            mask=mask,
            percentage=percentage,
        )
