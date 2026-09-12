from __future__ import annotations

import time

import cv2
import numpy as np

from .analyzers.brightness_analyzer import BrightnessAnalyzer
from .analyzers.histogram_generator import HistogramGenerator
from .analyzers.lab_analyzer import LABAnalyzer
from .analyzers.rgb_analyzer import RGBAnalyzer
from .brown_detector import BrownDetector
from .colour_adjustment import ColourAdjustmentProcessor
from .analysis_metrics import AnalysisMetrics
from .moving_average import MovingAverage
from .pipeline import ProcessingPipeline
from .processing_result import ProcessingResult
from .reference_colour_correction import dominant_colour_fill
from .sample_roi import CircularSampleROI


class FrameProcessor:
    """Run the image-processing and analysis pipeline for one frame."""

    def __init__(
        self,
        averaging_window: int = 20,
        diagnostics_enabled: bool = False,
    ) -> None:
        self.pipeline = ProcessingPipeline()
        # Do not apply gray-world white balance to the captured frame. Tea
        # commonly fills most of the ROI with one genuine dominant colour;
        # forcing the channel averages to gray would remove that colour.
        self.colour_adjustment = ColourAdjustmentProcessor()
        self.pipeline.add(self.colour_adjustment)

        self.brown_detector = BrownDetector()
        self.rgb_analyzer = RGBAnalyzer()
        self.lab_analyzer = LABAnalyzer()
        self.brightness_analyzer = BrightnessAnalyzer()
        self.histogram_generator = HistogramGenerator()
        self.sample_roi = CircularSampleROI()
        self.brown_average = MovingAverage(averaging_window)
        self.analysis_metrics = AnalysisMetrics()
        self.diagnostics_enabled = diagnostics_enabled
        self._smoothed_image = None
        self._smoothing_alpha = 0.35
        self.pipeline_options = {
            "colour_adjustment": False,
            "image_smoothing": False,
            "sample_roi_mask": False,
            "dominant_colour_fill": False,
        }

    def set_pipeline_options(self, options: dict) -> None:
        self.pipeline_options = {
            name: bool(options.get(name, False))
            for name in self.pipeline_options
        }
        self._reset_image_smoothing()

    def set_averaging_window(self, window_size: int) -> None:
        self.brown_average.set_window_size(window_size)

    def reset_average(self) -> None:
        self.brown_average.reset()
        self._smoothed_image = None

    def _reset_image_smoothing(self) -> None:
        self._smoothed_image = None

    def set_exposure(self, value: int) -> None:
        self.colour_adjustment.set_exposure(value)
        self._reset_image_smoothing()

    def set_gain(self, value: int) -> None:
        self.colour_adjustment.set_gain(value)
        self._reset_image_smoothing()

    def set_brightness(self, value: int) -> None:
        self.colour_adjustment.set_brightness(value)
        self._reset_image_smoothing()

    def set_contrast(self, value: int) -> None:
        self.colour_adjustment.set_contrast(value)
        self._reset_image_smoothing()

    def set_saturation(self, value: int) -> None:
        self.colour_adjustment.set_saturation(value)
        self._reset_image_smoothing()

    def set_gamma(self, value: int) -> None:
        self.colour_adjustment.set_gamma(value)
        self._reset_image_smoothing()

    def set_temperature(self, value: int) -> None:
        self.colour_adjustment.set_temperature(value)
        self._reset_image_smoothing()

    def set_tint(self, value: int) -> None:
        self.colour_adjustment.set_tint(value)
        self._reset_image_smoothing()

    def process(self, frame: np.ndarray) -> ProcessingResult:
        start = time.perf_counter()

        adjusted = (
            self.pipeline.process(frame)
            if self.pipeline_options["colour_adjustment"]
            else frame.copy()
        )
        if self.pipeline_options["image_smoothing"] and (
            self._smoothed_image is None
            or self._smoothed_image.shape != adjusted.shape
        ):
            white_balance = adjusted
        elif self.pipeline_options["image_smoothing"]:
            white_balance = cv2.addWeighted(
                adjusted,
                self._smoothing_alpha,
                self._smoothed_image,
                1.0 - self._smoothing_alpha,
                0.0,
            )
        else:
            white_balance = adjusted
        self._smoothed_image = white_balance.copy()
        roi_mask = self.sample_roi.create_mask(white_balance)
        display_image = white_balance
        if self.pipeline_options["sample_roi_mask"]:
            display_image = cv2.bitwise_and(
                white_balance,
                white_balance,
                mask=roi_mask,
            )
        if self.pipeline_options["dominant_colour_fill"]:
            display_image, _colour = dominant_colour_fill(
                display_image,
                roi_mask if self.pipeline_options["sample_roi_mask"] else None,
            )
        brown = self.brown_detector.process(white_balance, roi_mask)
        stable_brown_percentage = self.brown_average.add(
            brown.percentage
        )
        samples = self.brown_average.sample_count
        window = self.brown_average.window_size
        is_stable = samples >= window
        average_rgb = self.rgb_analyzer.process(white_balance, roi_mask)
        average_lab = self.lab_analyzer.process(white_balance, roi_mask)
        brightness = self.brightness_analyzer.process(
            white_balance,
            roi_mask,
        )
        histogram_image = None
        brown_mask = None
        if self.diagnostics_enabled:
            histogram_image = self.histogram_generator.process(
                white_balance,
                roi_mask,
            )
            brown_mask = cv2.cvtColor(brown.mask, cv2.COLOR_GRAY2BGR)

        processing_ms = (time.perf_counter() - start) * 1000

        return ProcessingResult(
            original=frame,
            white_balance=display_image,
            brown_mask=brown_mask,
            histogram_image=histogram_image,
            brown_percentage=stable_brown_percentage,
            average_rgb=average_rgb,
            average_lab=average_lab,
            brightness=brightness,
            status=(
                "PROCESSING"
                if is_stable
                else f"STABILIZING {samples}/{window}"
            ),
            fermentation_status=(
                self.analysis_metrics.classify_fermentation(
                    stable_brown_percentage
                )
                if is_stable
                else "Stabilizing"
            ),
            tea_quality="",
            confidence=min(100.0, (samples / window) * 100.0),
            processing_ms=processing_ms,
        )
