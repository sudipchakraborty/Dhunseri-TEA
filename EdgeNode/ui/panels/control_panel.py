from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QSlider,
    QVBoxLayout,
)
from urllib.parse import urlsplit

from ..base_panel import BasePanel
from email_module import EmailWidget


class ControlPanel(BasePanel):
    """
    Camera Control Panel

    UI Only.
    No OpenCV code belongs here.
    """

    # --------------------------------------------------
    # Camera
    # --------------------------------------------------

    connect_requested = Signal(object)
    disconnect_requested = Signal()
    close_requested = Signal()
    email_status_changed = Signal(str)
    rtsp_ip_save_requested = Signal(str)

    # --------------------------------------------------
    # Camera Parameters
    # --------------------------------------------------

    exposure_changed = Signal(int)
    gain_changed = Signal(int)
    brightness_changed = Signal(int)
    contrast_changed = Signal(int)
    saturation_changed = Signal(int)
    gamma_changed = Signal(int)

    auto_exposure_changed = Signal(bool)
    auto_white_balance_changed = Signal(bool)
    auto_focus_changed = Signal(bool)

    # --------------------------------------------------

    def __init__(
        self,
        rtsp_url="rtsp://admin:DPDYWJ@192.168.0.201:554/Streaming/Channels/101",
    ):

        super().__init__("AI Camera Settings")
        self._rtsp_url = rtsp_url

        self._build_ui()

        self._connect_signals()

    # --------------------------------------------------

    def _build_ui(self):

        # ---------------------------------------------
        # Camera
        # ---------------------------------------------

        camera_group = QGroupBox("Camera")

        camera_layout = QVBoxLayout(camera_group)

        self.camera_combo = QComboBox()

        self.camera_combo.addItem(
            "RTSP Camera",
            self._rtsp_url,
        )

        camera_layout.addWidget(self.camera_combo)

        rtsp_ip_layout = QHBoxLayout()
        self.rtsp_ip_edit = QLineEdit(urlsplit(self._rtsp_url).hostname or "")
        self.rtsp_ip_edit.setPlaceholderText("Camera IPv4 address")
        self.save_rtsp_ip_button = QPushButton("Save IP")
        rtsp_ip_layout.addWidget(self.rtsp_ip_edit, 1)
        rtsp_ip_layout.addWidget(self.save_rtsp_ip_button)
        camera_layout.addLayout(rtsp_ip_layout)

        # ---------------------------------------------
        # Parameters
        # ---------------------------------------------

        parameter_group = QGroupBox("Parameters")

        parameter_layout = QFormLayout(parameter_group)

        self.exposure = self._slider()
        self.gain = self._slider()
        self.brightness = self._slider()
        self.contrast = self._slider()
        self.saturation = self._slider()
        self.gamma = self._slider()

        parameter_layout.addRow("Exposure", self.exposure)
        parameter_layout.addRow("Gain", self.gain)
        parameter_layout.addRow("Brightness", self.brightness)
        parameter_layout.addRow("Contrast", self.contrast)
        parameter_layout.addRow("Saturation", self.saturation)
        parameter_layout.addRow("Gamma", self.gamma)

        # ---------------------------------------------
        # Options
        # ---------------------------------------------

        option_group = QGroupBox("Options")

        option_layout = QVBoxLayout(option_group)

        self.auto_exposure = QCheckBox("Auto Exposure")
        self.auto_white_balance = QCheckBox("Auto White Balance")
        self.auto_focus = QCheckBox("Auto Focus")

        option_layout.addWidget(self.auto_exposure)
        option_layout.addWidget(self.auto_white_balance)
        option_layout.addWidget(self.auto_focus)

        # ---------------------------------------------
        # Buttons
        # ---------------------------------------------

        self.connect_button = QPushButton("Connect")

        self.disconnect_button = QPushButton("Disconnect")

        self.email_widget = EmailWidget()
        self.email_widget.send_button.hide()
        self.auto_email_checkbox = QCheckBox(
            "Automatically email PPE alerts"
        )
        self.close_button = QPushButton("Close Application")

        # ---------------------------------------------
        # Layout
        # ---------------------------------------------

        self.content_layout.addWidget(camera_group)
        self.content_layout.addWidget(parameter_group)
        self.content_layout.addWidget(option_group)

        self.content_layout.addWidget(self.connect_button)
        self.content_layout.addWidget(self.disconnect_button)
        self.content_layout.addWidget(self.auto_email_checkbox)
        self.content_layout.addWidget(self.email_widget)
        self.content_layout.addWidget(self.close_button)

        self.content_layout.addStretch()

    # --------------------------------------------------

    def _connect_signals(self):

        self.connect_button.clicked.connect(
            self._on_connect_clicked
        )

        self.disconnect_button.clicked.connect(
            self.disconnect_requested.emit
        )

        self.close_button.clicked.connect(
            self.close_requested.emit
        )

        self.email_widget.status_changed.connect(
            self.email_status_changed.emit
        )

        self.save_rtsp_ip_button.clicked.connect(
            lambda: self.rtsp_ip_save_requested.emit(
                self.rtsp_ip_edit.text()
            )
        )

        # --------------------------------------
        # Sliders
        # --------------------------------------

        self.exposure.valueChanged.connect(
            self.exposure_changed.emit
        )

        self.gain.valueChanged.connect(
            self.gain_changed.emit
        )

        self.brightness.valueChanged.connect(
            self.brightness_changed.emit
        )

        self.contrast.valueChanged.connect(
            self.contrast_changed.emit
        )

        self.saturation.valueChanged.connect(
            self.saturation_changed.emit
        )

        self.gamma.valueChanged.connect(
            self.gamma_changed.emit
        )

        # --------------------------------------
        # Checkboxes
        # --------------------------------------

        self.auto_exposure.toggled.connect(
            self.auto_exposure_changed.emit
        )

        self.auto_white_balance.toggled.connect(
            self.auto_white_balance_changed.emit
        )

        self.auto_focus.toggled.connect(
            self.auto_focus_changed.emit
        )

    # --------------------------------------------------

    def _slider(self):

        slider = QSlider(Qt.Horizontal)

        slider.setRange(0, 100)

        slider.setValue(50)

        return slider

    # --------------------------------------------------

    def _on_connect_clicked(self):

        camera_index = self.camera_combo.currentData()

        if camera_index is None:
            camera_index = self.camera_combo.currentIndex()

        self.connect_requested.emit(camera_index)

    # --------------------------------------------------
    # Public API
    # --------------------------------------------------

    def set_rtsp_camera(self, ip_address, url):
        self.rtsp_ip_edit.setText(ip_address)
        self.camera_combo.setItemData(0, url)
        self.camera_combo.setItemText(
            0,
            f"RTSP Camera ({ip_address})",
        )
