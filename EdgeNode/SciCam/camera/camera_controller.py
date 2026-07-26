import cv2


class CameraController:
    """
    Controls all camera properties.

    This class is the only place where
    OpenCV camera settings are changed.
    """

    def __init__(self):

        self.capture = None

    # --------------------------------------------

    def set_capture(self, capture):

        self.capture = capture

    # --------------------------------------------

    def set_exposure(self, value):

        if self.capture is None:
            return

        self.capture.set(
            cv2.CAP_PROP_EXPOSURE,
            value,
        )

    # --------------------------------------------

    def set_gain(self, value):

        if self.capture is None:
            return

        self.capture.set(
            cv2.CAP_PROP_GAIN,
            value,
        )

    # --------------------------------------------

    def set_brightness(self, value):

        if self.capture is None:
            return

        self.capture.set(
            cv2.CAP_PROP_BRIGHTNESS,
            value,
        )

    # --------------------------------------------

    def set_contrast(self, value):

        if self.capture is None:
            return

        self.capture.set(
            cv2.CAP_PROP_CONTRAST,
            value,
        )

    # --------------------------------------------

    def set_saturation(self, value):

        if self.capture is None:
            return

        self.capture.set(
            cv2.CAP_PROP_SATURATION,
            value,
        )

    # --------------------------------------------

    def set_gamma(self, value):

        if self.capture is None:
            return

        self.capture.set(
            cv2.CAP_PROP_GAMMA,
            value,
        )

    # --------------------------------------------

    def set_auto_exposure(self, enabled):

        if self.capture is None:
            return

        if enabled:

            self.capture.set(
                cv2.CAP_PROP_AUTO_EXPOSURE,
                1,
            )

        else:

            self.capture.set(
                cv2.CAP_PROP_AUTO_EXPOSURE,
                0,
            )

    # --------------------------------------------

    def set_auto_focus(self, enabled):

        if self.capture is None:
            return

        self.capture.set(
            cv2.CAP_PROP_AUTOFOCUS,
            int(enabled),
        )

    # --------------------------------------------

    def set_auto_white_balance(self, enabled):

        if self.capture is None:
            return

        self.capture.set(
            cv2.CAP_PROP_AUTO_WB,
            int(enabled),
        )