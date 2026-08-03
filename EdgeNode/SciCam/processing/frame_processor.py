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

    def set_averaging_window(self, window_size: int) -> None:
        self.brown_average.set_window_size(window_size)

    def reset_average(self) -> None:
        self.brown_average.reset()

    def set_exposure(self, value: int) -> None:
        self.colour_adjustment.set_exposure(value)

    def set_gain(self, value: int) -> None:
        self.colour_adjustment.set_gain(value)

    def set_brightness(self, value: int) -> None:
        self.colour_adjustment.set_brightness(value)

    def set_contrast(self, value: int) -> None:
        self.colour_adjustment.set_contrast(value)

    def set_saturation(self, value: int) -> None:
        self.colour_adjustment.set_saturation(value)

    def set_gamma(self, value: int) -> None:
        self.colour_adjustment.set_gamma(value)

    def set_temperature(self, value: int) -> None:
        self.colour_adjustment.set_temperature(value)

    def set_tint(self, value: int) -> None:
        self.colour_adjustment.set_tint(value)

    def process(self, frame: np.ndarray) -> ProcessingResult:
        start = time.perf_counter()

        white_balance = self.pipeline.process(frame)
        roi_mask = self.sample_roi.create_mask(white_balance)
        masked_white_balance = cv2.bitwise_and(
            white_balance,
            white_balance,
            mask=roi_mask,
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
            white_balance=masked_white_balance,
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
