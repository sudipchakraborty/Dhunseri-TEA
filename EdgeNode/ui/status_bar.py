from PySide6.QtWidgets import QLabel, QStatusBar


class StatusBar(QStatusBar):
    """Application status bar."""

    def __init__(self) -> None:
        super().__init__()

        self.camera = QLabel("Camera : Disconnected")
        self.fps = QLabel("FPS : --")
        self.resolution = QLabel("Resolution : --")
        self.state = QLabel("Ready")

        self.addWidget(self.camera)
        self.addPermanentWidget(self.fps)
        self.addPermanentWidget(self.resolution)
        self.addPermanentWidget(self.state)

    def set_camera_connected(
        self,
        connected: bool,
        fps: int | None = None,
        resolution: str | None = None,
    ) -> None:
        self.camera.setText(
            "Camera : Connected" if connected else "Camera : Disconnected"
        )

        if fps is not None:
            self.fps.setText(f"FPS : {fps}")

        if resolution is not None:
            self.resolution.setText(f"Resolution : {resolution}")

    def set_state(self, text: str) -> None:
        self.state.setText(text)