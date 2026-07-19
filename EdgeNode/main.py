import cv2

from SciCam.camera import Camera
from SciCam.camera_helper import CameraHelper

from SciCam.frame_processor import FrameProcessor
from SciCam.image_statistics import ImageStatistics
from SciCam.roi_manager import ROIManager
from utils.mouse_callback import MouseCallback

ROI_X = 250
ROI_Y = 150
ROI_WIDTH = 800
ROI_HEIGHT = 600

def main():

    camera = Camera()

    CameraHelper.open_camera(camera)

    CameraHelper.set_resolution(camera)

    CameraHelper.set_brightness(camera)
    CameraHelper.set_contrast(camera)
    CameraHelper.set_saturation(camera)
    CameraHelper.set_gamma(camera)
    CameraHelper.set_gain(camera)
    CameraHelper.set_exposure(camera)

    CameraHelper.set_fps(camera)

    CameraHelper.print_camera_info(camera)
    CameraHelper.print_camera_properties(camera)

    # -----------------------------------
    # Live Camera Loop
    # -----------------------------------

    while True:

        ret, frame = CameraHelper.read_frame(camera)

        if not ret:
            print("Frame Capture Failed")
            break

        roi = ROIManager.get_roi(frame, ROI_X, ROI_Y, ROI_WIDTH, ROI_HEIGHT)
        ROIManager.draw_roi(frame, ROI_X, ROI_Y, ROI_WIDTH, ROI_HEIGHT)

        frame_data = FrameProcessor.process(frame)
        statistics = ImageStatistics.calculate(frame_data)
        print(statistics)

        CameraHelper.show_frame(
            "TeaVision",
            frame_data
        )

        CameraHelper.show_frame("Tea Camera",frame)
        CameraHelper.show_frame("Tea ROI",roi)

        MouseCallback.current_image = roi

        cv2.setMouseCallback(
            "Tea ROI",
            MouseCallback.callback
        )


        key = CameraHelper.wait_key()

        if key == ord("s"):
            CameraHelper.capture_image(frame)

        elif key == ord("q"):
            break

    # -----------------------------------
    # Cleanup
    # -----------------------------------

    CameraHelper.release_camera(camera)


if __name__ == "__main__":
    main()
