from __future__ import annotations

import ipaddress
import json
from pathlib import Path

from .app_paths import application_root


DEFAULT_CAMERA_CONFIG = application_root() / "config" / "camera.json"


class CameraSettings:
    """Persistent RTSP camera address configuration."""

    def __init__(self, path: Path = DEFAULT_CAMERA_CONFIG) -> None:
        self.path = Path(path)
        self.rtsp_ip = "192.168.0.201"
        self.load()

    @property
    def rtsp_url(self) -> str:
        return f"rtsp://admin:DPDYWJ@{self.rtsp_ip}:554/Streaming/Channels/101"

    @staticmethod
    def validate_ip(value: str) -> str:
        address = ipaddress.ip_address(value.strip())
        if address.version != 4:
            raise ValueError("Please enter an IPv4 address.")
        return str(address)

    def load(self) -> None:
        if not self.path.exists():
            self.save(self.rtsp_ip)
            return
        with self.path.open("r", encoding="utf-8") as file:
            data = json.load(file)
        self.rtsp_ip = self.validate_ip(data["rtsp_ip"])

    def save(self, value: str) -> None:
        self.rtsp_ip = self.validate_ip(value)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("w", encoding="utf-8") as file:
            json.dump({"rtsp_ip": self.rtsp_ip}, file, indent=2)
            file.write("\n")
