from __future__ import annotations

import cv2
import numpy as np
from scipy.optimize import least_squares

from .colour_adjustment import ColourAdjustmentProcessor


CORRECTED_CONTROLS = (
    "exposure",
    "brightness",
    "saturation",
    "gamma",
    "temperature",
    "tint",
)


class ReferenceColourCorrector:
    """Fit software colour controls to a real-colour reference image."""

    @staticmethod
    def _sample_pixels(image, mask=None, maximum=8000):
        pixels = image[mask > 0] if mask is not None else image.reshape(-1, 3)
        # Ignore only near-black borders from masked/reference images.
        pixels = pixels[np.max(pixels, axis=1) >= 12]
        if not len(pixels):
            raise ValueError("The selected image has no usable colour pixels.")
        if len(pixels) > maximum:
            indices = np.linspace(0, len(pixels) - 1, maximum, dtype=int)
            pixels = pixels[indices]
        return pixels.reshape(-1, 1, 3).astype(np.uint8)

    @staticmethod
    def _lab_mean(pixels):
        lab = cv2.cvtColor(pixels, cv2.COLOR_BGR2LAB)
        return lab.reshape(-1, 3).mean(axis=0)

    def correct(self, source, source_mask, reference, current):
        source_pixels = self._sample_pixels(source, source_mask)
        reference_pixels = self._sample_pixels(reference)
        target_lab = self._lab_mean(reference_pixels)
        initial = np.array(
            [current[name] for name in CORRECTED_CONTROLS],
            dtype=np.float64,
        )

        processor = ColourAdjustmentProcessor()
        processor.set_gain(current["gain"])
        processor.set_contrast(current["contrast"])

        def apply(values):
            for name, value in zip(CORRECTED_CONTROLS, values):
                getattr(processor, f"set_{name}")(value)
            return processor.process(source_pixels)

        def residual(values):
            difference = (self._lab_mean(apply(values)) - target_lab) / np.array(
                [35.0, 22.0, 22.0]
            )
            # Prefer the smallest practical movement when alternatives produce
            # the same average colour, keeping the controls understandable.
            regularization = (values - initial) / 1000.0
            return np.concatenate((difference, regularization))

        before_error = float(
            np.linalg.norm(self._lab_mean(apply(initial)) - target_lab)
        )
        fit = least_squares(
            residual,
            initial,
            bounds=(np.zeros(len(initial)), np.full(len(initial), 100.0)),
            max_nfev=80,
            diff_step=0.05,
        )
        fitted = np.clip(np.rint(fit.x), 0, 100).astype(int)
        after_error = float(
            np.linalg.norm(self._lab_mean(apply(fitted)) - target_lab)
        )
        return (
            dict(zip(CORRECTED_CONTROLS, fitted.tolist())),
            before_error,
            after_error,
        )
