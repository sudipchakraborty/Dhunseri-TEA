from __future__ import annotations

import threading

from PySide6.QtCore import QObject, Signal

from .ppe_detector import PPEDetector


class PPEDetectionService(QObject):
    """Run PPE inference off the GUI thread and retain only the latest frame."""

    result_ready = Signal(object)
    error = Signal(str)
    ready = Signal()

    def __init__(self) -> None:
        super().__init__()
        self._lock = threading.Lock()
        self._wake = threading.Event()
        self._stop = threading.Event()
        self._latest_frame = None
        self._thread = None

    def start(self) -> None:
        if self._thread is not None and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(
            target=self._run,
            name="ppe-detection",
            daemon=True,
        )
        self._thread.start()

    def submit(self, frame) -> None:
        with self._lock:
            self._latest_frame = frame
        self._wake.set()

    def stop(self) -> None:
        self._stop.set()
        self._wake.set()
        if self._thread is not None:
            self._thread.join(timeout=2.0)

    def _take_latest(self):
        with self._lock:
            frame = self._latest_frame
            self._latest_frame = None
        return frame

    def _run(self) -> None:
        try:
            detector = PPEDetector()
            self.ready.emit()
            while not self._stop.is_set():
                self._wake.wait(0.1)
                self._wake.clear()
                frame = self._take_latest()
                if frame is None or self._stop.is_set():
                    continue
                self.result_ready.emit(detector.process(frame))
        except Exception as error:
            self.error.emit(str(error))
