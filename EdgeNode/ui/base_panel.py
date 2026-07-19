from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QLabel,
    QVBoxLayout,
    QWidget,
)


class BasePanel(QFrame):
    """Reusable panel with a title and content area."""

    def __init__(self, title: str) -> None:
        super().__init__()

        self.setObjectName("BasePanel")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        self.title_label = QLabel(title)
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setObjectName("PanelTitle")

        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(5, 5, 5, 5)

        layout.addWidget(self.title_label)
        layout.addWidget(self.content_widget)

        self.setStyleSheet(
            """
            QFrame#BasePanel{
                background-color:#3A3A3A;
                border:1px solid #666666;
                border-radius:8px;
            }

            QLabel#PanelTitle{
                color:white;
                font-size:16px;
                font-weight:bold;
                padding:6px;
            }
            """
        )