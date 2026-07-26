import cv2
import numpy as np


class HistogramGenerator:
    """
    Generates a displayable histogram image.

    Output:
        512 x 300 BGR image
    """

    WIDTH = 512
    HEIGHT = 300

    def process(self, frame, mask=None):

        hist_img = np.full(
            (
                self.HEIGHT,
                self.WIDTH,
                3,
            ),
            255,
            dtype=np.uint8,
        )

        channels = (
            (0, (255, 0, 0)),   # Blue
            (1, (0, 255, 0)),   # Green
            (2, (0, 0, 255)),   # Red
        )

        for channel, color in channels:

            hist = cv2.calcHist(
                [frame],
                [channel],
                mask,
                [256],
                [0, 256],
            )

            cv2.normalize(
                hist,
                hist,
                0,
                self.HEIGHT - 20,
                cv2.NORM_MINMAX,
            )

            for i in range(255):

                cv2.line(
                    hist_img,
                    (
                        i * 2,
                        self.HEIGHT - 1 - int(hist.flat[i]),
                    ),
                    (
                        (i + 1) * 2,
                        self.HEIGHT - 1 - int(hist.flat[i + 1]),
                    ),
                    color,
                    2,
                )

        cv2.rectangle(
            hist_img,
            (0, 0),
            (
                self.WIDTH - 1,
                self.HEIGHT - 1,
            ),
            (80, 80, 80),
            1,
        )

        return hist_img
