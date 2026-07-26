from dataclasses import dataclass


@dataclass(slots=True)
class CameraDevice:
    """
    Physical camera information.
    """

    index: int
    name: str

    width: int = 0
    height: int = 0
    fps: float = 0.0