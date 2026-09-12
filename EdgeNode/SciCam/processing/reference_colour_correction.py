from __future__ import annotations

import cv2
import numpy as np
from scipy.optimize import differential_evolution, least_squares

from .colour_adjustment import ColourAdjustmentProcessor


CORRECTED_CONTROLS = (
    "exposure",
    "gain",
    "brightness",
    "contrast",
    "saturation",
    "gamma",
    "temperature",
    "tint",
)


def dominant_colour_fill(image, mask=None, bin_size=16):
    """Fill an image with its most common quantized BGR colour."""
    if image is None or image.ndim != 3 or image.shape[2] != 3:
        raise ValueError("A BGR colour image is required.")
    if not 1 <= bin_size <= 256:
        raise ValueError("bin_size must be between 1 and 256.")

    pixels = image[mask > 0] if mask is not None else image.reshape(-1, 3)
    if not len(pixels):
        raise ValueError("The image has no usable colour pixels.")

    quantized = pixels.astype(np.uint32) // bin_size
    bins_per_channel = (256 + bin_size - 1) // bin_size
    keys = (
        quantized[:, 0] * bins_per_channel * bins_per_channel
        + quantized[:, 1] * bins_per_channel
        + quantized[:, 2]
    )
    winning_key = np.bincount(keys).argmax()
    dominant_pixels = pixels[keys == winning_key]
    colour = np.median(dominant_pixels, axis=0).astype(np.uint8)
    return np.full_like(image, colour), tuple(int(value) for value in colour)


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

    @staticmethod
    def _bgr_mean(pixels):
        return pixels.reshape(-1, 3).astype(np.float64).mean(axis=0)

    def correct(self, source, source_mask, reference, current):
        source_pixels = self._sample_pixels(source, source_mask)
        reference_pixels = self._sample_pixels(reference)
        target_lab = self._lab_mean(reference_pixels)
        target_bgr = self._bgr_mean(reference_pixels)
        initial = np.array(
            [current[name] for name in CORRECTED_CONTROLS],
            dtype=np.float64,
        )

        processor = ColourAdjustmentProcessor()

        def apply(values):
            for name, value in zip(CORRECTED_CONTROLS, values):
                getattr(processor, f"set_{name}")(value)
            return processor.process(source_pixels)

        def residual(values):
            adjusted = apply(values)
            lab_difference = (
                self._lab_mean(adjusted) - target_lab
            ) / np.array([22.0, 14.0, 14.0])
            bgr_difference = (
                self._bgr_mean(adjusted) - target_bgr
            ) / np.array([32.0, 32.0, 32.0])
            # Prefer the smallest practical movement when alternatives produce
            # similar colour, keeping the controls understandable.
            regularization = (values - initial) / 1500.0
            return np.concatenate(
                (lab_difference, bgr_difference, regularization)
            )

        before_error = float(
            np.linalg.norm(self._lab_mean(apply(initial)) - target_lab)
        )
        starts = [
            initial,
            np.full(len(initial), 50.0),
            np.array([35, 55, 25, 25, 80, 95, 80, 35], dtype=np.float64),
            np.array([45, 60, 35, 35, 95, 80, 90, 25], dtype=np.float64),
            np.array([25, 50, 20, 20, 100, 100, 100, 0], dtype=np.float64),
        ]
        fits = [
            least_squares(
                residual,
                start,
                bounds=(
                    np.zeros(len(initial)),
                    np.full(len(initial), 100.0),
                ),
                max_nfev=260,
                diff_step=0.02,
                xtol=1e-4,
                ftol=1e-4,
                gtol=1e-4,
            )
            for start in starts
        ]

        def colour_error(values):
            adjusted = apply(values)
            lab_error = np.linalg.norm(self._lab_mean(adjusted) - target_lab)
            bgr_error = np.linalg.norm(self._bgr_mean(adjusted) - target_bgr)
            return bgr_error + (lab_error * 0.45)

        global_fit = differential_evolution(
            colour_error,
            [(0.0, 100.0)] * len(initial),
            maxiter=70,
            popsize=10,
            polish=True,
            seed=7,
            tol=0.01,
            workers=1,
        )
        candidates = [fit.x for fit in fits]
        candidates.append(global_fit.x)
        best_values = min(candidates, key=colour_error)
        fitted = np.clip(np.rint(best_values), 0, 100).astype(int)
        after_error = float(
            np.linalg.norm(self._lab_mean(apply(fitted)) - target_lab)
        )
        return (
            dict(zip(CORRECTED_CONTROLS, fitted.tolist())),
            before_error,
            after_error,
        )
