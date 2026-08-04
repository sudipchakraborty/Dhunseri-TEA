from __future__ import annotations

from dataclasses import dataclass, field
import cv2
import numpy as np

from .app_paths import application_root


@dataclass(slots=True)
class DetectionResult:
    annotated_frame: np.ndarray
    events: set[str]
    overlays: list["DetectionOverlay"] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class DetectionOverlay:
    bounds: tuple[int, int, int, int]
    label: str
    confidence: float
    color: tuple[int, int, int]
    thickness: int = 2


class AIDetector:
    """YOLO-backed person and face-mask event detector."""

    MASKED_LABELS = {
        "mask",
        "masked",
        "face_mask",
        "with_mask",
        "mask_weared_correct",
    }
    UNMASKED_LABELS = {
        "no_mask",
        "nomask",
        "without_mask",
        "unmasked",
        "mask_weared_incorrect",
    }
    def __init__(
        self,
        confidence: float = 0.35,
    ) -> None:
        try:
            from ultralytics import YOLO
            import torch
        except ImportError as error:
            raise RuntimeError(
                "AI detection requires the 'ultralytics' package."
            ) from error

        models_dir = application_root() / "models"
        self.mask_model_path = models_dir / "person_mask.pt"
        self.person_model_path = models_dir / "yolov8n.pt"
        if not self.person_model_path.is_file():
            raise RuntimeError(
                "Person detection model not found. Add yolov8n.pt to "
                f"{models_dir}."
            )
        # PyTorch 2.6+ defaults to weights-only checkpoint loading, while
        # Ultralytics 8.0 checkpoints contain their trusted model class.
        original_torch_load = torch.load

        def load_trusted_model(*args, **kwargs):
            kwargs.setdefault("weights_only", False)
            return original_torch_load(*args, **kwargs)

        torch.load = load_trusted_model
        try:
            self.person_model = YOLO(str(self.person_model_path))
            self.mask_model = (
                YOLO(str(self.mask_model_path))
                if self.mask_model_path.is_file()
                else None
            )
        finally:
            torch.load = original_torch_load
        self.confidence = confidence
        self.supports_mask_detection = self.mask_model is not None
        self.supports_gun_detection = False

    @staticmethod
    def _normalise_label(label: str) -> str:
        return label.strip().lower().replace("-", " ").replace(" ", "_")

    @staticmethod
    def draw_overlays(
        frame: np.ndarray,
        overlays: list[DetectionOverlay],
    ) -> np.ndarray:
        """Draw the latest AI boxes on a current live-camera frame."""
        annotated_frame = frame.copy()
        for overlay in overlays:
            x1, y1, x2, y2 = overlay.bounds
            cv2.rectangle(
                annotated_frame,
                (x1, y1),
                (x2, y2),
                overlay.color,
                overlay.thickness,
            )
            cv2.putText(
                annotated_frame,
                f"{overlay.label} {overlay.confidence:.0%}",
                (x1, max(28, y1 - 10)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.72,
                overlay.color,
                2,
                cv2.LINE_AA,
            )
        return annotated_frame

    def process(self, frame: np.ndarray) -> DetectionResult:
        person_prediction = self.person_model.predict(
            source=frame,
            conf=self.confidence,
            verbose=False,
        )[0]
        events: set[str] = set()
        overlays: list[DetectionOverlay] = []

        if person_prediction.boxes is not None:
            for box in person_prediction.boxes:
                class_id = int(box.cls.item())
                label = self._normalise_label(
                    str(self.person_model.names[class_id])
                )
                if label == "person":
                    events.add("Person Detected")
                    overlays.append(
                        DetectionOverlay(
                            bounds=tuple(
                                int(value)
                                for value in box.xyxy[0].tolist()
                            ),
                            label="Person",
                            confidence=float(box.conf.item()),
                            color=(255, 180, 0),
                        )
                    )

        if self.mask_model is not None:
            mask_prediction = self.mask_model.predict(
                source=frame,
                conf=self.confidence,
                verbose=False,
            )[0]
            if mask_prediction.boxes is not None:
                for box in mask_prediction.boxes:
                    class_id = int(box.cls.item())
                    confidence = float(box.conf.item())
                    label = self._normalise_label(
                        str(self.mask_model.names[class_id])
                    )
                    if label in self.MASKED_LABELS:
                        event_name = "Mask Detected"
                        color = (0, 200, 0)
                    elif label in self.UNMASKED_LABELS:
                        event_name = "No Mask Detected"
                        color = (0, 0, 255)
                    else:
                        continue

                    events.add(event_name)
                    overlays.append(
                        DetectionOverlay(
                            bounds=tuple(
                                int(value)
                                for value in box.xyxy[0].tolist()
                            ),
                            label=event_name,
                            confidence=confidence,
                            color=color,
                        )
                    )

        annotated_frame = self.draw_overlays(frame, overlays)
        return DetectionResult(
            annotated_frame=annotated_frame,
            events=events,
            overlays=overlays,
        )
