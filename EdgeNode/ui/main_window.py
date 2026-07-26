from datetime import datetime
import re

import cv2

from PySide6.QtCore import Qt, QThread, QTimer
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QMainWindow,
    QMessageBox,
    QVBoxLayout,
    QWidget,
)

from SciCam.camera_worker import CameraWorker
from SciCam.camera_settings import CameraSettings
from SciCam.frame_converter import FrameConverter
from SciCam.inspection_history import (
    DEFAULT_IMAGE_DIR,
    PROJECT_ROOT,
    InspectionHistoryStore,
)
from SciCam.processing.frame_processor import FrameProcessor

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

        self.frame_processor = FrameProcessor()
        self.camera_settings = CameraSettings()
        self.history_store = InspectionHistoryStore()

        # Store latest inspection result
        self.last_result = None

        self._configure_window()
        self._build_ui()
        self._connect_signals()
        self._load_history()

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
            self.camera_settings.rtsp_url
        )
        self.control_panel.set_rtsp_camera(
            self.camera_settings.rtsp_ip,
            self.camera_settings.rtsp_url,
        )
        self.inspection_panel = InspectionPanel()
        self.result_panel = ResultPanel()

        content_layout.addWidget(self.control_panel, 1)
        content_layout.addWidget(self.inspection_panel, 3)
        content_layout.addWidget(self.result_panel, 1)

        main_layout.addLayout(content_layout)

        self.history_panel = HistoryPanel()
        self.history_panel.setFixedHeight(220)

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

        self.control_panel.save_requested.connect(
            self.save_inspection
        )

        self.control_panel.close_requested.connect(
            self.close
        )

        self.control_panel.averaging_window_changed.connect(
            self.frame_processor.set_averaging_window
        )

        self.control_panel.config_requested.connect(
            self.configure_metrics
        )

        self.history_panel.image_requested.connect(
            self.show_history_image
        )

        self.control_panel.rtsp_ip_save_requested.connect(
            self.save_rtsp_ip
        )

    # ---------------------------------------------------------

    def start_camera(self, source):

        if self.camera_thread is not None:
            return

        self.frame_processor.reset_average()
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

            result = self.frame_processor.process(frame)

            # Store latest inspection
            self.last_result = result

            self.inspection_panel.set_original_image(
                FrameConverter.to_qimage(result.original)
            )

            self.inspection_panel.set_white_balance_image(
                FrameConverter.to_qimage(result.white_balance)
            )

            self.inspection_panel.set_mask_image(
                FrameConverter.to_qimage(result.brown_mask)
            )

            if result.histogram_image is not None:

                self.inspection_panel.set_histogram_image(
                    FrameConverter.to_qimage(
                        result.histogram_image
                    )
                )

            self.result_panel.update_results(result)

        except Exception as ex:

            self.statusBar().showMessage(
                f"Processing Error : {ex}"
            )

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
            self.frame_processor.brown_average.sample_count
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
        pixmap = QPixmap(str(path))
        if pixmap.isNull():
            QMessageBox.warning(
                self,
                "Image unavailable",
                f"Saved image was not found:\n{path}",
            )
            return

        dialog = QDialog(self)
        dialog.setWindowTitle(f"Saved Sample: {sample_id}")
        dialog.resize(800, 600)
        layout = QVBoxLayout(dialog)
        image_label = QLabel()
        image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        image_label.setPixmap(
            pixmap.scaled(
                760,
                540,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        )
        layout.addWidget(image_label)
        dialog.exec()

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

    # ---------------------------------------------------------

    def stop_camera(self):

        if self.camera_worker is not None:
            self.camera_worker.stop()

    # ---------------------------------------------------------

    def _camera_finished(self):

        self._shutdown_timer.stop()
        self.frame_processor.reset_average()
        self.camera_worker = None
        self.camera_thread = None

        self.statusBar().showMessage(
            "Camera Disconnected"
        )

        if self._closing:
            QTimer.singleShot(0, self.close)

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
