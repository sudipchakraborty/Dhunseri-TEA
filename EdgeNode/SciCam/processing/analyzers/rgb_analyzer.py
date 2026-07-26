import cv2


class RGBAnalyzer:

    def process(self, frame, mask=None):

        rgb = cv2.cvtColor(
            frame,
            cv2.COLOR_BGR2RGB,
        )

        r, g, b, _ = cv2.mean(rgb, mask=mask)

        return (int(r), int(g), int(b))
