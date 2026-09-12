from threading import Event
from unittest.mock import patch
import os

import cv2
import numpy as np

from SciCam.rtsp_camera import RTSPCamera


class FakeCapture:
    def __init__(self, *args, **kwargs):
        self.released = Event()
        self.third_frame_read = Event()
        self.index = 0

    def isOpened(self):
        return not self.released.is_set()

    def set(self, prop, value):
        return True

    def read(self):
        self.index += 1
        if self.index <= 3:
            frame = np.full((2, 2, 3), self.index, dtype=np.uint8)
            if self.index == 3:
                self.third_frame_read.set()
            return True, frame
        self.released.wait(0.2)
        return False, None

    def release(self):
        self.released.set()


def test_rtsp_reader_returns_latest_frame_instead_of_queued_frames():
    fake = FakeCapture()
    with patch.object(cv2, "VideoCapture", return_value=fake):
        camera = RTSPCamera("rtsp://camera/stream")
        assert camera.open()
        assert fake.third_frame_read.wait(1.0)

        ok, frame = camera.read()
        camera.release()

    assert ok
    assert np.all(frame == 3)


def test_rtsp_reader_forces_tcp_transport():
    fake = FakeCapture()
    with patch.object(cv2, "VideoCapture", return_value=fake):
        camera = RTSPCamera("rtsp://camera/stream")
        assert camera.open()
        camera.release()

    assert os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] == "rtsp_transport;tcp"
