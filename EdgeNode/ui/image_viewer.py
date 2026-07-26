from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QLabel, QSizePolicy, QVBoxLayout, QWidget

class ImageViewer(QWidget):
    """
    Reusable image viewer widget.

    Version 1:
    - Displays a pixmap
    - Shows a placeholder when no image is available
    - Automatically scales with the window
    """

    def __init__(self, placeholder: str = "No Image") -> None:
        super().__init__()

        self._pixmap: QPixmap | None = None

        self.image_label = QLabel(placeholder)
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Expanding,
        )
        self.image_label.setMinimumSize(200, 150)
        self.image_label.setStyleSheet("""
            QLabel{
                background:#1f1f1f;
                border:1px solid #555;
                border-radius:6px;
                color:#aaaaaa;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.addWidget(self.image_label)

    def set_pixmap(self, pixmap: QPixmap) -> None:
        """Display a pixmap."""

        self._pixmap = pixmap
        self._update_pixmap()

    def clear(self) -> None:
        """Clear the viewer."""

        self._pixmap = None
        self.image_label.setPixmap(QPixmap())
        self.image_label.setText("No Image")

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._update_pixmap()

    def _update_pixmap(self) -> None:
        if self._pixmap is None:
            return

        scaled = self._pixmap.scaled(
            self.image_label.size(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation,
        )

        self.image_label.setText("")
        self.image_label.setPixmap(scaled)
        
    def set_image(self, image):

        pixmap = QPixmap.fromImage(image)

        self.set_pixmap(pixmap)
