from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QLabel,
    QHBoxLayout,
    QMainWindow,
    QVBoxLayout,
    QWidget,
)


class MainWindow(QMainWindow):
    """Main application window."""

    def __init__(self) -> None:
        super().__init__()

        self._configure_window()
        self._build_ui()

    def _configure_window(self) -> None:
        self.setWindowTitle(
            "TeaVision Edge - Industrial Tea Fermentation Analysis System"
        )

        self.resize(1400, 900)
        self.setMinimumSize(1200, 700)

    def _build_ui(self) -> None:
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(10)

        title = QLabel("TeaVision Edge")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet(
            """
            font-size:28px;
            font-weight:bold;
            padding:10px;
            """
        )

        main_layout.addWidget(title)

        content_layout = QHBoxLayout()
        content_layout.setSpacing(10)

        left = self._create_panel("Camera Settings")
        center = self._create_panel("Inspection Area")
        right = self._create_panel("Analysis Result")

        content_layout.addWidget(left, 1)
        content_layout.addWidget(center, 3)
        content_layout.addWidget(right, 1)

        main_layout.addLayout(content_layout)

        history = self._create_panel("History Table")
        history.setFixedHeight(180)

        main_layout.addWidget(history)

        self.statusBar().showMessage("Ready")

    def _create_panel(self, title: str) -> QWidget:
        panel = QWidget()

        panel.setStyleSheet(
            """
            QWidget{
                border:1px solid #666666;
                border-radius:8px;
                background:#3A3A3A;
            }
            """
        )

        layout = QVBoxLayout(panel)

        label = QLabel(title)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        label.setStyleSheet(
            """
            font-size:16px;
            font-weight:bold;
            padding:8px;
            color:white;
            """
        )

        layout.addWidget(label)
        layout.addStretch()

        return panel