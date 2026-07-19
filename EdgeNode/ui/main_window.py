from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QMainWindow,
    QVBoxLayout,
    QWidget,
)

from .base_panel import BasePanel
from .status_bar import StatusBar


class MainWindow(QMainWindow):
    """Main application window."""

    def __init__(self) -> None:
        super().__init__()

        self._configure_window()
        self._build_ui()

    def _configure_window(self) -> None:
        """Configure the main window."""

        self.setWindowTitle(
            "TeaVision Edge - Industrial Tea Fermentation Analysis System"
        )

        self.resize(1400, 900)
        self.setMinimumSize(1200, 700)

    def _build_ui(self) -> None:
        """Build the user interface."""

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(10)

        # -----------------------------
        # Main Content
        # -----------------------------
        content_layout = QHBoxLayout()
        content_layout.setSpacing(10)

        self.left_panel = BasePanel("Camera Settings")
        self.center_panel = BasePanel("Inspection Area")
        self.right_panel = BasePanel("Analysis Result")

        content_layout.addWidget(self.left_panel, 1)
        content_layout.addWidget(self.center_panel, 3)
        content_layout.addWidget(self.right_panel, 1)

        main_layout.addLayout(content_layout)

        # -----------------------------
        # History Panel
        # -----------------------------
        self.history_panel = BasePanel("History Table")
        self.history_panel.setFixedHeight(180)

        main_layout.addWidget(self.history_panel)

        # -----------------------------
        # Status Bar
        # -----------------------------
        self.app_status_bar = StatusBar()
        self.setStatusBar(self.app_status_bar)

