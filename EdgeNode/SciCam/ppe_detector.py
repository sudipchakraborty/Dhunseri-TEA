from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import cv2
import numpy as np

from .app_paths import application_root


@dataclass(frozen=True, slots=True)
class PPEBox:
    bounds: tuple[int, int, int, int]
    label: str
    confidence: float
    color: tuple[int, int, int]


@dataclass(slots=True)
class PPEResult:
    person_present: bool
    missing_items: tuple[str, ...]
    confirmed: bool
    boxes: list[PPEBox] = field(default_factory=list)

    @property
    def event_name(self) -> str:
        if not self.missing_items:
            return ""
        return f"Danger Zone: {' and '.join(self.missing_items)}"


class PPEDetector:
    """Demo full-frame person, mask, and glove compliance detector."""

    RELEVANT_LABELS = {
        "person",
        "mask",
        "no_mask",
        "gloves",
        "no_gloves",
    }

    def __init__(
        self,
        model_path: Path | None = None,
        confidence: float = 0.35,
        confirmation_frames: int = 3,
    ) -> None:
        try:
            import torch
            from ultralytics import YOLO
        except ImportError as error:
            raise RuntimeError(
                "PPE detection requires torch and ultralytics."
            ) from error

        self.model_path = model_path or (
            application_root() / "models" / "ppe_demo.pt"
        )
        self.person_model_path = application_root() / "models" / "yolov8n.pt"
        self.mask_model_path = application_root() / "models" / "person_mask.pt"
        if not self.model_path.is_file():
            raise RuntimeError(f"PPE model not found: {self.model_path}")
        if not self.person_model_path.is_file():
            raise RuntimeError(f"Person model not found: {self.person_model_path}")
        if not self.mask_model_path.is_file():
            raise RuntimeError(f"Mask model not found: {self.mask_model_path}")

        original_torch_load = torch.load

        def load_trusted_model(*args, **kwargs):
            kwargs.setdefault("weights_only", False)
            return original_torch_load(*args, **kwargs)

        torch.load = load_trusted_model
        try:
            self.model = YOLO(str(self.model_path))
            self.person_model = YOLO(str(self.person_model_path))
            self.mask_model = YOLO(str(self.mask_model_path))
        finally:
            torch.load = original_torch_load

        self.confidence = confidence
        self.confirmation_frames = max(1, int(confirmation_frames))
        self._violation_streak = 0

    @staticmethod
    def _normalise(label: str) -> str:
        return label.strip().lower().replace("-", "_").replace(" ", "_")

    def process(self, frame: np.ndarray) -> PPEResult:
        person_prediction = self.person_model.predict(
            source=frame,
            conf=self.confidence,
            classes=[0],
            imgsz=640,
            device=0,
            verbose=False,
        )[0]
        mask_prediction = self.mask_model.predict(
            source=frame,
            conf=self.confidence,
            imgsz=640,
            device=0,
            verbose=False,
        )[0]
        ppe_prediction = self.model.predict(
            source=frame,
            conf=self.confidence,
            imgsz=640,
            device=0,
            verbose=False,
        )[0]

        detected: set[str] = set()
        boxes: list[PPEBox] = []
        colors = {
            "person": (255, 180, 0),
            "mask": (0, 200, 0),
            "gloves": (0, 200, 0),
            "no_mask": (0, 0, 255),
            "no_gloves": (0, 0, 255),
        }

        predictions = (
            (person_prediction, self.person_model),
            (mask_prediction, self.mask_model),
            (ppe_prediction, self.model),
        )
        for prediction, model in predictions:
            if prediction.boxes is None:
                continue
            for box in prediction.boxes:
                class_id = int(box.cls.item())
                label = self._normalise(str(model.names[class_id]))
                if label not in self.RELEVANT_LABELS:
                    continue
                detected.add(label)
                boxes.append(
                    PPEBox(
                        bounds=tuple(
                            int(value) for value in box.xyxy[0].tolist()
                        ),
                        label=label.replace("_", " ").title(),
                        confidence=float(box.conf.item()),
                        color=colors[label],
                    )
                )

        person_present = "person" in detected
        missing_items: list[str] = []
        if person_present:
            if "no_gloves" in detected or "gloves" not in detected:
                missing_items.append("No Gloves")
            if "no_mask" in detected or "mask" not in detected:
                missing_items.append("No Mask")

        if missing_items:
            self._violation_streak += 1
        else:
            self._violation_streak = 0

        return PPEResult(
            person_present=person_present,
            missing_items=tuple(missing_items),
            confirmed=self._violation_streak >= self.confirmation_frames,
            boxes=boxes,
        )

    @staticmethod
    def draw(frame: np.ndarray, result: PPEResult | None) -> np.ndarray:
        output = frame.copy()
        height, width = output.shape[:2]

        if result is None:
            border_color = (0, 200, 255)
            status = "DANGER ZONE - PPE CHECK STARTING"
        elif result.confirmed:
            border_color = (0, 0, 255)
            status = f"ALERT: {' + '.join(result.missing_items)}"
        elif result.person_present and result.missing_items:
            border_color = (0, 165, 255)
            status = f"VERIFYING: {' + '.join(result.missing_items)}"
        else:
            border_color = (0, 200, 0)
            status = "DANGER ZONE - PPE OK" if result.person_present else "DANGER ZONE"

        cv2.rectangle(output, (3, 3), (width - 4, height - 4), border_color, 6)
        cv2.rectangle(output, (8, 8), (min(width - 8, 650), 58), (0, 0, 0), -1)
        cv2.putText(
            output,
            status,
            (18, 43),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.9,
            border_color,
            2,
            cv2.LINE_AA,
        )

        if result is not None:
            for item in result.boxes:
                x1, y1, x2, y2 = item.bounds
                cv2.rectangle(output, (x1, y1), (x2, y2), item.color, 2)
                cv2.putText(
                    output,
                    f"{item.label} {item.confidence:.0%}",
                    (x1, max(28, y1 - 8)),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.65,
                    item.color,
                    2,
                    cv2.LINE_AA,
                )
        return output
