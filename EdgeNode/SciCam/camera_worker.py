from __future__ import annotations

import time
from queue import Empty, SimpleQueue

import cv2

from PySide6.QtCore import QObject, Signal, Slot

from .rtsp_camera import RTSPCamera


class CameraWorker(QObject):
    """
    Captures frames in a background thread and manages
    camera properties safely.
    """

    frame_ready = Signal(object)
    result_ready = Signal(object)
    paused_result_ready = Signal(object)
    processing_error = Signal(str)
    finished = Signal()

    def __init__(self):
        super().__init__()

        self._running = False
        self._camera_source = 0
        self._capture = None
        self._rtsp_camera = None
        self._frame_interval = 0.1
        self._property_requests = SimpleQueue()
        self._frame_processor = None
        self._reading_enabled = True
        self._last_processed_frame = None
        self._reprocess_requested = False

    # -------------------------------------------------

    def set_camera(self, source):
        """Select a USB camera index or an RTSP URL."""
        self._camera_source = source

    def set_frame_processor(self, processor):
        self._frame_processor = processor

    def set_reading_enabled(self, enabled: bool):
        # A bool assignment is atomic in CPython. The capture loop continues
        # while paused so camera controls remain available and RTSP stays live.
        self._reading_enabled = bool(enabled)

    def request_frozen_frame_reprocess(self):
        """Apply new parameters to the last displayed frame while paused."""
        if not self._reading_enabled:
            self._reprocess_requested = True

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

                while True:
                    try:
                        prop, value = self._property_requests.get_nowait()
                    except Empty:
                        break
                    if self._capture is not None:
                        self._capture.set(prop, value)

                if (
                    not self._reading_enabled
                    and self._reprocess_requested
                    and self._last_processed_frame is not None
                    and self._frame_processor is not None
                ):
                    self._reprocess_requested = False
                    try:
                        paused_result = self._frame_processor.process(
                            self._last_processed_frame
                        )
                    except Exception as error:
                        self.processing_error.emit(str(error))
                    else:
                        self.paused_result_ready.emit(paused_result)

                if self._rtsp_camera is not None:
                    ok, frame = self._rtsp_camera.read()
                    if ok:
                        # The PiCam RTSP feed used by this application arrives
                        # with RGB channel order, whereas all downstream OpenCV
                        # processing expects BGR. Without this swap, yellow is
                        # displayed as cyan because red and blue are reversed.
                        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
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
                if (
                    self._reading_enabled
                    and now - last_emitted >= self._frame_interval
                ):
                    self._last_processed_frame = frame.copy()
                    if self._frame_processor is None:
                        self.frame_ready.emit(frame)
                    else:
                        try:
                            result = self._frame_processor.process(frame)
                        except Exception as error:
                            self.processing_error.emit(str(error))
                        else:
                            self.result_ready.emit(result)
                    last_emitted = now

        finally:

            self._running = False
            self._last_processed_frame = None
            self._reprocess_requested = False

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
        # UI requests can arrive from another thread. Apply them inside the
        # capture loop, where VideoCapture is owned.
        self._property_requests.put((prop, value))

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
