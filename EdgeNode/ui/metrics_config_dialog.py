from __future__ import annotations

from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QVBoxLayout,
)

from SciCam.processing.analysis_metrics import AnalysisMetrics


class MetricsConfigDialog(QDialog):
    """Editor for the five fermentation classification ranges."""

    def __init__(self, metrics: AnalysisMetrics, parent=None) -> None:
        super().__init__(parent)
        self.metrics = metrics
        self.setWindowTitle("Configure Analysis Metrics")
        self.setMinimumWidth(440)

        layout = QVBoxLayout(self)
        fermentation_group = QGroupBox("Fermentation index settings")
        fermentation_form = QFormLayout(fermentation_group)

        fermentation = metrics.data["fermentation"]

        self.range_inputs = {}
        labels = {
            "under_poor": "Under Fermented (Poor)",
            "under_moderate": "Under Fermented (Moderate)",
            "good": "Good Fermentation",
            "over_moderate": "Over Fermented (Moderate)",
            "over_poor": "Over Fermented (Poor)",
        }
        for key, label in labels.items():
            range_data = fermentation[key]
            from_spin = self._spin(range_data["from"])
            to_spin = self._spin(range_data["to"])
            range_layout = QHBoxLayout()
            range_layout.addWidget(QLabel("From"))
            range_layout.addWidget(from_spin)
            range_layout.addWidget(QLabel("To"))
            range_layout.addWidget(to_spin)
            fermentation_form.addRow(label, range_layout)
            self.range_inputs[key] = (from_spin, to_spin)

        layout.addWidget(fermentation_group)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    @staticmethod
    def _spin(value: float) -> QDoubleSpinBox:
        spin = QDoubleSpinBox()
        spin.setRange(0.0, 100.0)
        spin.setDecimals(0)
        spin.setSuffix(" %")
        spin.setValue(float(value))
        return spin

    def _save(self) -> None:
        data = {
            "fermentation": {
                key: {
                    "from": controls[0].value(),
                    "to": controls[1].value(),
                }
                for key, controls in self.range_inputs.items()
            },
        }
        try:
            self.metrics.save(data)
        except (KeyError, TypeError, ValueError) as error:
            QMessageBox.warning(self, "Invalid thresholds", str(error))
            return
        self.accept()
