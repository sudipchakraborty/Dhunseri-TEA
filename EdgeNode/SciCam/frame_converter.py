import cv2

from PySide6.QtGui import (
    QImage,
)


class FrameConverter:

    @staticmethod
    def to_qimage(frame):

        rgb = cv2.cvtColor(
            frame,
            cv2.COLOR_BGR2RGB,
        )

        h, w, ch = rgb.shape

        bytes_per_line = ch * w

        return QImage(
            rgb.data,
            w,
            h,
            bytes_per_line,
            QImage.Format_RGB888,
        ).copy()