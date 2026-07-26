from __future__ import annotations

from collections import deque


class MovingAverage:
    """Fixed-size rolling average for stabilizing measurements."""

    def __init__(self, window_size: int = 20) -> None:
        self._values = deque(maxlen=self._validate(window_size))

    @staticmethod
    def _validate(window_size: int) -> int:
        window_size = int(window_size)
        if window_size < 1:
            raise ValueError("window_size must be at least 1")
        return window_size

    @property
    def window_size(self) -> int:
        return self._values.maxlen

    @property
    def sample_count(self) -> int:
        return len(self._values)

    def set_window_size(self, window_size: int) -> None:
        window_size = self._validate(window_size)
        if window_size != self.window_size:
            self._values = deque(maxlen=window_size)

    def add(self, value: float) -> float:
        self._values.append(float(value))
        return sum(self._values) / len(self._values)

    def reset(self) -> None:
        self._values.clear()

