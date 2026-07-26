from __future__ import annotations

import numpy as np


class ImageProcessor:
    """
    Base image processing class.
    """

    def process(self, frame: np.ndarray) -> np.ndarray:
        return frame