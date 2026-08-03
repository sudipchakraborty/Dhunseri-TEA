from pathlib import Path
import tempfile
import unittest

from SciCam.processing.analysis_metrics import AnalysisMetrics


class AnalysisMetricsTests(unittest.TestCase):
    def test_default_fermentation_ranges(self):
        metrics = AnalysisMetrics(
            Path(__file__).parents[1] / "config" / "analysis_metrics.json"
        )

        cases = {
            81.49: "Under Fermented (Poor)",
            81.5: "Under Fermented (Moderate)",
            82.0: "Under Fermented (Moderate)",
            84.49: "Under Fermented (Moderate)",
            85.0: "Good Fermentation",
            87.49: "Good Fermentation",
            88.0: "Over Fermented (Moderate)",
            90.0: "Over Fermented (Moderate)",
            90.49: "Over Fermented (Moderate)",
            90.5: "Over Fermented (Poor)",
        }
        for value, expected in cases.items():
            with self.subTest(value=value):
                self.assertEqual(
                    metrics.classify_fermentation(value),
                    expected,
                )

    def test_old_configuration_is_migrated(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "metrics.json"
            path.write_text(
                '{"fermentation":{"under_fermented_max":40,'
                '"perfect_max":60},"tea_quality":{"poor_max":30,'
                '"moderate_max":50,"good_max":75}}',
                encoding="utf-8",
            )

            metrics = AnalysisMetrics(path)

            self.assertNotIn("tea_quality", metrics.data)
            self.assertEqual(
                metrics.data["fermentation"]["good"]["from"],
                85.0,
            )


if __name__ == "__main__":
    unittest.main()
