import numpy as np

from SciCam.processing.white_balance import WhiteBalanceProcessor


def test_white_balance_preserves_gray_image():
    frame = np.full((20, 20, 3), 120, dtype=np.uint8)

    balanced = WhiteBalanceProcessor().process(frame)

    assert np.array_equal(balanced, frame)


def test_white_balance_reduces_channel_bias():
    frame = np.full((20, 20, 3), (60, 120, 180), dtype=np.uint8)

    balanced = WhiteBalanceProcessor().process(frame)
    means = balanced.reshape(-1, 3).mean(axis=0)

    assert means.max() - means.min() <= 1.0
