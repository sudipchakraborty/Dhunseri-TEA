from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QFileDialog,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from .image_viewer import ImageViewer


class CapturedImagePanel(QWidget):
    image_selected = Signal(str)
    previous_requested = Signal()
    next_requested = Signal()

    def __init__(self) -> None:
        super().__init__()
        self._last_folder = (
            r"C:\Users\sudip\OneDrive\ESTPL\PROJECTS\DHUNSERI-TEA"
            r"\Captured Image"
        )
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(8)

        top = QHBoxLayout()
        self.browse_button = QPushButton("Browse Captured Image")
        self.previous_button = QPushButton("< Previous")
        self.next_button = QPushButton("Next >")
        self.path_label = QLabel("No captured image selected")
        self.path_label.setWordWrap(True)
        top.addWidget(self.browse_button)
        top.addWidget(self.path_label, 1)
        layout.addLayout(top)

        self.result_label = QLabel("Brown content: --")
        self.result_label.setStyleSheet(
            "font-size: 18pt; font-weight: bold; color: #ff3030;"
        )
        self.roi_label = QLabel("ROI: --")
        layout.addWidget(self.result_label)
        layout.addWidget(self.roi_label)

        grid = QGridLayout()
        self.original_viewer = ImageViewer("Captured Image")
        self.roi_viewer = ImageViewer("Selected ROI")
        grid.addWidget(self.original_viewer, 0, 0)
        grid.addWidget(self.roi_viewer, 0, 1)
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)
        layout.addLayout(grid, 1)

        nav = QHBoxLayout()
        nav.addStretch()
        nav.addWidget(self.previous_button)
        nav.addWidget(self.next_button)
        nav.addStretch()
        layout.addLayout(nav)

        self.browse_button.clicked.connect(self._browse)
        self.previous_button.clicked.connect(self.previous_requested.emit)
        self.next_button.clicked.connect(self.next_requested.emit)

    def _browse(self) -> None:
        file_path, _selected = QFileDialog.getOpenFileName(
            self,
            "Select Captured Tea Image",
            self._last_folder,
            "Images (*.png *.jpg *.jpeg *.bmp *.tif *.tiff);;All Files (*)",
        )
        if not file_path:
            return
        self._last_folder = str(Path(file_path).parent)
        self.image_selected.emit(file_path)

    def set_path(self, path: str) -> None:
        self.path_label.setText(Path(path).name)
        self.path_label.setToolTip(path)

    def set_result(self, percentage: float, confidence: float, roi_text: str) -> None:
        self.result_label.setText(
            f"Brown content: {percentage:.2f}%   Confidence: {confidence:.1f}%"
        )
        self.roi_label.setText(f"ROI: {roi_text}")
