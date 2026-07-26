from __future__ import annotations

import cv2
import numpy as np


class CircularSampleROI:
    """Build a stable circular mask for a fixed, round sample tray."""

    def __init__(
        self,
        center_x: float = 0.5,
        center_y: float = 0.5,
        radius: float = 0.36,
    ) -> None:
        """
        Values are fractions of the frame dimensions. ``radius`` is a
        fraction of the shorter frame side and is intentionally smaller
        than the tray so its white rim is excluded.
        """
        self.center_x = center_x
        self.center_y = center_y
        self.radius = radius

    def create_mask(self, frame: np.ndarray) -> np.ndarray:
        height, width = frame.shape[:2]
        center = (
            round(width * self.center_x),
            round(height * self.center_y),
        )
        radius = round(min(width, height) * self.radius)

        mask = np.zeros((height, width), dtype=np.uint8)
        cv2.circle(mask, center, radius, 255, thickness=-1)
        return mask

