import cv2


class ROIManager:

    @staticmethod
    def get_roi(frame,
                x,
                y,
                width,
                height):
        """
        Crop Region of Interest.
        """

        roi = frame[
            y:y + height,
            x:x + width
        ]

        return roi

    @staticmethod
    def draw_roi(frame,
                 x,
                 y,
                 width,
                 height,
                 color=(0,255,0),
                 thickness=2):

        cv2.rectangle(
            frame,
            (x,y),
            (x+width,y+height),
            color,
            thickness
        )

        return frame