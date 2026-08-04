from __future__ import annotations

import time
from threading import Condition, Event, Thread

import cv2


class RTSPCamera:
    """OpenCV-based RTSP reader with a small reconnect delay."""

    def __init__(
        self,
        url: str,
        reconnect_delay: float = 1.0,
    ):
        self.url = url
        self.reconnect_delay = reconnect_delay
        self._capture = None
        self._reader_thread = None
        self._stop_reader = Event()
        self._frame_available = Condition()
        self._latest_frame = None
        self._frame_sequence = 0
        self._delivered_sequence = 0
        self._reader_failed = False

    def open(self) -> bool:
        self.release()

        # FFmpeg is normally the most reliable OpenCV backend for RTSP.
        self._capture = cv2.VideoCapture(
            self.url,
            cv2.CAP_FFMPEG,
            [
                cv2.CAP_PROP_OPEN_TIMEOUT_MSEC,
                3000,
                cv2.CAP_PROP_READ_TIMEOUT_MSEC,
                2000,
            ],
        )

        # Keep latency low when the backend supports this property.
        self._capture.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        if not self._capture.isOpened():
            return False

        # Decode continuously on a dedicated thread. Image processing can be
        # slower than the camera frame rate; retaining only this latest frame
        # prevents FFmpeg's queue from turning into seconds of stale video.
        self._stop_reader.clear()
        with self._frame_available:
            self._latest_frame = None
            self._frame_sequence = 0
            self._delivered_sequence = 0
            self._reader_failed = False
        self._reader_thread = Thread(
            target=self._drain_stream,
            name="RTSP-latest-frame-reader",
            daemon=True,
        )
        self._reader_thread.start()
        return True

    def _drain_stream(self) -> None:
        while not self._stop_reader.is_set():
            try:
                ok, frame = self._capture.read()
            except cv2.error:
                ok, frame = False, None
            if not ok:
                with self._frame_available:
                    self._reader_failed = True
                    self._frame_available.notify_all()
                return
            with self._frame_available:
                self._latest_frame = frame
                self._frame_sequence += 1
                self._frame_available.notify_all()

    def read(self):
        if self._capture is None or not self._capture.isOpened():
            return False, None
        deadline = time.monotonic() + 2.0
        with self._frame_available:
            while (
                self._frame_sequence == self._delivered_sequence
                and not self._reader_failed
                and not self._stop_reader.is_set()
            ):
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    return False, None
                self._frame_available.wait(remaining)

            if self._frame_sequence == self._delivered_sequence:
                return False, None
            self._delivered_sequence = self._frame_sequence
            return True, self._latest_frame.copy()

    def reconnect(self, should_continue) -> bool:
        """Retry opening until connected or the worker is stopped."""
        self.release()

        deadline = time.monotonic() + self.reconnect_delay
        while should_continue() and time.monotonic() < deadline:
            time.sleep(0.05)

        return should_continue() and self.open()

    def release(self) -> None:
        self._stop_reader.set()
        with self._frame_available:
            self._frame_available.notify_all()
        reader = self._reader_thread
        if reader is not None and reader.is_alive():
            reader.join(timeout=2.1)
        if self._capture is not None:
            self._capture.release()
            self._capture = None
        if reader is not None and reader.is_alive():
            reader.join(timeout=0.5)
        self._reader_thread = None
        with self._frame_available:
            self._latest_frame = None
