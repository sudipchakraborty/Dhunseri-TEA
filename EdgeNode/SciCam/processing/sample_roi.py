from __future__ import annotations

import cv2
import numpy as np


class CircularSampleROI:
    """Build a stable circular mask for a fixed, round sample tray."""

    def __init__(
        self,
        center_x: float = 0.5,
        center_y: float = 0.57,
        radius: float = 0.23,
    ) -> None:
        """
        Values are fractions of the frame dimensions. ``radius`` is a
        fraction of the shorter frame side. These defaults align with the
        fixed inspection tray: its centre is slightly below frame centre and
        the radius stays inside the white rim.
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

    def crop_around_sample(
        self,
        frame: np.ndarray,
        padding: float = 1.15,
    ) -> np.ndarray:
        """Return a display crop centred on the circular sample ROI."""
        height, width = frame.shape[:2]
        center_x = round(width * self.center_x)
        center_y = round(height * self.center_y)
        radius = round(min(width, height) * self.radius * padding)
        left = max(0, center_x - radius)
        right = min(width, center_x + radius + 1)
        top = max(0, center_y - radius)
        bottom = min(height, center_y + radius + 1)
        return frame[top:bottom, left:right]
