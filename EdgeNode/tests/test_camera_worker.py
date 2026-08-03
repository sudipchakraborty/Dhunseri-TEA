import cv2
import numpy as np


def test_rgb_rtsp_pixel_converts_to_expected_bgr_colour():
    yellow_rgb = np.array([[[245, 210, 40]]], dtype=np.uint8)

    converted = cv2.cvtColor(yellow_rgb, cv2.COLOR_RGB2BGR)

    assert tuple(converted[0, 0]) == (40, 210, 245)
