from __future__ import annotations

import cv2
import numpy as np

from ..image_processor import ImageProcessor


class ColourAdjustmentProcessor(ImageProcessor):
    """Backend-independent, neutral-at-50 image colour controls."""

    def __init__(self) -> None:
        self.exposure = 50
        self.gain = 50
        self.brightness = 50
        self.contrast = 50
        self.saturation = 50
        self.gamma = 50
        self.temperature = 50
        self.tint = 50

    @staticmethod
    def _value(value: int | float) -> float:
        return max(0.0, min(100.0, float(value)))

    def set_exposure(self, value: int) -> None:
        self.exposure = self._value(value)

    def set_gain(self, value: int) -> None:
        self.gain = self._value(value)

    def set_brightness(self, value: int) -> None:
        self.brightness = self._value(value)

    def set_contrast(self, value: int) -> None:
        self.contrast = self._value(value)

    def set_saturation(self, value: int) -> None:
        self.saturation = self._value(value)

    def set_gamma(self, value: int) -> None:
        self.gamma = self._value(value)

    def set_temperature(self, value: int) -> None:
        self.temperature = self._value(value)

    def set_tint(self, value: int) -> None:
        self.tint = self._value(value)

    def process(self, frame: np.ndarray) -> np.ndarray:
        image = frame.astype(np.float32) / 255.0

        # Exposure is expressed as +/- 2 stops; gain is a gentler multiplier.
        exposure_scale = 2.0 ** ((self.exposure - 50) / 25.0)
        gain_scale = 2.0 ** ((self.gain - 50) / 50.0)
        image *= exposure_scale * gain_scale

        # Independent colour balance. Positive temperature adds red and
        # reduces blue; positive tint adds magenta and reduces green.
        temperature = (self.temperature - 50) / 50.0
        tint = (self.tint - 50) / 50.0
        image[:, :, 2] *= 2.0 ** temperature
        image[:, :, 0] *= 2.0 ** -temperature
        image[:, :, 1] *= 2.0 ** -tint
        image[:, :, 2] *= 2.0 ** (tint * 0.5)
        image[:, :, 0] *= 2.0 ** (tint * 0.5)

        contrast_scale = 2.0 ** ((self.contrast - 50) / 50.0)
        image = (image - 0.5) * contrast_scale + 0.5
        image += (self.brightness - 50) / 100.0
        image = np.clip(image, 0.0, 1.0)

        # Gamma affects midtones without changing black and white endpoints.
        gamma_value = 2.0 ** ((50 - self.gamma) / 50.0)
        image = np.power(image, gamma_value)

        image_u8 = np.round(image * 255.0).astype(np.uint8)
        hsv = cv2.cvtColor(image_u8, cv2.COLOR_BGR2HSV).astype(np.float32)
        hsv[:, :, 1] *= self.saturation / 50.0
        hsv[:, :, 1] = np.clip(hsv[:, :, 1], 0, 255)

        return cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)
