from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QGroupBox,
    QGridLayout,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QSlider,
    QSpinBox,
    QVBoxLayout,
)

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
    start_reading_requested = Signal()
    stop_reading_requested = Signal()
    close_requested = Signal()
    config_requested = Signal()
    email_status_changed = Signal(str)
    rtsp_ip_save_requested = Signal(str)

    # --------------------------------------------------
    # Inspection
    # --------------------------------------------------

    save_requested = Signal()

    # --------------------------------------------------
    # Camera Parameters
    # --------------------------------------------------

    exposure_changed = Signal(int)
    gain_changed = Signal(int)
    brightness_changed = Signal(int)
    contrast_changed = Signal(int)
    saturation_changed = Signal(int)
    gamma_changed = Signal(int)
    temperature_changed = Signal(int)
    tint_changed = Signal(int)

    auto_exposure_changed = Signal(bool)
    auto_white_balance_changed = Signal(bool)
    auto_focus_changed = Signal(bool)
    averaging_window_changed = Signal(int)
    control_settings_changed = Signal()

    # --------------------------------------------------

    def __init__(
        self,
        rtsp_url="rtsp://192.168.0.135:8554/picam",
    ):

        super().__init__("Camera Settings")
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
            "RTSP Camera (PiCam)",
            self._rtsp_url,
        )
        self.camera_combo.addItem("USB Camera 0", 0)
        self.camera_combo.addItem("USB Camera 1", 1)
        self.camera_combo.addItem("USB Camera 2", 2)
        self.camera_combo.setCurrentIndex(0)

        camera_layout.addWidget(self.camera_combo)

        rtsp_ip_layout = QHBoxLayout()
        self.rtsp_ip_edit = QLineEdit(
            self._rtsp_url.split("//", 1)[-1].split(":", 1)[0]
        )
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
        parameter_layout.setVerticalSpacing(8)
        parameter_layout.setHorizontalSpacing(12)
        parameter_layout.setFieldGrowthPolicy(
            QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow
        )
        parameter_group.setMinimumHeight(285)

        self.exposure = self._slider()
        self.gain = self._slider()
        self.brightness = self._slider()
        self.contrast = self._slider()
        self.saturation = self._slider()
        self.gamma = self._slider()
        self.temperature = self._slider()
        self.tint = self._slider()
        self.averaging_window = QSpinBox()
        self.averaging_window.setRange(1, 100)
        self.averaging_window.setValue(20)
        self.averaging_window.setSuffix(" frames")

        parameter_layout.addRow("Exposure", self.exposure)
        parameter_layout.addRow("Gain", self.gain)
        parameter_layout.addRow("Brightness", self.brightness)
        parameter_layout.addRow("Contrast", self.contrast)
        parameter_layout.addRow("Saturation", self.saturation)
        parameter_layout.addRow("Gamma", self.gamma)
        parameter_layout.addRow("Temperature", self.temperature)
        parameter_layout.addRow("Tint", self.tint)
        parameter_layout.addRow(
            "Moving Average",
            self.averaging_window,
        )

        # ---------------------------------------------
        # Options
        # ---------------------------------------------

        option_group = QGroupBox("Options")

        option_layout = QHBoxLayout(option_group)

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
        self.start_reading_button = QPushButton("Start Reading")
        self.stop_reading_button = QPushButton("Stop Reading")
        self.set_reading_active(False)

        self.save_button = QPushButton("Save Inspection")
        self.config_button = QPushButton("Configure Metrics")
        self.email_widget = EmailWidget()
        self.email_widget.send_button.hide()
        self.close_button = QPushButton("Close Application")

        # ---------------------------------------------
        # Layout
        # ---------------------------------------------

        self.content_layout.addWidget(camera_group)
        self.content_layout.addWidget(parameter_group)
        self.content_layout.addWidget(option_group)

        button_layout = QGridLayout()
        button_layout.setHorizontalSpacing(8)
        button_layout.setVerticalSpacing(8)
        button_layout.addWidget(self.connect_button, 0, 0)
        button_layout.addWidget(self.disconnect_button, 0, 1)
        button_layout.addWidget(self.start_reading_button, 1, 0)
        button_layout.addWidget(self.stop_reading_button, 1, 1)
        button_layout.addWidget(self.save_button, 2, 0)
        button_layout.addWidget(self.config_button, 2, 1)
        button_layout.addWidget(self.email_widget, 3, 0)
        button_layout.addWidget(self.close_button, 3, 1)
        self.content_layout.addLayout(button_layout)

        self.content_layout.addStretch()

    # --------------------------------------------------

    def _connect_signals(self):

        self.connect_button.clicked.connect(
            self._on_connect_clicked
        )

        self.disconnect_button.clicked.connect(
            self.disconnect_requested.emit
        )

        self.start_reading_button.clicked.connect(
            self.start_reading_requested.emit
        )

        self.stop_reading_button.clicked.connect(
            self.stop_reading_requested.emit
        )

        self.save_button.clicked.connect(
            self.save_requested.emit
        )

        self.close_button.clicked.connect(
            self.close_requested.emit
        )

        self.config_button.clicked.connect(
            self.config_requested.emit
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

        self.temperature.valueChanged.connect(
            self.temperature_changed.emit
        )

        self.tint.valueChanged.connect(
            self.tint_changed.emit
        )

        self.averaging_window.valueChanged.connect(
            self.averaging_window_changed.emit
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

        for control in (
            self.exposure,
            self.gain,
            self.brightness,
            self.contrast,
            self.saturation,
            self.gamma,
            self.temperature,
            self.tint,
            self.averaging_window,
            self.auto_exposure,
            self.auto_white_balance,
            self.auto_focus,
        ):
            signal = (
                control.toggled
                if isinstance(control, QCheckBox)
                else control.valueChanged
            )
            signal.connect(
                lambda _value: self.control_settings_changed.emit()
            )

    # --------------------------------------------------

    def _slider(self):

        slider = QSlider(Qt.Horizontal)

        slider.setRange(0, 100)

        slider.setValue(50)
        slider.setMinimumHeight(22)
        slider.setToolTip("50 = neutral; move left to reduce, right to increase")

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

    def set_camera_list(self, cameras):
        """
        cameras = [(0, "USB Camera"),
                   (1, "Logitech C920")]
        """

        self.camera_combo.clear()

        for index, name in cameras:

            self.camera_combo.addItem(
                name,
                index,
            )

    def set_rtsp_camera(self, ip_address, url):
        self.rtsp_ip_edit.setText(ip_address)
        self.camera_combo.setItemData(0, url)
        self.camera_combo.setItemText(
            0,
            f"RTSP Camera ({ip_address})",
        )

    def control_settings(self):
        return {
            "exposure": self.exposure.value(),
            "gain": self.gain.value(),
            "brightness": self.brightness.value(),
            "contrast": self.contrast.value(),
            "saturation": self.saturation.value(),
            "gamma": self.gamma.value(),
            "temperature": self.temperature.value(),
            "tint": self.tint.value(),
            "averaging_window": self.averaging_window.value(),
            "auto_exposure": self.auto_exposure.isChecked(),
            "auto_white_balance": self.auto_white_balance.isChecked(),
            "auto_focus": self.auto_focus.isChecked(),
        }

    def apply_control_settings(self, values):
        for name in (
            "exposure", "gain", "brightness", "contrast", "saturation",
            "gamma", "temperature", "tint", "averaging_window",
        ):
            getattr(self, name).setValue(values[name])
        self.auto_exposure.setChecked(values["auto_exposure"])
        self.auto_white_balance.setChecked(values["auto_white_balance"])
        self.auto_focus.setChecked(values["auto_focus"])

    def set_reading_active(self, active):
        self.start_reading_button.setEnabled(not active)
        self.stop_reading_button.setEnabled(active)
