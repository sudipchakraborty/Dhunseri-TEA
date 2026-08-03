from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import (
    QFormLayout,
    QFrame,
    QLabel,
    QLCDNumber,
    QVBoxLayout,
)

from .base_panel import BasePanel
from SciCam.processing.processing_result import ProcessingResult


class ResultPanel(BasePanel):
    """
    Analysis Result Panel

    Displays all inspection information generated
    by FrameProcessor.
    """

    def __init__(self):
        super().__init__("Analysis Result")

        self._build_ui()

    # --------------------------------------------------------

    def _build_ui(self):

        self.title_label.setText("ANALYSIS RESULT")
        self.title_label.setFixedHeight(52)

        brown_caption = QLabel("BROWN CONTENT")
        brown_caption.setStyleSheet(
            """
            color: white;
            background-color: #555555;
            font-size: 11pt;
            font-weight: bold;
            padding: 3px 6px;
            """
        )
        brown_caption.setAlignment(Qt.AlignmentFlag.AlignLeft)

        self.brown_display = QLCDNumber()
        # Whole percentage only. QLCDNumber right-aligns values within the
        # available digit positions, keeping the readout near the percent sign.
        self.brown_display.setDigitCount(3)
        self.brown_display.setSegmentStyle(
            QLCDNumber.SegmentStyle.Flat
        )
        self.brown_display.setFixedHeight(135)
        self.brown_display.display("0")
        self.brown_display.setStyleSheet(
            """
            QLCDNumber {
                background-color: #120000;
                color: #ff2020;
                border: none;
            }
            """
        )

        palette = self.brown_display.palette()
        palette.setColor(QPalette.ColorRole.WindowText, QColor("#ff2020"))
        palette.setColor(QPalette.ColorRole.Light, QColor("#ff2020"))
        palette.setColor(QPalette.ColorRole.Dark, QColor("#5a0000"))
        self.brown_display.setPalette(palette)

        percent_label = QLabel("%")
        percent_label.setAlignment(
            Qt.AlignmentFlag.AlignRight
            | Qt.AlignmentFlag.AlignBottom
        )
        percent_label.setFixedHeight(44)
        percent_label.setContentsMargins(0, 8, 8, 0)
        percent_label.setStyleSheet(
            "color: #ff3030; font-size: 25pt; font-weight: bold;"
        )

        self.lbl_fermentation = QLabel("Fermentation: Stabilizing")
        self.lbl_fermentation.setStyleSheet(
            "color: white; font-size: 15pt; font-weight: bold;"
        )
        self.lbl_fermentation.setMinimumHeight(36)

        display_frame = QFrame()
        display_frame.setObjectName("BrownDisplayFrame")
        display_frame.setStyleSheet(
            """
            QFrame#BrownDisplayFrame {
                background-color: #120000;
                border: 2px solid #a52323;
                border-radius: 8px;
            }
            QFrame#BrownDisplayFrame QLabel {
                border: none;
                background: transparent;
            }
            """
        )

        display_layout = QVBoxLayout(display_frame)
        display_layout.setContentsMargins(14, 12, 14, 14)
        display_layout.setSpacing(5)
        display_layout.addWidget(
            brown_caption,
            0,
            Qt.AlignmentFlag.AlignLeft,
        )
        display_layout.addWidget(self.brown_display)
        display_layout.addWidget(percent_label)
        display_layout.addSpacing(8)
        display_layout.addWidget(self.lbl_fermentation)

        self.content_layout.addWidget(display_frame)

        layout = QFormLayout()

        self.lbl_brown = QLabel("0.00 %")
        self.lbl_status = QLabel("READY")
        self.lbl_rgb = QLabel("(0, 0, 0)")
        self.lbl_lab = QLabel("(0.0, 0.0, 0.0)")
        self.lbl_brightness = QLabel("0.0")
        self.lbl_confidence = QLabel("0.0 %")
        self.lbl_processing = QLabel("0.0 ms")

        labels = [
            self.lbl_brown,
            self.lbl_status,
            self.lbl_rgb,
            self.lbl_lab,
            self.lbl_brightness,
            self.lbl_confidence,
            self.lbl_processing,
        ]

        for label in labels:
            label.setAlignment(Qt.AlignCenter)

        layout.addRow("Status", self.lbl_status)
        layout.addRow("Average RGB", self.lbl_rgb)
        layout.addRow("Average LAB", self.lbl_lab)
        layout.addRow("Brightness", self.lbl_brightness)
        layout.addRow("Confidence", self.lbl_confidence)
        layout.addRow("Processing", self.lbl_processing)

        self.content_layout.addLayout(layout)

    # --------------------------------------------------------
    # Public API
    # --------------------------------------------------------

    def update_results(
        self,
        result: ProcessingResult,
    ):

        self.lbl_brown.setText(
            f"{result.brown_percentage:.0f} %"
        )
        self.brown_display.display(
            f"{result.brown_percentage:.0f}"
        )

        self.lbl_status.setText(
            result.status
        )
        self.lbl_fermentation.setText(
            f"Fermentation: {result.fermentation_status}"
        )
        self.lbl_rgb.setText(
            f"({result.average_rgb[0]}, "
            f"{result.average_rgb[1]}, "
            f"{result.average_rgb[2]})"
        )

        self.lbl_lab.setText(
            f"({result.average_lab[0]:.1f}, "
            f"{result.average_lab[1]:.1f}, "
            f"{result.average_lab[2]:.1f})"
        )

        self.lbl_brightness.setText(
            f"{result.brightness:.1f}"
        )

        self.lbl_confidence.setText(
            f"{result.confidence:.1f} %"
        )

        self.lbl_processing.setText(
            f"{result.processing_ms:.1f} ms"
        )

    # --------------------------------------------------------

    def clear(self):

        self.lbl_brown.setText("0 %")
        self.brown_display.display("0")
        self.lbl_status.setText("READY")
        self.lbl_fermentation.setText("Fermentation: Waiting")
        self.lbl_rgb.setText("(0, 0, 0)")
        self.lbl_lab.setText("(0.0, 0.0, 0.0)")
        self.lbl_brightness.setText("0.0")
        self.lbl_confidence.setText("0.0 %")
        self.lbl_processing.setText("0.0 ms")
