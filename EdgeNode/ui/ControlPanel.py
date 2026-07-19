from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QSlider
)

from PySide6.QtCore import Qt


class ControlPanel(QWidget):

    def __init__(self):

        super().__init__()

        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("Camera Settings"))

        for text in [
            "Exposure",
            "Gain",
            "Brightness",
            "Contrast",
            "Saturation",
            "Gamma"
        ]:

            layout.addWidget(QLabel(text))

            slider = QSlider(Qt.Horizontal)

            layout.addWidget(slider)

        layout.addStretch()
        