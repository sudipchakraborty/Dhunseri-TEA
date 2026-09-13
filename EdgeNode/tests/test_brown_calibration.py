import json
from pathlib import Path

import cv2
import numpy as np

from SciCam.processing.brown_detector import (
    BrownCalibration,
    BrownDetector,
)
from SciCam.processing.frame_processor import FrameProcessor


def test_identity_calibration_keeps_reference_scale(tmp_path):
    path = tmp_path / "brown_calibration.json"
    path.write_text(
        json.dumps(
            {
                "references": {
                    "light_tea_rgb": [239.5, 235.5, 232.0],
                    "full_brown_rgb": [52.2, 31.7, 18.7],
                },
                "strength_gamma": 1.15,
                "samples": [],
                "model": {
                    "coefficients": [1.0, 0.0],
                    "feature_range": [0.0, 100.0],
                },
            }
        ),
        encoding="utf-8",
    )
    calibration = BrownCalibration(path)
    detector = BrownDetector(calibration)
    light_bgr = np.full((80, 80, 3), (232, 236, 240), dtype=np.uint8)
    brown_bgr = np.full((80, 80, 3), (19, 32, 52), dtype=np.uint8)

    assert detector.process(light_bgr).percentage < 1.0
    assert detector.process(brown_bgr).percentage > 99.0


def test_fitted_calibration_maps_measured_feature_to_label(tmp_path):
    path = tmp_path / "brown_calibration.json"
    path.write_text(
        json.dumps(
            {
                "references": {
                    "light_tea_rgb": [239.5, 235.5, 232.0],
                    "full_brown_rgb": [52.2, 31.7, 18.7],
                },
                "strength_gamma": 1.15,
                "samples": [{"brown_percentage": 60.0, "feature": 59.45}],
                "model": {
                    "coefficients": [1.0, 0.55],
                    "feature_range": [0.0, 100.0],
                },
            }
        ),
        encoding="utf-8",
    )

    assert BrownCalibration(path).apply(59.45) == 60.0


def test_generated_sixty_percent_smoke_image_reads_near_label():
    image_path = Path(
        r"C:\Users\sudip\OneDrive\ESTPL\PROJECTS\DHUNSERI-TEA"
        r"\brown_percentage_test_images_0_to_100\60percent.jpg"
    )
    if not image_path.exists():
        return

    image = cv2.imread(str(image_path))
    result = FrameProcessor(averaging_window=1).process(image)

    assert 55.0 <= result.brown_percentage <= 65.0
    assert result.confidence >= 70.0
