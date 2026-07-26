from __future__ import annotations

import time

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
        return self._capture.isOpened()

    def read(self):
        if self._capture is None or not self._capture.isOpened():
            return False, None

        return self._capture.read()

    def reconnect(self, should_continue) -> bool:
        """Retry opening until connected or the worker is stopped."""
        self.release()

        deadline = time.monotonic() + self.reconnect_delay
        while should_continue() and time.monotonic() < deadline:
            time.sleep(0.05)

        return should_continue() and self.open()

    def release(self) -> None:
        if self._capture is not None:
            self._capture.release()
            self._capture = None
