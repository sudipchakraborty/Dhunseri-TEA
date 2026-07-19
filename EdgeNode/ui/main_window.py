from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
)

from app.ui.control_panel import ControlPanel
from app.ui.image_panel import ImagePanel
from app.ui.result_panel import ResultPanel
from app.ui.history_table import HistoryTable
from app.ui.toolbar import ToolBar


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("TEA QUALITY ANALYZER")

        self.resize(1600,900)

        central = QWidget()

        self.setCentralWidget(central)

        main_layout = QVBoxLayout(central)

        top_layout = QHBoxLayout()

        self.control_panel = ControlPanel()

        self.image_panel = ImagePanel()

        self.result_panel = ResultPanel()

        top_layout.addWidget(self.control_panel,1)

        top_layout.addWidget(self.image_panel,3)

        top_layout.addWidget(self.result_panel,1)

        self.toolbar = ToolBar()

        self.history = HistoryTable()

        main_layout.addLayout(top_layout)

        main_layout.addWidget(self.toolbar)

        main_layout.addWidget(self.history)