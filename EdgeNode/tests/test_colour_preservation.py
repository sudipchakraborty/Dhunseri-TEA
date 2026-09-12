import numpy as np

from SciCam.processing.frame_processor import FrameProcessor
from SciCam.processing.reference_colour_correction import (
    ReferenceColourCorrector,
)


def test_frame_processor_preserves_dominant_object_colour():
    """A yellow object must not be neutralized to white or gray."""
    yellow_bgr = (40, 210, 245)
    frame = np.full((100, 100, 3), yellow_bgr, dtype=np.uint8)

    result = FrameProcessor(averaging_window=1).process(frame)

    assert tuple(result.white_balance[50, 50]) == yellow_bgr
    assert result.average_rgb == (245, 210, 40)


def test_saturation_slider_changes_colour_strength():
    frame = np.full((100, 100, 3), (40, 210, 245), dtype=np.uint8)
    processor = FrameProcessor(averaging_window=1)

    processor.set_saturation(0)
    gray = processor.process(frame).white_balance[50, 50]
    processor.set_saturation(100)
    vivid = processor.process(frame).white_balance[50, 50]

    assert int(gray.max()) - int(gray.min()) == 0
    assert int(vivid.max()) - int(vivid.min()) > 150


def test_brightness_slider_changes_light_level():
    frame = np.full((100, 100, 3), 100, dtype=np.uint8)
    processor = FrameProcessor(averaging_window=1)

    processor.set_brightness(25)
    darker = processor.process(frame).white_balance[50, 50, 0]
    processor.set_brightness(75)
    lighter = processor.process(frame).white_balance[50, 50, 0]

    assert darker < 100 < lighter


def test_temperature_slider_warms_a_cool_image():
    frame = np.full((100, 100, 3), (180, 150, 110), dtype=np.uint8)
    processor = FrameProcessor(averaging_window=1)

    processor.set_temperature(100)
    warmed = processor.process(frame).white_balance[50, 50]

    assert warmed[2] > 110
    assert warmed[0] < 180


def test_adjusted_image_smooths_single_frame_variation():
    processor = FrameProcessor(averaging_window=1)
    dark = np.full((100, 100, 3), 80, dtype=np.uint8)
    bright = np.full((100, 100, 3), 120, dtype=np.uint8)

    processor.process(dark)
    smoothed = processor.process(bright).white_balance[50, 50, 0]

    assert 80 < smoothed < 120


def test_reference_correction_adds_channel_gains_for_close_colour_match():
    source = np.full((100, 100, 3), (90, 104, 200), dtype=np.uint8)
    reference = np.full((100, 100, 3), (0, 82, 154), dtype=np.uint8)
    current = {
        "exposure": 37,
        "gain": 53,
        "brightness": 47,
        "contrast": 22,
        "saturation": 76,
        "gamma": 99,
        "temperature": 99,
        "tint": 70,
    }

    values, gains, before_error, after_error = (
        ReferenceColourCorrector().correct(source, None, reference, current)
    )
    processor = FrameProcessor(averaging_window=1)
    for name, value in values.items():
        getattr(processor, f"set_{name}")(value)
    processor.set_gain(current["gain"])
    processor.set_contrast(current["contrast"])
    processor.set_reference_colour_gains(gains)

    corrected = processor.process(source).white_balance[50, 50]

    assert after_error < before_error
    assert np.linalg.norm(corrected.astype(float) - reference[50, 50]) < 4.0
