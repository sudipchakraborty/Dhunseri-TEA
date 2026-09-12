from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QFrame,
    QGroupBox,
    QGridLayout,
    QHBoxLayout,
    QLineEdit,
    QLayout,
    QPushButton,
    QScrollArea,
    QSlider,
    QSpinBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
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
    image_browse_requested = Signal()
    previous_image_requested = Signal()
    next_image_requested = Signal()

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
    pipeline_changed = Signal(dict)

    # --------------------------------------------------

    def __init__(
        self,
        rtsp_url="rtsp://192.168.0.135:8554/picam",
        image_path="",
    ):

        super().__init__("Camera Settings")
        self._rtsp_url = rtsp_url
        self._image_path = image_path

        self._build_ui()

        # Keep the title visible and let controls retain their minimum sizes
        # when the history table leaves less vertical space for this panel.
        self.content_layout.setSizeConstraint(
            QLayout.SizeConstraint.SetMinAndMaxSize
        )
        self.layout().removeWidget(self.content_widget)
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.scroll_area.setWidget(self.content_widget)
        self.layout().addWidget(self.scroll_area, 1)

        self._connect_signals()

    # --------------------------------------------------

    def _build_ui(self):

        self.tabs = QTabWidget()
        settings_tab = QWidget()
        settings_layout = QVBoxLayout(settings_tab)
        settings_layout.setContentsMargins(6, 8, 6, 6)
        settings_layout.setSpacing(10)
        parameters_tab = QWidget()
        parameters_layout = QVBoxLayout(parameters_tab)
        parameters_layout.setContentsMargins(6, 8, 6, 6)

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
        self.camera_combo.addItem(
            "Image File",
            ("image", self._image_path),
        )
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

        image_layout = QHBoxLayout()
        image_layout.setSpacing(6)
        self.image_path_edit = QLineEdit(self._image_path)
        self.image_path_edit.setReadOnly(True)
        self.image_path_edit.setPlaceholderText("No image selected")
        self.previous_image_button = QPushButton("<")
        self.next_image_button = QPushButton(">")
        self.browse_image_button = QPushButton("Browse")
        for button in (
            self.previous_image_button,
            self.next_image_button,
        ):
            button.setFixedWidth(34)
        self.browse_image_button.setFixedWidth(76)
        image_layout.addWidget(self.image_path_edit, 1)
        image_layout.addWidget(self.previous_image_button)
        image_layout.addWidget(self.next_image_button)
        image_layout.addWidget(self.browse_image_button)
        camera_layout.addLayout(image_layout)

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

        self.exposure, exposure_field = self._slider_field("exposure")
        self.gain, gain_field = self._slider_field("gain")
        self.brightness, brightness_field = self._slider_field("brightness")
        self.contrast, contrast_field = self._slider_field("contrast")
        self.saturation, saturation_field = self._slider_field("saturation")
        self.gamma, gamma_field = self._slider_field("gamma")
        self.temperature, temperature_field = self._slider_field("temperature")
        self.tint, tint_field = self._slider_field("tint")
        self.averaging_window = QSpinBox()
        self.averaging_window.setRange(1, 100)
        self.averaging_window.setValue(20)
        self.averaging_window.setSuffix(" frames")

        parameter_layout.addRow("Exposure", exposure_field)
        parameter_layout.addRow("Gain", gain_field)
        parameter_layout.addRow("Brightness", brightness_field)
        parameter_layout.addRow("Contrast", contrast_field)
        parameter_layout.addRow("Saturation", saturation_field)
        parameter_layout.addRow("Gamma", gamma_field)
        parameter_layout.addRow("Temperature", temperature_field)
        parameter_layout.addRow("Tint", tint_field)
        parameter_layout.addRow(
            "Moving Average",
            self.averaging_window,
        )

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

        settings_layout.addWidget(camera_group)
        settings_layout.addWidget(option_group)

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
        settings_layout.addLayout(button_layout)
        settings_layout.addStretch()

        parameters_layout.addWidget(parameter_group)
        parameters_layout.addStretch()

        pipeline_tab = QWidget()
        pipeline_layout = QVBoxLayout(pipeline_tab)
        pipeline_layout.setContentsMargins(8, 10, 8, 8)
        pipeline_group = QGroupBox("Pype Line Selection")
        pipeline_group_layout = QVBoxLayout(pipeline_group)
        self.pipeline_checkboxes = {
            "colour_adjustment": QCheckBox("Colour Adjustment"),
            "image_smoothing": QCheckBox("Frame Smoothing"),
            "sample_roi_mask": QCheckBox("Sample ROI Mask"),
            "dominant_colour_fill": QCheckBox("Dominant Colour Fill"),
        }
        for checkbox in self.pipeline_checkboxes.values():
            pipeline_group_layout.addWidget(checkbox)
        pipeline_layout.addWidget(pipeline_group)
        pipeline_layout.addStretch()

        self.tabs.addTab(settings_tab, "Camera Settings")
        self.tabs.addTab(parameters_tab, "Parameters")
        self.tabs.addTab(pipeline_tab, "Pipeline")
        self.content_layout.addWidget(self.tabs)

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

        self.browse_image_button.clicked.connect(
            self.image_browse_requested.emit
        )
        self.previous_image_button.clicked.connect(
            self.previous_image_requested.emit
        )
        self.next_image_button.clicked.connect(
            self.next_image_requested.emit
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

        for checkbox in self.pipeline_checkboxes.values():
            checkbox.toggled.connect(self._pipeline_changed)

    # --------------------------------------------------

    def _slider(self):

        slider = QSlider(Qt.Horizontal)

        slider.setRange(0, 100)

        slider.setValue(50)
        slider.setMinimumHeight(22)
        slider.setToolTip("50 = neutral; move left to reduce, right to increase")

        return slider

    def _slider_field(self, name):
        """Return a slider with an editable value box on its right."""

        slider = self._slider()
        value_box = QSpinBox()
        value_box.setRange(slider.minimum(), slider.maximum())
        value_box.setValue(slider.value())
        # Windows display scaling gives the spin buttons a generous width;
        # reserve enough space for the complete 0-100 text beside them.
        value_box.setFixedWidth(90)
        value_box.setAlignment(Qt.AlignmentFlag.AlignRight)
        value_box.setToolTip("Enter a value from 0 to 100")

        slider.valueChanged.connect(value_box.setValue)
        value_box.valueChanged.connect(slider.setValue)
        setattr(self, f"{name}_value", value_box)

        field = QWidget()
        field_layout = QHBoxLayout(field)
        field_layout.setContentsMargins(0, 0, 0, 0)
        field_layout.setSpacing(8)
        field_layout.addWidget(slider, 1)
        field_layout.addWidget(value_box)
        return slider, field

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

    def set_image_path(self, image_path):
        self._image_path = image_path or ""
        display_path = self._image_path.replace("\\", "/")
        display_name = display_path.rsplit("/", 1)[-1] if display_path else ""
        self.image_path_edit.setText(display_name)
        self.image_path_edit.setToolTip(self._image_path)
        image_index = self.camera_combo.count() - 1
        self.camera_combo.setItemData(
            image_index,
            ("image", self._image_path),
        )
        label = "Image File"
        if self._image_path:
            label = f"Image File ({display_name})"
        self.camera_combo.setItemText(image_index, label)

    def select_image_source(self):
        self.camera_combo.setCurrentIndex(self.camera_combo.count() - 1)

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
            "pipeline": self.pipeline_settings(),
        }

    def pipeline_settings(self):
        return {
            name: checkbox.isChecked()
            for name, checkbox in self.pipeline_checkboxes.items()
        }

    def _pipeline_changed(self, _checked):
        values = self.pipeline_settings()
        self.pipeline_changed.emit(values)
        self.control_settings_changed.emit()

    def apply_control_settings(self, values):
        for name in (
            "exposure", "gain", "brightness", "contrast", "saturation",
            "gamma", "temperature", "tint", "averaging_window",
        ):
            getattr(self, name).setValue(values[name])
        self.auto_exposure.setChecked(values["auto_exposure"])
        self.auto_white_balance.setChecked(values["auto_white_balance"])
        self.auto_focus.setChecked(values["auto_focus"])
        pipeline = values.get("pipeline", {})
        for name, checkbox in self.pipeline_checkboxes.items():
            checkbox.setChecked(bool(pipeline.get(name, False)))

    def set_reading_active(self, active):
        self.start_reading_button.setEnabled(not active)
        self.stop_reading_button.setEnabled(active)
