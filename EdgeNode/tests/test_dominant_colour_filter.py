import numpy as np

from SciCam.processing.reference_colour_correction import dominant_colour_fill


def test_dominant_colour_fill_groups_camera_noise_and_fills_image():
    image = np.array(
        [
            [[101, 151, 201], [104, 154, 204], [30, 50, 70]],
            [[103, 153, 203], [220, 10, 10], [102, 152, 202]],
        ],
        dtype=np.uint8,
    )
    filled, colour = dominant_colour_fill(image, bin_size=16)
    assert colour == (102, 152, 202)
    assert np.all(filled == np.array(colour, dtype=np.uint8))


def test_dominant_colour_fill_uses_only_masked_pixels():
    image = np.full((4, 4, 3), (0, 0, 0), dtype=np.uint8)
    image[1:3, 1:3] = (80, 120, 160)
    mask = np.zeros((4, 4), dtype=np.uint8)
    mask[1:3, 1:3] = 255
    filled, colour = dominant_colour_fill(image, mask)
    assert colour == (80, 120, 160)
    assert np.all(filled == np.array(colour, dtype=np.uint8))
