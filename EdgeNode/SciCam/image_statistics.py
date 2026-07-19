import cv2
import numpy as np


class ImageStatistics:

    @staticmethod
    def calculate(image):

        blue, green, red = cv2.split(image)

        statistics = {

            "mean_red": np.mean(red),

            "mean_green": np.mean(green),

            "mean_blue": np.mean(blue),

            "brightness": np.mean(
                cv2.cvtColor(
                    image,
                    cv2.COLOR_BGR2GRAY
                )
            ),

            "std_dev": np.std(image),

            "minimum": np.min(image),

            "maximum": np.max(image)

        }

        return statistics
