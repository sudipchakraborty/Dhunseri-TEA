from __future__ import annotations

import cv2

from .camera_device import CameraDevice


class CameraManager:
    """
    Discovers connected cameras.
    """

    def __init__(self) -> None:
        self._devices: list[CameraDevice] = []

    def discover(self, max_devices: int = 10) -> list[CameraDevice]:
        """
        Scan available camera indices.
        """

        self._devices.clear()

        for index in range(max_devices):

            cap = cv2.VideoCapture(index)

            if not cap.isOpened():
                cap.release()
                continue

            success, _ = cap.read()

            if success:
                self._devices.append(
                    CameraDevice(
                        index=index,
                        name=f"Camera {index}",
                    )
                )

            cap.release()

        return self._devices

    @property
    def devices(self) -> list[CameraDevice]:
        return self._devices