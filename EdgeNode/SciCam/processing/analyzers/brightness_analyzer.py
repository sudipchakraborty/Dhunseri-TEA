import cv2


class BrightnessAnalyzer:

    def process(self, frame, mask=None):

        gray = cv2.cvtColor(
            frame,
            cv2.COLOR_BGR2GRAY,
        )

        return float(cv2.mean(gray, mask=mask)[0])
