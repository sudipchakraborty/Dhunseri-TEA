class FrameProcessor:

    @staticmethod
    def process(image):
        """Return the OpenCV image after applying frame processing.

        This is currently a pass-through hook. Future processing operations can
        be added here while preserving the NumPy image expected by cv2.imshow.
        """
        return image
