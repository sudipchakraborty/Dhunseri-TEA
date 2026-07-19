import cv2
import os
from datetime import datetime

class CameraHelper:
    """
    Camera Helper Class
    Contains all camera-related operations.
    """

    @staticmethod
    def open_camera(camera):
        """
        Open the camera.
        """
        camera.cap = cv2.VideoCapture(0)

        if not camera.cap.isOpened():
            raise RuntimeError(
                f"Unable to open camera {camera.camera_index}"
            )

        camera.is_open = True

        print("===================================")
        print(" Camera Opened Successfully")
        print("===================================")

    @staticmethod
    def set_resolution(camera):

        camera.cap.set(cv2.CAP_PROP_FRAME_WIDTH, camera.width)
        camera.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, camera.height)

        print(f"Resolution Set : {camera.width} x {camera.height}")

    @staticmethod
    def set_fps(camera):
        camera.cap.set(cv2.CAP_PROP_FPS, camera.fps)
        print(f"FPS Set : {camera.fps}")

    @staticmethod
    def print_camera_info(camera):

        width = int(camera.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(camera.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = camera.cap.get(cv2.CAP_PROP_FPS)

        print("--------------------------------")
        print("Camera Information")
        print("--------------------------------")
        print(f"Width  : {width}")
        print(f"Height : {height}")
        print(f"FPS    : {fps}")
        print("--------------------------------")

    @staticmethod
    def read_frame(camera):
        """
        Read one frame.
        """
        if not camera.is_open:
            return False, None

        return camera.cap.read()

    @staticmethod
    def show_frame(window_name, frame):
        """
        Display frame.
        """
        cv2.imshow(window_name, frame)

    @staticmethod
    def wait_key(delay=1):
        """
        Wait for keyboard input.
        """
        return cv2.waitKey(delay) & 0xFF

    @staticmethod
    def release_camera(camera):
        """
        Release camera resources.
        """
        if camera.cap is not None:
            camera.cap.release()

        cv2.destroyAllWindows()

        camera.is_open = False

        print("===================================")
        print(" Camera Released")
        print("===================================")
    
    @staticmethod
    def capture_image(frame):
        """
        Save current frame as PNG with timestamp.
        """

        save_dir = "data/captured"

        os.makedirs(save_dir, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        filename = f"tea_{timestamp}.png"

        filepath = os.path.join(save_dir, filename)

        cv2.imwrite(filepath, frame)

        print(f"Image Saved : {filepath}")

    @staticmethod
    def set_brightness(camera):

        camera.cap.set(
            cv2.CAP_PROP_BRIGHTNESS,
            camera.brightness
        )

        print(f"Brightness : {camera.brightness}")
    
    @staticmethod
    def set_contrast(camera):

        camera.cap.set(
            cv2.CAP_PROP_CONTRAST,
            camera.contrast
        )

        print(f"Contrast : {camera.contrast}")

    @staticmethod
    def set_saturation(camera):

        camera.cap.set(
            cv2.CAP_PROP_SATURATION,
            camera.saturation
        )

        print(f"Saturation : {camera.saturation}")


    @staticmethod
    def set_gamma(camera):

        camera.cap.set(
            cv2.CAP_PROP_GAMMA,
            camera.gamma
        )

        print(f"Gamma : {camera.gamma}")

    @staticmethod
    def set_gain(camera):

        camera.cap.set(
            cv2.CAP_PROP_GAIN,
            camera.gain
        )

        print(f"Gain : {camera.gain}")

    @staticmethod
    def set_exposure(camera):

        camera.cap.set(
            cv2.CAP_PROP_EXPOSURE,
            camera.exposure
        )

        print(f"Exposure : {camera.exposure}")


    @staticmethod
    def print_camera_properties(camera):
        """
        Print all available camera properties.
        """

        properties = {
            "Frame Width": cv2.CAP_PROP_FRAME_WIDTH,
            "Frame Height": cv2.CAP_PROP_FRAME_HEIGHT,
            "FPS": cv2.CAP_PROP_FPS,
            "Brightness": cv2.CAP_PROP_BRIGHTNESS,
            "Contrast": cv2.CAP_PROP_CONTRAST,
            "Saturation": cv2.CAP_PROP_SATURATION,
            "Hue": cv2.CAP_PROP_HUE,
            "Gain": cv2.CAP_PROP_GAIN,
            "Exposure": cv2.CAP_PROP_EXPOSURE,
            "Gamma": cv2.CAP_PROP_GAMMA,
            "Sharpness": cv2.CAP_PROP_SHARPNESS,
            "Focus": cv2.CAP_PROP_FOCUS,
            "Zoom": cv2.CAP_PROP_ZOOM,
            "Temperature": cv2.CAP_PROP_TEMPERATURE,
            "White Balance Blue U": cv2.CAP_PROP_WHITE_BALANCE_BLUE_U,
            "Backlight": cv2.CAP_PROP_BACKLIGHT,
            "Auto Exposure": cv2.CAP_PROP_AUTO_EXPOSURE,
            "Auto Focus": cv2.CAP_PROP_AUTOFOCUS,
            "Buffer Size": cv2.CAP_PROP_BUFFERSIZE
        }

        print("\n========== CAMERA PROPERTIES ==========\n")

        for name, prop in properties.items():
            value = camera.cap.get(prop)
            print(f"{name:<25}: {value}")

        print("\n=======================================\n")