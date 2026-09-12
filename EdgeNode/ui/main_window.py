from datetime import datetime
from pathlib import Path
import re

import cv2

from PySide6.QtCore import Qt, QThread, QTimer
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QDialog,
    QFileDialog,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from SciCam.camera_worker import CameraWorker
from SciCam.camera_settings import CameraSettings
from SciCam.camera_control_settings import CameraControlSettings
from SciCam.frame_converter import FrameConverter
from SciCam.inspection_history import (
    DEFAULT_IMAGE_DIR,
    PROJECT_ROOT,
    InspectionHistoryStore,
)
from SciCam.processing.frame_processor import FrameProcessor
from SciCam.processing.reference_colour_correction import ReferenceColourCorrector
from SciCam.report_generator import InspectionReportGenerator

from .history_panel import HistoryPanel
from .inspection_panel import InspectionPanel
from .metrics_config_dialog import MetricsConfigDialog
from .result_panel import ResultPanel
from .status_bar import StatusBar
from .panels.control_panel import ControlPanel


class MainWindow(QMainWindow):
    """
    Main Application Window
    """

    IMAGE_EXTENSIONS = {
        ".bmp",
        ".jpeg",
        ".jpg",
        ".png",
        ".tif",
        ".tiff",
    }

    def __init__(self):
        super().__init__()

        self.camera_thread = None
        self.camera_worker = None
        self._active_camera_source = None
        self._pending_camera_source = None
        self._reading_active = False
        self._closing = False
        self._shutdown_timer = QTimer(self)
        self._shutdown_timer.setSingleShot(True)
        self._shutdown_timer.timeout.connect(
            self._force_camera_shutdown
        )

        self.frame_processor = FrameProcessor()
        self.camera_settings = CameraSettings()
        self.camera_control_settings = CameraControlSettings()
        self.history_store = InspectionHistoryStore()
        self.report_generator = InspectionReportGenerator(
            self.frame_processor.analysis_metrics
        )
        self.reference_colour_corrector = ReferenceColourCorrector()
        self._dominant_filter_applied = False
        self._dominant_filter_colour = None
        self._settings_before_correction = None

        # Store latest inspection result
        self.last_result = None

        self._configure_window()
        self._build_ui()
        self.control_panel.apply_control_settings(
            self.camera_control_settings.values
        )
        self.inspection_panel.load_reference_image(
            self.camera_control_settings.values.get(
                "reference_image_path", ""
            )
        )
        self._connect_signals()
        self._apply_control_settings_to_processor()
        self._load_history()

        # Connect the configured source by default. A saved image path is
        # reloaded for offline analysis; otherwise the RTSP camera remains the
        # live default and USB cameras stay selectable from the camera menu.
        startup_source = self.camera_settings.rtsp_url
        if self.camera_settings.image_path:
            startup_source = ("image", self.camera_settings.image_path)
            self.control_panel.select_image_source()
        QTimer.singleShot(
            0,
            lambda: self.start_camera(startup_source),
        )

    # ---------------------------------------------------------

    def _configure_window(self):

        self.setWindowTitle(
            "TeaVision Edge - Industrial Tea Fermentation Analysis System"
        )

        self.resize(1400, 900)
        self.setMinimumSize(1200, 700)

    # ---------------------------------------------------------

    def _build_ui(self):

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        content_layout = QHBoxLayout()
        content_layout.setSpacing(10)

        self.control_panel = ControlPanel(
            self.camera_settings.rtsp_url,
            self.camera_settings.image_path,
        )
        self.control_panel.set_rtsp_camera(
            self.camera_settings.rtsp_ip,
            self.camera_settings.rtsp_url,
        )
        self.control_panel.set_image_path(
            self.camera_settings.image_path
        )
        self.inspection_panel = InspectionPanel()
        self.result_panel = ResultPanel()

        # Stable side-panel widths prevent live result text and slider updates
        # from repeatedly changing the horizontal layout allocation.
        # Give calibration controls enough room for three-digit value boxes.
        # The image and result areas can use the remaining flexible width.
        self.control_panel.setFixedWidth(430)
        self.result_panel.setFixedWidth(300)

        content_layout.addWidget(self.control_panel)
        content_layout.addWidget(self.inspection_panel, 1)
        content_layout.addWidget(self.result_panel)

        main_layout.addLayout(content_layout)

        self.history_panel = HistoryPanel()
        self.history_panel.setFixedHeight(220)
        self.control_panel.email_widget.set_payload_provider(
            self._selected_history_email
        )

        main_layout.addWidget(self.history_panel)

        self.app_status_bar = StatusBar()
        self.setStatusBar(self.app_status_bar)

    # ---------------------------------------------------------

    def _connect_signals(self):

        self.control_panel.connect_requested.connect(
            self.start_camera
        )

        self.control_panel.disconnect_requested.connect(
            self.stop_camera
        )
        self.control_panel.start_reading_requested.connect(
            self.start_reading
        )
        self.control_panel.stop_reading_requested.connect(
            self.stop_reading
        )

        self.control_panel.save_requested.connect(
            self.save_inspection
        )

        self.control_panel.close_requested.connect(
            self.close
        )

        self.control_panel.averaging_window_changed.connect(
            self.frame_processor.set_averaging_window
        )
        self.control_panel.pipeline_changed.connect(
            self._set_pipeline_options
        )

        self.control_panel.exposure_changed.connect(
            self.frame_processor.set_exposure
        )
        self.control_panel.gain_changed.connect(
            self.frame_processor.set_gain
        )
        self.control_panel.brightness_changed.connect(
            self.frame_processor.set_brightness
        )
        self.control_panel.contrast_changed.connect(
            self.frame_processor.set_contrast
        )
        self.control_panel.saturation_changed.connect(
            self.frame_processor.set_saturation
        )
        self.control_panel.gamma_changed.connect(
            self.frame_processor.set_gamma
        )
        self.control_panel.temperature_changed.connect(
            self.frame_processor.set_temperature
        )
        self.control_panel.tint_changed.connect(
            self.frame_processor.set_tint
        )
        self.control_panel.control_settings_changed.connect(
            self.save_control_settings
        )
        self.control_panel.control_settings_changed.connect(
            self.reprocess_paused_frame
        )
        self.control_panel.auto_white_balance_changed.connect(
            self.set_auto_white_balance
        )
        self.control_panel.auto_exposure_changed.connect(
            self.set_auto_exposure
        )
        self.control_panel.auto_focus_changed.connect(
            self.set_auto_focus
        )

        self.control_panel.config_requested.connect(
            self.configure_metrics
        )

        self.control_panel.email_status_changed.connect(
            self.statusBar().showMessage
        )

        self.history_panel.image_requested.connect(
            self.show_history_image
        )
        self.inspection_panel.correction_requested.connect(
            self.correct_to_reference
        )
        self.inspection_panel.cancel_correction_requested.connect(
            self.cancel_reference_correction
        )
        self.inspection_panel.reference_changed.connect(
            self.reference_image_changed
        )
        self.inspection_panel.reference_clear_requested.connect(
            self.clear_reference_image
        )

        self.control_panel.rtsp_ip_save_requested.connect(
            self.save_rtsp_ip
        )
        self.control_panel.image_browse_requested.connect(
            self.browse_image
        )
        self.control_panel.previous_image_requested.connect(
            lambda: self.load_adjacent_image(-1)
        )
        self.control_panel.next_image_requested.connect(
            lambda: self.load_adjacent_image(1)
        )

    # ---------------------------------------------------------

    def start_camera(self, source):
        if self._is_image_source(source):
            self.start_image_source(source[1])
            return

        if self.camera_thread is not None:
            if source == self._active_camera_source:
                self.statusBar().showMessage(
                    f"Camera {source} is already connected."
                )
                return

            # CameraWorker owns its capture and must finish releasing it before
            # another source is opened. Remember the requested source and
            # start it from _camera_finished once shutdown is complete.
            self._pending_camera_source = source
            self.statusBar().showMessage(
                f"Switching camera to {source}..."
            )
            self.stop_camera()
            return

        self._pending_camera_source = None
        self._active_camera_source = source
        self.frame_processor.reset_average()
        self.camera_thread = QThread()

        self.camera_worker = CameraWorker()

        self.camera_worker.set_camera(source)
        self.camera_worker.set_frame_processor(self.frame_processor)
        self.camera_worker.set_reading_enabled(True)
        self._reading_active = True
        self.control_panel.set_reading_active(True)
        if not isinstance(source, str):
            self.camera_worker.set_auto_exposure(
                self.control_panel.auto_exposure.isChecked()
            )
            self.camera_worker.set_auto_white_balance(
                self.control_panel.auto_white_balance.isChecked()
            )
            self.camera_worker.set_auto_focus(
                self.control_panel.auto_focus.isChecked()
            )

        self.camera_worker.moveToThread(
            self.camera_thread
        )

        self.camera_thread.started.connect(
            self.camera_worker.run
        )

        self.camera_worker.result_ready.connect(
            self.update_result
        )
        self.camera_worker.paused_result_ready.connect(
            self.update_paused_result
        )
        self.camera_worker.processing_error.connect(
            self.show_processing_error
        )

        self.camera_worker.finished.connect(
            self.camera_thread.quit
        )

        self.camera_worker.finished.connect(
            self.camera_worker.deleteLater
        )

        self.camera_thread.finished.connect(
            self.camera_thread.deleteLater
        )

        self.camera_thread.finished.connect(
            self._camera_finished
        )

        self.camera_thread.start()

        self.statusBar().showMessage(
            f"Camera {source} Connecting"
        )

    # ---------------------------------------------------------

    def update_result(self, result):

        if not self._reading_active:
            return

        self._display_result(result)

    def update_paused_result(self, result):
        if self._reading_active:
            return
        self._display_result(result)

    def start_image_source(self, image_path):
        if not image_path:
            QMessageBox.warning(
                self,
                "Image unavailable",
                "Browse and select an image before connecting Image File.",
            )
            return

        if self.camera_thread is not None:
            self._pending_camera_source = ("image", image_path)
            self.statusBar().showMessage("Switching camera to image file...")
            self.stop_camera()
            return

        self._pending_camera_source = None
        self._active_camera_source = ("image", image_path)
        self._reading_active = False
        self.control_panel.set_reading_active(False)

        frame = cv2.imread(image_path)
        if frame is None:
            QMessageBox.warning(
                self,
                "Image unavailable",
                f"The selected image could not be loaded:\n{image_path}",
            )
            self._active_camera_source = None
            return

        try:
            result = self._process_still_image(frame)
        except Exception as error:
            self.show_processing_error(str(error))
            self._active_camera_source = None
            return

        self._display_result(result)
        self.statusBar().showMessage(
            f"Image analysed: {Path(image_path).name}"
        )

    def _process_still_image(self, frame):
        self.frame_processor.reset_average()
        result = None
        for _index in range(self.frame_processor.brown_average.window_size):
            result = self.frame_processor.process(frame)
        return result

    def _display_result(self, result):

        try:
            # Store latest inspection
            self.last_result = result

            self.inspection_panel.set_original_image(
                FrameConverter.to_qimage(result.original)
            )

            display_image = result.white_balance
            if self.control_panel.pipeline_settings()["sample_roi_mask"]:
                display_image = self.frame_processor.sample_roi.crop_around_sample(
                    display_image
                )
            self.inspection_panel.set_white_balance_image(
                FrameConverter.to_qimage(display_image)
            )

            self.result_panel.update_results(result)

        except Exception as ex:

            self.statusBar().showMessage(
                f"Processing Error : {ex}"
            )

    def show_processing_error(self, error):
        self.statusBar().showMessage(
            f"Processing Error : {error}"
        )

    def correct_to_reference(self, reference_path):
        if self.last_result is None:
            QMessageBox.warning(
                self,
                "Correction unavailable",
                "Wait for a camera image before applying correction.",
            )
            return
        reference = cv2.imread(reference_path)
        if reference is None:
            QMessageBox.warning(
                self,
                "Correction unavailable",
                "The selected reference image could not be loaded.",
            )
            return

        self.statusBar().showMessage("Calculating reference correction...")
        current = self.control_panel.control_settings()
        source = self.last_result.original
        source_mask = self.frame_processor.sample_roi.create_mask(source)
        try:
            values, before_error, after_error = (
                self.reference_colour_corrector.correct(
                    source,
                    source_mask,
                    reference,
                    current,
                )
            )
        except (TypeError, ValueError, cv2.error) as error:
            QMessageBox.warning(self, "Correction unavailable", str(error))
            return

        self._settings_before_correction = current.copy()
        self.inspection_panel.set_correction_active(True)
        for name, value in values.items():
            getattr(self.control_panel, name).setValue(value)
        self.save_control_settings()
        self.reprocess_paused_frame()
        self.statusBar().showMessage(
            "Reference correction applied "
            f"(colour error {before_error:.1f} to {after_error:.1f})."
        )

    def cancel_reference_correction(self):
        if self._settings_before_correction is None:
            return
        previous = self._settings_before_correction
        self._settings_before_correction = None
        self.control_panel.apply_control_settings(previous)
        self.save_control_settings()
        self.reprocess_paused_frame()
        self.inspection_panel.set_correction_active(False)
        self.statusBar().showMessage(
            "Reference correction cancelled; previous settings restored."
        )

    def apply_dominant_filter(self):
        if self.last_result is None:
            self.statusBar().showMessage(
                "Wait for a camera image before applying the filter."
            )
            return
        self._dominant_filter_applied = True
        self.inspection_panel.set_filter_active(True)
        self._display_result(self.last_result)
        colour = self._dominant_filter_colour
        colour_text = ""
        if colour is not None:
            blue, green, red = colour
            colour_text = f" RGB({red}, {green}, {blue})"
        self.statusBar().showMessage(
            f"Dominant-colour filter applied.{colour_text}"
        )

    def discard_dominant_filter(self):
        if not self._dominant_filter_applied:
            return
        self._dominant_filter_applied = False
        self._dominant_filter_colour = None
        self.inspection_panel.set_filter_active(False)
        if self.last_result is not None:
            self._display_result(self.last_result)
        self.statusBar().showMessage("Dominant-colour filter discarded.")

    # ---------------------------------------------------------

    def save_inspection(self):
        """
        Save current inspection into the history table.
        """

        if self.last_result is None:

            self.statusBar().showMessage(
                "Nothing to save."
            )

            return

        if (
            not self._is_image_source(self._active_camera_source)
            and self.frame_processor.brown_average.sample_count
            < self.frame_processor.brown_average.window_size
        ):
            self.statusBar().showMessage(
                "Please wait for brown content to stabilize."
            )
            return

        sample_id, accepted = QInputDialog.getText(
            self,
            "Save Sample",
            "Enter Sample ID:",
        )
        sample_id = sample_id.strip()
        if not accepted:
            return
        if not sample_id:
            QMessageBox.warning(
                self,
                "Sample ID required",
                "Please enter a Sample ID before saving.",
            )
            return

        captured_at = datetime.now()
        safe_id = re.sub(r"[^A-Za-z0-9_-]+", "_", sample_id).strip("_")
        safe_id = safe_id or "sample"
        filename = (
            f"{captured_at.strftime('%Y%m%d_%H%M%S_%f')}_"
            f"{safe_id}.jpg"
        )
        image_path = DEFAULT_IMAGE_DIR / filename

        if not cv2.imwrite(
            str(image_path),
            self.last_result.white_balance,
            [cv2.IMWRITE_JPEG_QUALITY, 95],
        ):
            QMessageBox.critical(
                self,
                "Image save failed",
                f"Could not save the sample image:\n{image_path}",
            )
            return

        record = {
            "captured_at": captured_at.isoformat(timespec="seconds"),
            "sample_id": sample_id,
            "brown_percentage": self.last_result.brown_percentage,
            "fermentation_status": (
                self.last_result.fermentation_status
            ),
            "tea_quality": self.last_result.tea_quality,
            "confidence": self.last_result.confidence,
            "processing_ms": self.last_result.processing_ms,
            "image_path": image_path.relative_to(
                PROJECT_ROOT
            ).as_posix(),
            "average_rgb": self.last_result.average_rgb,
            "average_lab": self.last_result.average_lab,
            "brightness": self.last_result.brightness,
        }

        try:
            self.history_store.add(record)
        except Exception as error:
            QMessageBox.critical(
                self,
                "History save failed",
                str(error),
            )
            return

        self.history_panel.add_record(record, insert_at_top=True)

        self.statusBar().showMessage(
            f"Sample {sample_id} saved."
        )

    # ---------------------------------------------------------

    def _load_history(self):
        for record in self.history_store.all_newest_first():
            self.history_panel.add_record(
                record,
                insert_at_top=False,
            )

    # ---------------------------------------------------------

    def show_history_image(self, image_path, sample_id):
        path = PROJECT_ROOT / image_path
        record = self.history_panel.selected_record()
        if record is None or record["image_path"] != image_path:
            QMessageBox.warning(
                self,
                "History record unavailable",
                "The selected inspection record is unavailable.",
            )
            return
        try:
            report_path = self.report_generator.generate(record, path)
        except (OSError, TypeError, ValueError) as error:
            QMessageBox.warning(self, "Report unavailable", str(error))
            return

        pixmap = QPixmap(str(report_path))
        if pixmap.isNull():
            QMessageBox.warning(
                self,
                "Report unavailable",
                f"Generated report could not be displayed:\n{report_path}",
            )
            return

        dialog = QDialog(self)
        dialog.setWindowTitle(f"Inspection Report: {sample_id}")
        dialog.resize(620, 700)
        layout = QVBoxLayout(dialog)
        image_label = QLabel()
        image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        image_label.setPixmap(
            pixmap.scaled(
                560,
                600,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        )
        layout.addWidget(image_label)

        send_email_button = QPushButton("Send This Report by Email")
        send_email_button.clicked.connect(
            lambda: self._send_previewed_history_email(
                image_path,
                sample_id,
                report_path,
                send_email_button,
            )
        )
        layout.addWidget(send_email_button)
        dialog.exec()

    # ---------------------------------------------------------

    def _send_previewed_history_email(
        self,
        image_path,
        sample_id,
        report_path,
        button,
    ):
        record = self.history_panel.selected_record()
        if (
            record is None
            or record["image_path"] != image_path
            or record["sample_id"] != sample_id
        ):
            QMessageBox.warning(
                self,
                "History record unavailable",
                "The previewed history record is no longer selected.",
            )
            return

        try:
            payload = self._selected_history_email(report_path)
        except (OSError, ValueError) as error:
            QMessageBox.warning(self, "Email unavailable", str(error))
            return

        button.setEnabled(False)
        self.control_panel.email_widget.send_succeeded.connect(
            button.deleteLater
        )
        self.control_panel.email_widget.send_failed.connect(
            lambda _error: button.setEnabled(True)
        )
        self.control_panel.email_widget.send_email(**payload)

    # ---------------------------------------------------------

    def _selected_history_email(self, prepared_report_path=None):
        record = self.history_panel.selected_record()
        if record is None:
            raise ValueError(
                "Select an inspection history record before sending email."
            )

        image_path = PROJECT_ROOT / record["image_path"]
        if not image_path.is_file():
            raise ValueError(f"Saved image was not found: {image_path}")

        report_path = (
            Path(prepared_report_path)
            if prepared_report_path is not None
            else self.report_generator.generate(record, image_path)
        )
        subject = f"Tea quality assessment: {record['sample_id']}"
        message = (
            "TeaVision Edge inspection result\n\n"
            f"Sample ID: {record['sample_id']}\n"
            f"Captured: {record['captured_at'].replace('T', ' ')}\n"
            f"Brown content: {record['brown_percentage']:.2f}%\n"
            f"Fermentation: {record['fermentation_status']}\n"
            f"Tea quality: {record['tea_quality']}\n"
            f"Confidence: {record['confidence']:.2f}\n"
            f"Processing time: {record['processing_ms']:.2f} ms\n\n"
            "The generated tea quality assessment report is attached."
        )
        return {
            "subject": subject,
            "message": message,
            "attachments": [report_path],
        }

    # ---------------------------------------------------------

    def configure_metrics(self):
        dialog = MetricsConfigDialog(
            self.frame_processor.analysis_metrics,
            self,
        )
        if dialog.exec():
            self.frame_processor.reset_average()
            self.statusBar().showMessage(
                "Analysis metrics saved; stabilizing new result."
            )

    # ---------------------------------------------------------

    def save_rtsp_ip(self, ip_address):
        try:
            self.camera_settings.save(ip_address)
        except (KeyError, TypeError, ValueError) as error:
            QMessageBox.warning(
                self,
                "Invalid camera IP",
                str(error),
            )
            return

        self.control_panel.set_rtsp_camera(
            self.camera_settings.rtsp_ip,
            self.camera_settings.rtsp_url,
        )
        self.statusBar().showMessage(
            "Camera IP saved. Select RTSP Camera and click Connect."
        )

    def browse_image(self):
        start_dir = (
            str(Path(self.camera_settings.image_path).parent)
            if self.camera_settings.image_path
            else str(PROJECT_ROOT)
        )
        image_path, _selected_filter = QFileDialog.getOpenFileName(
            self,
            "Select Inspection Image",
            start_dir,
            "Images (*.png *.jpg *.jpeg *.bmp *.tif *.tiff);;All Files (*)",
        )
        if not image_path:
            return

        self.load_image_path(image_path)

    def load_image_path(self, image_path):
        try:
            self.camera_settings.save(image_path=image_path)
        except (KeyError, TypeError, ValueError) as error:
            QMessageBox.warning(
                self,
                "Image save failed",
                str(error),
            )
            return

        self.control_panel.set_image_path(self.camera_settings.image_path)
        self.control_panel.select_image_source()
        self.start_image_source(self.camera_settings.image_path)

    def load_adjacent_image(self, direction):
        current_path = Path(self.camera_settings.image_path)
        if not self.camera_settings.image_path or not current_path.parent.is_dir():
            QMessageBox.warning(
                self,
                "Image unavailable",
                "Browse and select an image first.",
            )
            return

        images = self._image_files_in_folder(current_path.parent)
        if not images:
            QMessageBox.warning(
                self,
                "Image unavailable",
                "No image files were found in the selected folder.",
            )
            return

        try:
            current_index = images.index(current_path.resolve())
        except ValueError:
            current_index = 0
        next_index = (current_index + direction) % len(images)
        self.load_image_path(str(images[next_index]))

    def _image_files_in_folder(self, folder):
        return sorted(
            (
                path.resolve()
                for path in Path(folder).iterdir()
                if path.is_file()
                and path.suffix.lower() in self.IMAGE_EXTENSIONS
            ),
            key=lambda path: self._natural_path_key(path),
        )

    @staticmethod
    def _natural_path_key(path):
        return [
            int(part) if part.isdigit() else part.lower()
            for part in re.split(r"(\d+)", path.name)
        ]

    # ---------------------------------------------------------

    def stop_camera(self):

        if self._is_image_source(self._active_camera_source):
            self._active_camera_source = None
            self._reading_active = False
            self.control_panel.set_reading_active(False)
            self.statusBar().showMessage("Image source cleared.")
            return

        if self.camera_worker is not None:
            self.camera_worker.stop()

    def start_reading(self):
        if self.camera_worker is None:
            self.statusBar().showMessage("No camera is connected.")
            return
        self.frame_processor.reset_average()
        self.camera_worker.set_reading_enabled(True)
        self._reading_active = True
        self.control_panel.set_reading_active(True)
        self.statusBar().showMessage("Camera reading started.")

    def stop_reading(self):
        if self.camera_worker is None:
            self.statusBar().showMessage("No camera is connected.")
            return
        self.camera_worker.set_reading_enabled(False)
        self._reading_active = False
        self.control_panel.set_reading_active(False)
        self.statusBar().showMessage(
            "Camera reading paused; parameter controls remain enabled."
        )

    def reprocess_paused_frame(self):
        if self.camera_worker is not None and not self._reading_active:
            self.camera_worker.request_frozen_frame_reprocess()

    def set_auto_white_balance(self, enabled):
        if self.camera_worker is not None:
            self.camera_worker.set_auto_white_balance(enabled)

    def set_auto_exposure(self, enabled):
        if self.camera_worker is not None:
            self.camera_worker.set_auto_exposure(enabled)

    def set_auto_focus(self, enabled):
        if self.camera_worker is not None:
            self.camera_worker.set_auto_focus(enabled)

    def _apply_control_settings_to_processor(self):
        values = self.control_panel.control_settings()
        self.frame_processor.set_exposure(values["exposure"])
        self.frame_processor.set_gain(values["gain"])
        self.frame_processor.set_brightness(values["brightness"])
        self.frame_processor.set_contrast(values["contrast"])
        self.frame_processor.set_saturation(values["saturation"])
        self.frame_processor.set_gamma(values["gamma"])
        self.frame_processor.set_temperature(values["temperature"])
        self.frame_processor.set_tint(values["tint"])
        self.frame_processor.set_averaging_window(
            values["averaging_window"]
        )
        self.frame_processor.set_pipeline_options(values["pipeline"])

    def _set_pipeline_options(self, options):
        self.frame_processor.set_pipeline_options(options)
        if self._is_image_source(self._active_camera_source):
            self.start_image_source(self._active_camera_source[1])

    def save_control_settings(self):
        try:
            values = self.control_panel.control_settings()
            values["reference_image_path"] = (
                str(self.inspection_panel.reference_image_path)
                if self.inspection_panel.reference_image_path is not None
                else ""
            )
            self.camera_control_settings.save(
                values
            )
        except OSError as error:
            self.statusBar().showMessage(
                f"Could not save camera controls: {error}"
            )

    def reference_image_changed(self, _path):
        self.save_control_settings()
        self.statusBar().showMessage(
            "Reference image selected and saved."
        )

    def clear_reference_image(self):
        self._settings_before_correction = None
        self.save_control_settings()
        self.reprocess_paused_frame()
        self.statusBar().showMessage(
            "Reference image cleared."
        )

    # ---------------------------------------------------------

    def _camera_finished(self):

        self._shutdown_timer.stop()
        self.frame_processor.reset_average()
        self.camera_worker = None
        self.camera_thread = None
        self._active_camera_source = None
        self._reading_active = False
        self.control_panel.set_reading_active(False)

        pending_source = self._pending_camera_source
        self._pending_camera_source = None

        if pending_source is not None and not self._closing:
            self.statusBar().showMessage(
                f"Connecting camera {pending_source}..."
            )
            QTimer.singleShot(
                0,
                lambda source=pending_source: self.start_camera(source),
            )
            return

        self.statusBar().showMessage(
            "Camera Disconnected"
        )

        if self._closing:
            QTimer.singleShot(0, self.close)

    # ---------------------------------------------------------

    @staticmethod
    def _is_image_source(source):
        return (
            isinstance(source, tuple)
            and len(source) == 2
            and source[0] == "image"
        )

    # ---------------------------------------------------------

    def closeEvent(self, event):

        if self.camera_thread is not None:
            self._closing = True
            self.statusBar().showMessage(
                "Closing camera..."
            )
            self.stop_camera()
            self._shutdown_timer.start(5000)
            event.ignore()
            return

        event.accept()

    # ---------------------------------------------------------

    def _force_camera_shutdown(self):
        """Last-resort exit when a camera backend ignores read timeouts."""
        if self.camera_thread is not None:
            self.camera_thread.requestInterruption()
            self.camera_thread.terminate()
            self.camera_thread.wait(1000)
            self.camera_thread = None
            self.camera_worker = None

        self.close()
