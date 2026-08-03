import numpy as np

from SciCam.processing.frame_processor import FrameProcessor


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
