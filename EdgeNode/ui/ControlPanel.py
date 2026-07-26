from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QGroupBox,
    QPushButton,
    QSlider,
    QVBoxLayout,
)

from ui.base_panel import BasePanel


class ControlPanel(BasePanel):
    """
    Camera control panel.

    This class is responsible only for the UI.
    It does NOT communicate with OpenCV.
    """

    # -------------------------------------------------
    # Signals
    # -------------------------------------------------

    connect_requested = Signal(int)
    disconnect_requested = Signal()

    def __init__(self) -> None:
        super().__init__("Camera Settings")

        self._build_ui()

    def _build_ui(self) -> None:

        # -------------------------------------------------
        # Camera Selection
        # -------------------------------------------------

        camera_group = QGroupBox("Camera")

        camera_layout = QVBoxLayout(camera_group)

        self.camera_combo = QComboBox()
        self.camera_combo.addItem("Camera 0", 0)

        camera_layout.addWidget(self.camera_combo)

        # -------------------------------------------------
        # Camera Parameters
        # -------------------------------------------------

        parameter_group = QGroupBox("Parameters")

        parameter_layout = QFormLayout(parameter_group)

        self.exposure = self._create_slider()
        self.gain = self._create_slider()
        self.brightness = self._create_slider()
        self.contrast = self._create_slider()
        self.saturation = self._create_slider()
        self.gamma = self._create_slider()

        parameter_layout.addRow("Exposure", self.exposure)
        parameter_layout.addRow("Gain", self.gain)
        parameter_layout.addRow("Brightness", self.brightness)
        parameter_layout.addRow("Contrast", self.contrast)
        parameter_layout.addRow("Saturation", self.saturation)
        parameter_layout.addRow("Gamma", self.gamma)

        # -------------------------------------------------
        # Options
        # -------------------------------------------------

        option_group = QGroupBox("Options")

        option_layout = QVBoxLayout(option_group)

        self.auto_exposure = QCheckBox("Auto Exposure")
        self.auto_white_balance = QCheckBox("Auto White Balance")
        self.auto_focus = QCheckBox("Auto Focus")

        option_layout.addWidget(self.auto_exposure)
        option_layout.addWidget(self.auto_white_balance)
        option_layout.addWidget(self.auto_focus)

        # -------------------------------------------------
        # Buttons
        # -------------------------------------------------

        self.connect_button = QPushButton("Connect")
        self.disconnect_button = QPushButton("Disconnect")

        self.connect_button.clicked.connect(
            self._on_connect_clicked
        )

        self.disconnect_button.clicked.connect(
            self._on_disconnect_clicked
        )

        # -------------------------------------------------
        # Layout
        # -------------------------------------------------

        self.content_layout.addWidget(camera_group)
        self.content_layout.addWidget(parameter_group)
        self.content_layout.addWidget(option_group)

        self.content_layout.addWidget(self.connect_button)
        self.content_layout.addWidget(self.disconnect_button)

        self.content_layout.addStretch()

    # -------------------------------------------------
    # Private Methods
    # -------------------------------------------------

    def _create_slider(self) -> QSlider:

        slider = QSlider(Qt.Horizontal)

        slider.setRange(0, 100)
        slider.setValue(50)

        return slider

    def _on_connect_clicked(self) -> None:

        camera_index = self.camera_combo.currentData()

        if camera_index is None:
            camera_index = self.camera_combo.currentIndex()

        self.connect_requested.emit(camera_index)

    def _on_disconnect_clicked(self) -> None:

        self.disconnect_requested.emit()

    # -------------------------------------------------
    # Public API
    # -------------------------------------------------

    def set_camera_list(self, cameras) -> None:
        """
        Populate available cameras.
        """

        self.camera_combo.clear()

        for camera in cameras:
            self.camera_combo.addItem(
                camera.name,
                camera.index,
            )