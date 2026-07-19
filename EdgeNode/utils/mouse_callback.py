import cv2

from SciCam.color_inspector import ColorInspector


class MouseCallback:

    current_image = None

    @staticmethod
    def callback(event, x, y, flags, param):

        if event == cv2.EVENT_LBUTTONDOWN:

            ColorInspector.inspect(
                MouseCallback.current_image,
                x,
                y
            )
