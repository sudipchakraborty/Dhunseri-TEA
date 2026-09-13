from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from SciCam.processing.brown_detector import BrownCalibration  # noqa: E402
from SciCam.processing.sample_roi import CircularSampleROI  # noqa: E402


IMAGE_EXTENSIONS = {".bmp", ".jpeg", ".jpg", ".png", ".tif", ".tiff"}


def label_from_name(path: Path) -> float | None:
    match = re.search(r"(\d+(?:\.\d+)?)\s*percent", path.stem, re.I)
    if not match:
        return None
    return float(match.group(1))


def labelled_images_from_folder(folder: Path):
    for path in sorted(folder.rglob("*")):
        if path.suffix.lower() not in IMAGE_EXTENSIONS:
            continue
        label = label_from_name(path)
        if label is not None:
            yield path, label


def labelled_images_from_csv(csv_path: Path):
    with csv_path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        for row in reader:
            image_path = Path(row["image_path"])
            if not image_path.is_absolute():
                image_path = csv_path.parent / image_path
            yield image_path, float(row["brown_percentage"])


def piecewise_predictions(
    features: list[float],
    labels: list[float],
) -> np.ndarray:
    order = np.argsort(features)
    sorted_features = np.array(features, dtype=np.float64)[order]
    sorted_labels = np.array(labels, dtype=np.float64)[order]
    return np.interp(features, sorted_features, sorted_labels)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Fit TeaVision brown-percentage calibration.",
    )
    parser.add_argument(
        "input",
        type=Path,
        help=(
            "Folder with images named like 85percent.jpg, or a CSV with "
            "image_path,brown_percentage columns."
        ),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(__file__).resolve().parents[1]
        / "config"
        / "brown_calibration.json",
    )
    args = parser.parse_args()

    if args.input.suffix.lower() == ".csv":
        labelled = list(labelled_images_from_csv(args.input))
    else:
        labelled = list(labelled_images_from_folder(args.input))

    if len(labelled) < 3:
        raise SystemExit(
            "Need at least 3 labelled images to fit calibration."
        )

    roi = CircularSampleROI()
    calibration = BrownCalibration(args.output)
    features = []
    labels = []
    samples = []
    for image_path, label in labelled:
        image = cv2.imread(str(image_path))
        if image is None:
            raise SystemExit(f"Could not read image: {image_path}")
        mask = roi.create_mask(image)
        feature = calibration.strength_percentage(image, mask)
        features.append(feature)
        labels.append(float(np.clip(label, 0.0, 100.0)))
        samples.append(
            {
                "image": image_path.name,
                "brown_percentage": labels[-1],
                "feature": float(feature),
            }
        )

    predictions = np.clip(
        piecewise_predictions(features, labels),
        0.0,
        100.0,
    )
    errors = np.abs(predictions - np.array(labels))
    points = [
        {
            "feature": float(feature),
            "brown_percentage": float(label),
        }
        for feature, label in sorted(
            zip(features, labels),
            key=lambda pair: pair[0],
        )
    ]
    output = {
        "version": 1,
        "description": (
            "Fitted brown calibration. Prefer real fermented-tea images "
            "captured under production camera and lighting."
        ),
        "references": {
            "light_tea_rgb": calibration.reference_light.tolist(),
            "full_brown_rgb": calibration.reference_brown.tolist(),
        },
        "strength_gamma": calibration.gamma,
        "samples": samples,
        "model": {
            "type": "piecewise_linear",
            "points": points,
            "feature_range": [
                float(min(features)),
                float(max(features)),
            ],
            "mae": float(errors.mean()),
            "max_error": float(errors.max()),
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as file:
        json.dump(output, file, indent=2)
        file.write("\n")

    print(f"Wrote {args.output}")
    print(f"Samples: {len(samples)}")
    print(f"MAE: {errors.mean():.2f}%")
    print(f"Max error: {errors.max():.2f}%")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
