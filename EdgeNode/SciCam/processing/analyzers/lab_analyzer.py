import cv2


class LABAnalyzer:

    def process(self, frame, mask=None):

        lab = cv2.cvtColor(
            frame,
            cv2.COLOR_BGR2LAB,
        )

        l, a, b, _ = cv2.mean(lab, mask=mask)

        return (float(l), float(a), float(b))
