from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QHeaderView, QTableWidget, QTableWidgetItem

from .base_panel import BasePanel


class HistoryPanel(BasePanel):
    """Displays persisted tea inspection history and report links."""

    image_requested = Signal(str, str)

    def __init__(self):
        super().__init__("Inspection History")
        self._build_ui()

    def _build_ui(self):
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels(
            [
                "Time", "Sample ID", "Brown %", "Fermentation",
                "Tea Quality", "Confidence", "Process (ms)", "Image",
            ]
        )
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.cellClicked.connect(self._on_row_clicked)
        self.content_layout.addWidget(self.table)

    def add_record(self, record, insert_at_top=True):
        row = 0 if insert_at_top else self.table.rowCount()
        self.table.insertRow(row)
        values = [
            record["captured_at"].replace("T", " ")[:19],
            record["sample_id"],
            f'{record["brown_percentage"]:.2f}',
            record["fermentation_status"],
            record["tea_quality"],
            f'{record["confidence"]:.2f}',
            f'{record["processing_ms"]:.2f}',
            record["image_path"].split("/")[-1],
        ]
        for column, value in enumerate(values):
            item = QTableWidgetItem(str(value))
            item.setData(Qt.ItemDataRole.UserRole, record["image_path"])
            item.setData(Qt.ItemDataRole.UserRole + 1, dict(record))
            self.table.setItem(row, column, item)

    def _on_row_clicked(self, row, _column):
        item = self.table.item(row, 0)
        sample_item = self.table.item(row, 1)
        if item is not None and sample_item is not None:
            self.image_requested.emit(
                item.data(Qt.ItemDataRole.UserRole), sample_item.text()
            )

    def selected_record(self):
        """Return the selected inspection record, if any."""
        row = self.table.currentRow()
        if row < 0:
            return None
        item = self.table.item(row, 0)
        if item is None:
            return None
        return item.data(Qt.ItemDataRole.UserRole + 1)
