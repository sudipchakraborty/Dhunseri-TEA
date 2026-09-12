from pathlib import Path

from PySide6.QtCore import Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QFileDialog,
    QGridLayout,
    QHBoxLayout,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from .base_panel import BasePanel
from .image_viewer import ImageViewer


class InspectionPanel(BasePanel):
    """
    Displays inspection images.
    """

    correction_requested = Signal(str)
    cancel_correction_requested = Signal()
    reference_changed = Signal(str)
    reference_clear_requested = Signal()

    def __init__(self):
        super().__init__("Inspection Area")

        self._build_ui()

    def _build_ui(self):

        layout = QGridLayout()

        self.original_viewer = ImageViewer("Original")
        self.white_balance_viewer = ImageViewer("Adjusted Colour")
        self.reference_viewer = ImageViewer("Reference Image")
        self.select_reference_button = QPushButton(
            "Select Reference Image"
        )
        self.correction_button = QPushButton("Correction")
        self.cancel_correction_button = QPushButton("Cancel Correction")
        self.clear_reference_button = QPushButton("Clear Reference Image")
        self.correction_button.setEnabled(False)
        self.cancel_correction_button.setEnabled(False)
        self.clear_reference_button.setEnabled(False)
        self.select_reference_button.clicked.connect(
            self.select_reference_image
        )
        self.correction_button.clicked.connect(
            lambda: self.correction_requested.emit(
                str(self._reference_image_path)
            )
        )
        self.cancel_correction_button.clicked.connect(
            self.cancel_correction_requested.emit
        )
        self.clear_reference_button.clicked.connect(
            self.clear_reference_image
        )
        self._reference_image_path = None
        self.mask_viewer = ImageViewer("Brown Mask")
        self.histogram_viewer = ImageViewer("Histogram")

        corrected_panel = QWidget()
        corrected_layout = QVBoxLayout(corrected_panel)
        corrected_layout.setContentsMargins(0, 0, 0, 0)
        corrected_layout.setSpacing(5)
        corrected_layout.addWidget(self.white_balance_viewer, 1)

        reference_panel = QWidget()
        reference_layout = QVBoxLayout(reference_panel)
        reference_layout.setContentsMargins(0, 0, 0, 0)
        reference_layout.setSpacing(5)
        reference_layout.addWidget(self.reference_viewer, 1)
        reference_layout.addWidget(self.select_reference_button)
        reference_layout.addWidget(self.correction_button)
        reference_layout.addWidget(self.cancel_correction_button)
        reference_layout.addWidget(self.clear_reference_button)

        # Original and selected real-colour reference share the left column;
        # the adjusted preview remains the large comparison view on the right.
        layout.addWidget(self.original_viewer, 0, 0)
        layout.addWidget(reference_panel, 1, 0)
        layout.addWidget(corrected_panel, 0, 1, 2, 1)
        layout.setColumnStretch(0, 1)
        layout.setColumnStretch(1, 2)
        layout.setRowStretch(0, 1)
        layout.setRowStretch(1, 1)

        self.content_layout.addLayout(layout)

    # -------------------------------------------------

    def set_original_image(self, image):
        self.original_viewer.set_image(image)

    def set_white_balance_image(self, image):
        self.white_balance_viewer.set_image(image)

    def set_correction_active(self, active):
        self.cancel_correction_button.setEnabled(active)

    def set_mask_image(self, image):
        self.mask_viewer.set_image(image)

    def set_histogram_image(self, image):
        self.histogram_viewer.set_image(image)

    def select_reference_image(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Real-Colour Reference Image",
            "",
            "Images (*.png *.jpg *.jpeg *.bmp *.tif *.tiff)",
        )
        if not file_path:
            return
        if self.load_reference_image(file_path):
            self.reference_changed.emit(file_path)

    def load_reference_image(self, file_path):
        path = Path(file_path) if file_path else None
        if path is None or not path.is_file():
            self._clear_reference_controls()
            if path is not None:
                self.select_reference_button.setToolTip(
                    f"Reference image not found: {path}"
                )
            return False
        pixmap = QPixmap(str(path))
        if pixmap.isNull():
            self._clear_reference_controls()
            self.select_reference_button.setToolTip(
                "The selected image could not be loaded."
            )
            return False
        self.reference_viewer.set_pixmap(pixmap)
        self._reference_image_path = path
        self.correction_button.setEnabled(True)
        self.clear_reference_button.setEnabled(True)
        self.select_reference_button.setToolTip(str(path))
        return True

    def clear_reference_image(self):
        self._clear_reference_controls()
        self.reference_clear_requested.emit()

    def _clear_reference_controls(self):
        self.reference_viewer.clear()
        self._reference_image_path = None
        self.correction_button.setEnabled(False)
        self.cancel_correction_button.setEnabled(False)
        self.clear_reference_button.setEnabled(False)
        self.select_reference_button.setToolTip("")

    @property
    def reference_image_path(self):
        return self._reference_image_path
