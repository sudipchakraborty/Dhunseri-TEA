from __future__ import annotations

import numpy as np


class ProcessingPipeline:
    """Execute image processors sequentially."""

    def __init__(self) -> None:
        self._processors = []

    def add(self, processor) -> None:
        self._processors.append(processor)

    def clear(self) -> None:
        self._processors.clear()

    def process(self, frame: np.ndarray) -> np.ndarray:
        result = frame

        for processor in self._processors:
            result = processor.process(result)

        return result
