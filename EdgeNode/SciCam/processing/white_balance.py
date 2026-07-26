import cv2
import numpy as np

from ..image_processor import ImageProcessor


class WhiteBalanceProcessor(ImageProcessor):
    """
    Gray World White Balance
    """

    def process(self, frame: np.ndarray) -> np.ndarray:

        result = frame.astype(np.float32)

        b, g, r = cv2.split(result)

        avg_b = np.mean(b)
        avg_g = np.mean(g)
        avg_r = np.mean(r)

        avg = (avg_b + avg_g + avg_r) / 3

        if avg_b > 0:
            b *= avg / avg_b
        if avg_g > 0:
            g *= avg / avg_g
        if avg_r > 0:
            r *= avg / avg_r

        balanced = cv2.merge([b, g, r])

        balanced = np.clip(
            balanced,
            0,
            255,
        )

        return balanced.astype(np.uint8)
