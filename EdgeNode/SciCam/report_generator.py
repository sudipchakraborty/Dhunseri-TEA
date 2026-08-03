from __future__ import annotations

from datetime import datetime
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps
import numpy as np

from .app_paths import application_root
from .processing.analysis_metrics import FERMENTATION_LABELS


REPORT_DIR = application_root() / "data" / "reports"
REPORT_ASSET_DIR = application_root() / "assets" / "report"


class InspectionReportGenerator:
    """Render a branded, email-ready inspection report PNG."""

    WIDTH = 1024
    HEIGHT = 1536
    GREEN = "#075b35"
    DARK = "#17221d"
    BORDER = "#d5ddd8"
    MUTED = "#5f6964"

    def __init__(self, metrics) -> None:
        self.metrics = metrics

    @staticmethod
    def _font(size: int, bold: bool = False):
        candidates = [
            Path("C:/Windows/Fonts/seguisb.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf"),
            Path("C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf"),
        ]
        for path in candidates:
            if path.is_file():
                return ImageFont.truetype(str(path), size)
        return ImageFont.load_default()

    def _card(self, draw, box, radius=14, fill="#ffffff"):
        draw.rounded_rectangle(box, radius, fill=fill, outline=self.BORDER, width=2)

    def _fit_sample(self, path: Path, size: tuple[int, int]) -> Image.Image:
        with Image.open(path) as source:
            sample = ImageOps.exif_transpose(source).convert("RGB")
        # Saved inspection images use black outside the circular sample ROI.
        # Replace only those near-black mask pixels for a clean white report
        # background without altering the tea colours inside the sample.
        pixels = np.asarray(sample).copy()
        masked_background = np.max(pixels, axis=2) < 12
        pixels[masked_background] = 255
        sample = Image.fromarray(pixels, "RGB")
        return ImageOps.fit(sample, size, method=Image.Resampling.LANCZOS)

    @staticmethod
    def _logo(path: Path, size: tuple[int, int]) -> Image.Image:
        with Image.open(path) as source:
            logo = ImageOps.exif_transpose(source).convert("RGBA")
        logo.thumbnail(size, Image.Resampling.LANCZOS)
        return logo

    def generate(self, record: dict, image_path: Path, output_path: Path | None = None) -> Path:
        captured = datetime.fromisoformat(record["captured_at"])
        if output_path is None:
            REPORT_DIR.mkdir(parents=True, exist_ok=True)
            output_path = REPORT_DIR / f"{image_path.stem}_report.png"
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        canvas = Image.new("RGB", (self.WIDTH, self.HEIGHT), "#f7f9f7")
        draw = ImageDraw.Draw(canvas)
        title = self._font(34, True)
        h2 = self._font(25, True)
        h3 = self._font(19, True)
        body = self._font(17)
        small = self._font(14)

        # Header
        tea_logo = self._logo(REPORT_ASSET_DIR / "tea_leaf.png", (88, 88))
        canvas.paste(tea_logo, (42, 37), tea_logo)
        draw.text((151, 51), "Dhunseri Tea Quality Assessment System", font=title, fill="#063b24")
        estpl_logo = self._logo(REPORT_ASSET_DIR / "estpl.png", (105, 72))
        canvas.paste(estpl_logo, (875, 34), estpl_logo)
        draw.rounded_rectangle((792, 126, 982, 173), 10, fill="#f7fbf6", outline="#bfd0bd")
        draw.ellipse((812, 141, 830, 159), fill="#41833b")
        draw.text((842, 137), "SYSTEM READY", font=h3, fill="#2b692f")

        # Main result cards
        self._card(draw, (32, 197, 454, 701))
        self._card(draw, (480, 197, 992, 701))
        draw.text((61, 225), "Captured Sample", font=h2, fill=self.DARK)
        sample = self._fit_sample(image_path, (372, 407))
        canvas.paste(sample, (58, 268))
        # Outline the fixed circular sample ROI so pale samples remain clearly
        # separated from the white report background.
        draw.ellipse(
            (149, 404, 339, 594),
            outline="#52705f",
            width=4,
        )

        brown = float(record["brown_percentage"])
        status = record["fermentation_status"]
        draw.text((513, 238), "Brown Content", font=h2, fill=self.DARK)
        draw.text((510, 289), f"{brown:.1f}%", font=self._font(101, True), fill=self.GREEN)
        draw.line((515, 434, 957, 434), fill="#d0d5d2", width=2)
        status_upper = status.upper().replace("(", "").replace(")", "")
        status_colour = "#24703f" if "GOOD" in status_upper else "#c54132"
        status_fill = "#edf8f0" if "GOOD" in status_upper else "#fff1ee"
        draw.rounded_rectangle((513, 466, 958, 555), 10, fill=status_fill, outline=status_colour, width=2)
        draw.text((542, 492), status_upper, font=self._font(27, True), fill=status_colour)
        draw.text((514, 590), "Automated assessment based on the", font=body, fill=self.MUTED)
        draw.text((514, 620), "configured fermentation reference ranges.", font=body, fill=self.MUTED)

        # Sample details
        self._card(draw, (32, 728, 992, 943))
        draw.text((62, 758), "Test & Sample Details", font=h2, fill=self.DARK)
        test_id = f"DHTEA/{captured:%d%m%Y}/{captured:%H%M%S}"
        details = [
            ("Test ID", test_id),
            ("Sample Code", record["sample_id"]),
            ("Process Date", captured.strftime("%d %b %Y")),
            ("Test Date & Time", captured.strftime("%d %b %Y · %H:%M")),
            ("Tested By", "TeaVision Edge"),
        ]
        column_width = 184
        for index, (label, value) in enumerate(details):
            x = 54 + index * column_width
            if index:
                draw.line((x - 14, 811, x - 14, 919), fill="#d9dfdc", width=1)
            draw.text((x, 817), label, font=small, fill=self.MUTED)
            value_font = small if len(str(value)) > 20 else body
            draw.text((x, 868), str(value)[:25], font=value_font, fill=self.DARK)

        # Reference and technical cards
        self._card(draw, (32, 968, 499, 1367))
        self._card(draw, (517, 968, 992, 1367))
        draw.text((62, 998), "Fermentation Reference", font=h2, fill=self.DARK)
        fermentation = self.metrics.data["fermentation"]
        y = 1050
        marker_y = None
        for key in FERMENTATION_LABELS:
            bounds = fermentation[key]
            start, end = float(bounds["from"]), float(bounds["to"])
            fill = {
                "under_poor": "#f8c9c4", "under_moderate": "#ffe39b",
                "good": "#c8dec4", "over_moderate": "#ffe39b",
                "over_poor": "#f8c9c4",
            }[key]
            draw.rectangle((148, y, 241, y + 55), fill=fill, outline="#dc9589")
            draw.text((160, y + 15), f"{start:g}–{end:g}", font=body, fill=self.DARK)
            draw.text((261, y + 15), FERMENTATION_LABELS[key], font=small, fill=self.DARK)
            if start <= round(brown) <= end:
                marker_y = y + 27
            y += 59
        if marker_y is not None:
            draw.rounded_rectangle((48, marker_y - 18, 126, marker_y + 18), 5, fill="#cf3f2c")
            draw.text((61, marker_y - 13), f"{brown:.1f}", font=body, fill="white")
            draw.polygon((126, marker_y - 7, 138, marker_y, 126, marker_y + 7), fill="#cf3f2c")

        draw.text((547, 998), "Technical Analysis", font=h2, fill=self.DARK)
        rgb = record.get("average_rgb", (0, 0, 0))
        lab = record.get("average_lab", (0.0, 0.0, 0.0))
        rows = [
            ("Average RGB", f"({rgb[0]}, {rgb[1]}, {rgb[2]})"),
            ("Average LAB", f"({lab[0]:.1f}, {lab[1]:.1f}, {lab[2]:.1f})"),
            ("Brightness", f"{float(record.get('brightness', 0.0)):.1f}"),
            ("Confidence", f"{float(record['confidence']):.1f}%"),
            ("Processing Time", f"{float(record['processing_ms']):.1f} ms"),
        ]
        y = 1060
        for label, value in rows:
            draw.rounded_rectangle((540, y, 967, y + 55), 5, fill="#fbfcfb", outline="#dce2df")
            draw.text((560, y + 16), label, font=body, fill=self.DARK)
            draw.text((786, y + 16), value, font=body, fill=self.DARK)
            y += 59

        # Footer
        self._card(draw, (32, 1392, 992, 1504))
        draw.text((61, 1407), "Powered by", font=small, fill=self.MUTED)
        elva_logo = self._logo(REPORT_ASSET_DIR / "elva.png", (175, 77))
        canvas.paste(elva_logo, (58, 1423), elva_logo)
        draw.text((472, 1423), "Captured colour is assessed against the configured", font=body, fill=self.DARK)
        draw.text((472, 1453), "reference range. — Team ESTPL", font=body, fill=self.DARK)

        canvas.save(output_path, "PNG", optimize=True)
        return output_path
