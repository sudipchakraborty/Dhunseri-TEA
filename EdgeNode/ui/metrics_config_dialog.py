from __future__ import annotations

from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QMessageBox,
    QVBoxLayout,
)

from SciCam.processing.analysis_metrics import AnalysisMetrics


class MetricsConfigDialog(QDialog):
    """Editor for fermentation and tea-quality brown-value limits."""

    def __init__(self, metrics: AnalysisMetrics, parent=None) -> None:
        super().__init__(parent)
        self.metrics = metrics
        self.setWindowTitle("Configure Analysis Metrics")
        self.setMinimumWidth(440)

        layout = QVBoxLayout(self)
        fermentation_group = QGroupBox("Fermentation thresholds")
        fermentation_form = QFormLayout(fermentation_group)
        quality_group = QGroupBox("Tea quality thresholds")
        quality_form = QFormLayout(quality_group)

        fermentation = metrics.data["fermentation"]
        quality = metrics.data["tea_quality"]

        self.under_max = self._spin(
            fermentation["under_fermented_max"]
        )
        self.perfect_max = self._spin(fermentation["perfect_max"])
        self.poor_max = self._spin(quality["poor_max"])
        self.moderate_max = self._spin(quality["moderate_max"])
        self.good_max = self._spin(quality["good_max"])

        fermentation_form.addRow(
            "Under Fermented: 0 to",
            self.under_max,
        )
        fermentation_form.addRow(
            "Perfect: above previous to",
            self.perfect_max,
        )
        quality_form.addRow("Poor Quality: 0 to", self.poor_max)
        quality_form.addRow(
            "Moderate Quality: above previous to",
            self.moderate_max,
        )
        quality_form.addRow(
            "Good: above previous to",
            self.good_max,
        )

        layout.addWidget(fermentation_group)
        layout.addWidget(quality_group)

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
        spin.setDecimals(2)
        spin.setSuffix(" %")
        spin.setValue(float(value))
        return spin

    def _save(self) -> None:
        data = {
            "fermentation": {
                "under_fermented_max": self.under_max.value(),
                "perfect_max": self.perfect_max.value(),
            },
            "tea_quality": {
                "poor_max": self.poor_max.value(),
                "moderate_max": self.moderate_max.value(),
                "good_max": self.good_max.value(),
            },
        }
        try:
            self.metrics.save(data)
        except (KeyError, TypeError, ValueError) as error:
            QMessageBox.warning(self, "Invalid thresholds", str(error))
            return
        self.accept()

