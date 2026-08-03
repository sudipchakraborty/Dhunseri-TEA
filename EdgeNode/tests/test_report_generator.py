from datetime import datetime

from PIL import Image, ImageDraw

from SciCam.inspection_history import InspectionHistoryStore
from SciCam.processing.analysis_metrics import AnalysisMetrics
from SciCam.report_generator import InspectionReportGenerator


def test_report_contains_dynamic_record_data(tmp_path):
    image_path = tmp_path / "sample.png"
    sample = Image.new("RGB", (320, 240), "black")
    ImageDraw.Draw(sample).ellipse((60, 20, 260, 220), fill=(175, 92, 28))
    sample.save(image_path)
    record = {
        "captured_at": datetime(2026, 8, 3, 20, 49).isoformat(),
        "sample_id": "HAF20223",
        "brown_percentage": 86.4,
        "fermentation_status": "Good Fermentation",
        "tea_quality": "",
        "confidence": 100.0,
        "processing_ms": 42.6,
        "image_path": image_path.name,
        "average_rgb": (181, 96, 31),
        "average_lab": (112.4, 151.2, 172.8),
        "brightness": 103.5,
    }
    output = tmp_path / "report.png"

    InspectionReportGenerator(AnalysisMetrics()).generate(
        record, image_path, output
    )

    with Image.open(output) as report:
        assert report.size == (1024, 1536)
        assert report.format == "PNG"
        assert report.getpixel((60, 270)) == (255, 255, 255)


def test_history_round_trips_report_metrics(tmp_path):
    store = InspectionHistoryStore(tmp_path / "history.db")
    record = {
        "captured_at": "2026-08-03T20:49:00",
        "sample_id": "HAF20223",
        "brown_percentage": 86.4,
        "fermentation_status": "Good Fermentation",
        "tea_quality": "",
        "confidence": 100.0,
        "processing_ms": 42.6,
        "image_path": "sample.png",
        "average_rgb": (181, 96, 31),
        "average_lab": (112.4, 151.2, 172.8),
        "brightness": 103.5,
    }

    store.add(record)
    loaded = store.all_newest_first()[0]

    assert loaded["average_rgb"] == record["average_rgb"]
    assert loaded["average_lab"] == record["average_lab"]
    assert loaded["brightness"] == record["brightness"]
