from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (
    QHBoxLayout,
    QHeaderView,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
)

from .base_panel import BasePanel


class HistoryPanel(BasePanel):
    """Display persisted AI detection events and evidence links."""

    event_requested = Signal(object)
    clear_requested = Signal()
    send_email_requested = Signal()

    def __init__(self):
        super().__init__("Detection Events")

        self._build_ui()

    def _build_ui(self):

        self.table = QTableWidget()

        self.table.setColumnCount(4)

        self.table.setHorizontalHeaderLabels(
            [
                "Row ID",
                "Date",
                "Event Name",
                "Evidence Link",
            ]
        )

        header = self.table.horizontalHeader()

        header.setSectionResizeMode(QHeaderView.Stretch)

        self.table.verticalHeader().setVisible(False)

        self.table.setAlternatingRowColors(True)

        self.table.setSelectionBehavior(
            QTableWidget.SelectRows
        )

        self.table.setEditTriggers(
            QTableWidget.NoEditTriggers
        )
        self.table.cellClicked.connect(self._on_row_clicked)

        self.content_layout.addWidget(self.table)

        button_layout = QHBoxLayout()
        self.send_email_button = QPushButton(
            "Send Selected Evidence by Email"
        )
        self.send_email_button.clicked.connect(
            self.send_email_requested.emit
        )
        button_layout.addWidget(self.send_email_button)

        self.clear_button = QPushButton("Clear Events")
        self.clear_button.clicked.connect(self.clear_requested.emit)
        button_layout.addWidget(self.clear_button)
        self.content_layout.addLayout(button_layout)

    # -----------------------------------------------------

    def add_record(
        self,
        record,
        insert_at_top=True,
    ):

        row = 0 if insert_at_top else self.table.rowCount()

        self.table.insertRow(row)

        values = [
            record["rowid"],
            record["event_date"].replace("T", " ")[:19],
            record["event_name"],
            "View evidence",
        ]

        for col, value in enumerate(values):
            item = QTableWidgetItem(str(value))
            item.setData(
                Qt.ItemDataRole.UserRole,
                dict(record),
            )
            if col == 3:
                font = QFont(item.font())
                font.setUnderline(True)
                item.setFont(font)
                item.setForeground(QColor("#4da3ff"))
            self.table.setItem(row, col, item)

    def _on_row_clicked(self, row, _column):
        item = self.table.item(row, 0)
        if item is not None:
            self.event_requested.emit(
                item.data(Qt.ItemDataRole.UserRole)
            )

    def selected_record(self):
        """Return the selected detection event, if any."""
        row = self.table.currentRow()
        if row < 0:
            return None
        item = self.table.item(row, 0)
        if item is None:
            return None
        return item.data(Qt.ItemDataRole.UserRole)

    def clear(self):
        self.table.setRowCount(0)
