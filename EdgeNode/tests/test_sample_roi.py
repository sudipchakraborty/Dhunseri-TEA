import cv2
import numpy as np

from SciCam.processing.sample_roi import CircularSampleROI


def test_default_roi_aligns_with_fixed_tray_geometry():
    frame = np.zeros((218, 290, 3), dtype=np.uint8)

    mask = CircularSampleROI().create_mask(frame)

    moments = cv2.moments(mask, binaryImage=True)
    center_x = round(moments["m10"] / moments["m00"])
    center_y = round(moments["m01"] / moments["m00"])
    expected_radius = round(218 * 0.23)

    assert (center_x, center_y) == (145, 124)
    assert mask[124, 145] == 255
    assert mask[124, 145 + expected_radius] == 255
    assert mask[124, 145 + expected_radius + 1] == 0


def test_display_crop_makes_sample_fill_the_view():
    frame = np.zeros((218, 290, 3), dtype=np.uint8)

    crop = CircularSampleROI().crop_around_sample(frame)

    # 50 px ROI radius with 15% display padding on each side.
    assert crop.shape[:2] == (117, 117)
