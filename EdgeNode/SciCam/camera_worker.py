from __future__ import annotations

import time

import cv2

from PySide6.QtCore import QObject, Signal, Slot

from .rtsp_camera import RTSPCamera


class CameraWorker(QObject):
    """
    Captures frames in a background thread and manages
    camera properties safely.
    """

    frame_ready = Signal(object)
    finished = Signal()

    def __init__(self):
        super().__init__()

        self._running = False
        self._camera_source = 0
        self._capture = None
        self._rtsp_camera = None
        self._frame_interval = 0.1

    # -------------------------------------------------

    def set_camera(self, source):
        """Select a USB camera index or an RTSP URL."""
        self._camera_source = source

    # -------------------------------------------------

    @Slot()
    def run(self):

        self._running = True

        if isinstance(self._camera_source, str):
            self._rtsp_camera = RTSPCamera(self._camera_source)
            if not self._rtsp_camera.open():
                self._rtsp_camera.release()
                self._rtsp_camera = None
                self._running = False
                self.finished.emit()
                return
        else:
            self._capture = cv2.VideoCapture(self._camera_source)

        if (
            self._rtsp_camera is None
            and not self._capture.isOpened()
        ):
            self._capture.release()
            self._capture = None
            self._running = False
            self.finished.emit()
            return

        try:
            last_emitted = 0.0

            while self._running:

                if self._rtsp_camera is not None:
                    ok, frame = self._rtsp_camera.read()
                else:
                    ok, frame = self._capture.read()

                if not ok:
                    if (
                        self._rtsp_camera is not None
                        and self._rtsp_camera.reconnect(
                            lambda: self._running
                        )
                    ):
                        continue
                    break

                now = time.monotonic()
                if now - last_emitted >= self._frame_interval:
                    self.frame_ready.emit(frame)
                    last_emitted = now

        finally:

            self._running = False

            if self._capture is not None:
                self._capture.release()
                self._capture = None

            if self._rtsp_camera is not None:
                self._rtsp_camera.release()
                self._rtsp_camera = None

            self.finished.emit()

    # -------------------------------------------------

    def stop(self):

        # Only set the flag here. This method is invoked by the GUI thread;
        # calling OpenCV release() from it can block against read() and freeze
        # the application. The worker owns and releases capture in run().
        self._running = False

    # -------------------------------------------------
    # Camera Properties
    # -------------------------------------------------

    def _set_property(self, prop, value):

        if self._capture is not None:
            self._capture.set(prop, value)

    def set_exposure(self, value):
        self._set_property(cv2.CAP_PROP_EXPOSURE, value)

    def set_gain(self, value):
        self._set_property(cv2.CAP_PROP_GAIN, value)

    def set_brightness(self, value):
        self._set_property(cv2.CAP_PROP_BRIGHTNESS, value)

    def set_contrast(self, value):
        self._set_property(cv2.CAP_PROP_CONTRAST, value)

    def set_saturation(self, value):
        self._set_property(cv2.CAP_PROP_SATURATION, value)

    def set_gamma(self, value):
        self._set_property(cv2.CAP_PROP_GAMMA, value)

    def set_auto_focus(self, enabled):
        self._set_property(cv2.CAP_PROP_AUTOFOCUS, int(enabled))

    def set_auto_white_balance(self, enabled):
        self._set_property(cv2.CAP_PROP_AUTO_WB, int(enabled))

    def set_auto_exposure(self, enabled):
        """
        OpenCV backend values differ across platforms.
        This mapping works for many DirectShow/MSMF cameras,
        but some drivers may require different values.
        """
        value = 1 if enabled else 0
        self._set_property(cv2.CAP_PROP_AUTO_EXPOSURE, value)
