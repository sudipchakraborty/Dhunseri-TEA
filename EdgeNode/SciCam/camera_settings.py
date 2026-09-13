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
        self.rtsp_ip = "192.168.0.135"
        self.image_path = ""
        self.captured_image_path = ""
        self.load()

    @property
    def rtsp_url(self) -> str:
        return f"rtsp://{self.rtsp_ip}:8554/picam"

    @staticmethod
    def validate_ip(value: str) -> str:
        address = ipaddress.ip_address(value.strip())
        if address.version != 4:
            raise ValueError("Please enter an IPv4 address.")
        return str(address)

    def load(self) -> None:
        if not self.path.exists():
            self.save(self.rtsp_ip, self.image_path)
            return
        with self.path.open("r", encoding="utf-8") as file:
            data = json.load(file)
        self.rtsp_ip = self.validate_ip(data["rtsp_ip"])
        self.image_path = str(data.get("image_path", "")).strip()
        self.captured_image_path = str(
            data.get("captured_image_path", "")
        ).strip()

    def save(
        self,
        value: str | None = None,
        image_path: str | None = None,
        captured_image_path: str | None = None,
    ) -> None:
        if value is None:
            value = self.rtsp_ip
        self.rtsp_ip = self.validate_ip(value)
        if image_path is not None:
            self.image_path = str(image_path).strip()
        if captured_image_path is not None:
            self.captured_image_path = str(captured_image_path).strip()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("w", encoding="utf-8") as file:
            json.dump(
                {
                    "rtsp_ip": self.rtsp_ip,
                    "image_path": self.image_path,
                    "captured_image_path": self.captured_image_path,
                },
                file,
                indent=2,
            )
            file.write("\n")
