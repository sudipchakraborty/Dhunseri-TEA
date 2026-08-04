from datetime import datetime
import time

import cv2

from PySide6.QtCore import Qt, QThread, QTimer
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from SciCam.camera_worker import CameraWorker
from SciCam.camera_settings import CameraSettings
from SciCam.alert_sound import ContinuousAlertSound
from SciCam.frame_converter import FrameConverter
from SciCam.inspection_history import (
    DEFAULT_IMAGE_DIR,
    PROJECT_ROOT,
    EventHistoryStore,
)
from SciCam.ppe_detector import PPEDetector
from SciCam.ppe_service import PPEDetectionService

from .history_panel import HistoryPanel
from .inspection_panel import InspectionPanel
from .status_bar import StatusBar
from .panels.control_panel import ControlPanel


class MainWindow(QMainWindow):
    """
    Main Application Window
    """

    def __init__(self):
        super().__init__()

        self.camera_thread = None
        self.camera_worker = None
        self._closing = False
        self._shutdown_timer = QTimer(self)
        self._shutdown_timer.setSingleShot(True)
        self._shutdown_timer.timeout.connect(
            self._force_camera_shutdown
        )
        self._alert_sound = ContinuousAlertSound()

        self.camera_settings = CameraSettings()
        self.history_store = EventHistoryStore()
        self._event_cooldown = 10.0
        self._last_event_times = {}
        self._ppe_result = None
        self._latest_frame = None
        self.ppe_service = PPEDetectionService()

        self._configure_window()
        self._build_ui()
        self._connect_signals()
        self._load_history()
        self.ppe_service.start()

        # Try the configured network camera when the event loop starts.
        QTimer.singleShot(
            0,
            lambda: self.start_camera(
                self.camera_settings.rtsp_url
            ),
        )

    # ---------------------------------------------------------

    def _configure_window(self):

        self.setWindowTitle(
            "Danger Zone PPE Monitor - Demo"
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
            self.camera_settings.rtsp_url
        )
        self.control_panel.set_rtsp_camera(
            self.camera_settings.rtsp_ip,
            self.camera_settings.rtsp_url,
        )
        self.inspection_panel = InspectionPanel()

        content_layout.addWidget(self.control_panel, 1)
        content_layout.addWidget(self.inspection_panel, 3)

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

        self.control_panel.close_requested.connect(
            self.close
        )

        self.control_panel.email_status_changed.connect(
            self.statusBar().showMessage
        )

        self.history_panel.event_requested.connect(
            self.show_event_evidence
        )

        self.history_panel.clear_requested.connect(
            self.clear_events
        )
        self.history_panel.send_email_requested.connect(
            self.send_selected_history_email
        )

        self.control_panel.rtsp_ip_save_requested.connect(
            self.save_rtsp_ip
        )

        self.ppe_service.result_ready.connect(
            self._handle_ppe_result
        )
        self.ppe_service.ready.connect(
            lambda: self.statusBar().showMessage(
                "PPE demo detector ready on GPU."
            )
        )
        self.ppe_service.error.connect(
            lambda message: self.statusBar().showMessage(
                f"PPE detector unavailable: {message}"
            )
        )

    # ---------------------------------------------------------

    def start_camera(self, source):

        if self.camera_thread is not None:
            return

        self._ppe_result = None
        self._latest_frame = None

        self.camera_thread = QThread()

        self.camera_worker = CameraWorker()

        self.camera_worker.set_camera(source)

        self.camera_worker.moveToThread(
            self.camera_thread
        )

        self.camera_thread.started.connect(
            self.camera_worker.run
        )

        self.camera_worker.frame_ready.connect(
            self.update_frame
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

    def update_frame(self, frame):
        try:
            self._latest_frame = frame
            display_frame = PPEDetector.draw(frame, self._ppe_result)
            self.inspection_panel.set_original_image(
                FrameConverter.to_qimage(display_frame)
            )
            self.ppe_service.submit(frame)

        except Exception as ex:

            self.statusBar().showMessage(
                f"Camera display error: {ex}"
            )

        finally:
            if self.camera_worker is not None:
                self.camera_worker.frame_consumed()

    def _handle_ppe_result(self, result):
        self._ppe_result = result
        if not result.confirmed or self._latest_frame is None:
            self._stop_continuous_alert()
            return

        self._start_continuous_alert()

        now = time.monotonic()
        event_name = result.event_name
        if event_name and self._event_is_due(event_name, now):
            evidence = PPEDetector.draw(
                self._latest_frame,
                result,
            )
            record = self._save_event(event_name, evidence)
            if (
                record is not None
                and self.control_panel.auto_email_checkbox.isChecked()
            ):
                self.send_event_email(record)

    def _start_continuous_alert(self):
        self._alert_sound.start()

    def _stop_continuous_alert(self):
        self._alert_sound.stop()

    # ---------------------------------------------------------

    def _event_is_due(self, event_name, now):
        previous = self._last_event_times.get(event_name, 0.0)
        if now - previous < self._event_cooldown:
            return False
        self._last_event_times[event_name] = now
        return True

    def _save_event(self, event_name, evidence_frame):
        event_date = datetime.now()
        safe_name = event_name.lower().replace(" ", "_")
        filename = (
            f"{event_date.strftime('%Y%m%d_%H%M%S_%f')}_"
            f"{safe_name}.jpg"
        )
        image_path = DEFAULT_IMAGE_DIR / filename

        if not cv2.imwrite(
            str(image_path),
            evidence_frame,
            [cv2.IMWRITE_JPEG_QUALITY, 95],
        ):
            self.statusBar().showMessage(
                f"Could not save event evidence: {image_path}"
            )
            return None

        record = {
            "event_date": event_date.isoformat(timespec="seconds"),
            "event_name": event_name,
            "evidence_path": image_path.relative_to(
                PROJECT_ROOT
            ).as_posix(),
        }

        try:
            self.history_store.add(record)
        except Exception as error:
            QMessageBox.critical(
                self,
                "Event save failed",
                str(error),
            )
            return None

        self.history_panel.add_record(record, insert_at_top=True)
        self.statusBar().showMessage(
            f"{event_name}; evidence saved."
        )
        return record

    # ---------------------------------------------------------

    def _load_history(self):
        for record in self.history_store.all_newest_first():
            self.history_panel.add_record(
                record,
                insert_at_top=False,
            )

    # ---------------------------------------------------------

    def clear_events(self):
        if self.history_panel.table.rowCount() == 0:
            self.statusBar().showMessage("There are no events to clear.")
            return

        answer = QMessageBox.question(
            self,
            "Clear detection events",
            (
                "Clear all detection events from the table and database?\n\n"
                "Saved evidence images will not be deleted."
            ),
            QMessageBox.StandardButton.Yes
            | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return

        try:
            count = self.history_store.clear()
        except Exception as error:
            QMessageBox.critical(
                self,
                "Could not clear events",
                str(error),
            )
            return

        self.history_panel.clear()
        self.statusBar().showMessage(
            f"Cleared {count} detection event(s)."
        )

    # ---------------------------------------------------------

    def show_event_evidence(self, record):
        image_path = PROJECT_ROOT / record["evidence_path"]
        pixmap = QPixmap(str(image_path))
        if pixmap.isNull():
            QMessageBox.warning(
                self,
                "Evidence unavailable",
                f"Evidence image was not found:\n{image_path}",
            )
            return

        dialog = QDialog(self)
        dialog.setWindowTitle(
            f"Evidence: {record['event_name']}"
        )
        dialog.resize(820, 650)
        layout = QVBoxLayout(dialog)

        image_label = QLabel()
        image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        image_label.setPixmap(
            pixmap.scaled(
                780,
                570,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        )
        layout.addWidget(image_label, 1)

        send_button = QPushButton("Send Evidence by Email")
        send_button.clicked.connect(
            lambda: self.send_event_email(record)
        )
        layout.addWidget(send_button)
        dialog.exec()

    # ---------------------------------------------------------

    def send_event_email(self, record):
        try:
            payload = self._event_email_payload(record)
        except (OSError, ValueError) as error:
            QMessageBox.warning(self, "Email unavailable", str(error))
            return
        self.control_panel.email_widget.send_email(**payload)

    def send_selected_history_email(self):
        try:
            payload = self._selected_history_email()
        except (OSError, ValueError) as error:
            QMessageBox.warning(self, "Email unavailable", str(error))
            return
        self.control_panel.email_widget.send_email(**payload)

    # ---------------------------------------------------------

    def _selected_history_email(self):
        record = self.history_panel.selected_record()
        if record is None:
            raise ValueError(
                "Select a detection event before sending email."
            )
        return self._event_email_payload(record)

    def _event_email_payload(self, record):
        image_path = PROJECT_ROOT / record["evidence_path"]
        if not image_path.is_file():
            raise ValueError(f"Evidence image was not found: {image_path}")

        subject = f"Visual AI alert: {record['event_name']}"
        message = (
            "Visual AI camera detection event\n\n"
            f"Row ID: {record['rowid']}\n"
            f"Date: {record['event_date'].replace('T', ' ')}\n"
            f"Event: {record['event_name']}\n\n"
            "The event evidence image is attached."
        )
        return {
            "subject": subject,
            "message": message,
            "attachments": [image_path],
        }

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
            "Camera IP saved. Click Connect."
        )

    # ---------------------------------------------------------

    def stop_camera(self):

        if self.camera_worker is not None:
            self.camera_worker.stop()

    # ---------------------------------------------------------

    def _camera_finished(self):

        self._shutdown_timer.stop()
        self._stop_continuous_alert()
        self.camera_worker = None
        self.camera_thread = None
        self._ppe_result = None
        self._latest_frame = None

        self.statusBar().showMessage(
            "Camera Disconnected"
        )

        if self._closing:
            QTimer.singleShot(0, self.close)

    # ---------------------------------------------------------

    def closeEvent(self, event):

        self._stop_continuous_alert()
        self.ppe_service.stop()

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
        self._stop_continuous_alert()
        if self.camera_thread is not None:
            self.camera_thread.requestInterruption()
            self.camera_thread.terminate()
            self.camera_thread.wait(1000)
            self.camera_thread = None
            self.camera_worker = None

        self.close()
