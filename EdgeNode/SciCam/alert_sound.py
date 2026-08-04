from __future__ import annotations

import threading
import winsound


class ContinuousAlertSound:
    """Play a repeating Windows alarm tone without blocking the GUI."""

    def __init__(
        self,
        frequency: int = 1400,
        duration_ms: int = 350,
        gap_seconds: float = 0.15,
    ) -> None:
        self.frequency = frequency
        self.duration_ms = duration_ms
        self.gap_seconds = gap_seconds
        self._stop = threading.Event()
        self._thread = None

    @property
    def is_active(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def start(self) -> None:
        if self.is_active:
            return
        self._stop.clear()
        self._thread = threading.Thread(
            target=self._play_loop,
            name="ppe-alert-sound",
            daemon=True,
        )
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        thread = self._thread
        if thread is not None and thread is not threading.current_thread():
            thread.join(timeout=0.75)
        self._thread = None

    def _play_loop(self) -> None:
        while not self._stop.is_set():
            try:
                winsound.Beep(self.frequency, self.duration_ms)
            except RuntimeError:
                winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
            self._stop.wait(self.gap_seconds)
