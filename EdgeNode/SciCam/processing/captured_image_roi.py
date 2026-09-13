from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np


@dataclass(slots=True)
class CapturedImageROI:
    mask: np.ndarray
    overlay: np.ndarray
    bounds: tuple[int, int, int]
    method: str


class CapturedImageROISelector:
    """Find the tea surface inside captured cup photos."""

    def select(self, frame: np.ndarray) -> CapturedImageROI:
        if frame is None or frame.ndim != 3:
            raise ValueError("A BGR colour image is required.")

        circle = self._find_tea_region(frame)
        if circle is None:
            circle = self._find_cup_circle(frame)
            method = "cup circle"
        else:
            method = "tea region"
        if circle is None:
            circle = self._fallback_circle(frame)
            method = "center fallback"

        x, y, radius = circle
        inner_radius = max(8, int(radius * 0.68))
        mask = np.zeros(frame.shape[:2], dtype=np.uint8)
        cv2.circle(mask, (x, y), inner_radius, 255, -1)

        overlay = frame.copy()
        tinted = overlay.copy()
        tinted[mask > 0] = (
            0.45 * tinted[mask > 0]
            + 0.55 * np.array([0, 180, 255])
        ).astype(np.uint8)
        overlay = cv2.addWeighted(tinted, 0.42, overlay, 0.58, 0)
        cv2.circle(overlay, (x, y), inner_radius, (0, 255, 255), 5)
        cv2.circle(overlay, (x, y), max(3, int(inner_radius * 0.02)), (0, 0, 255), -1)

        return CapturedImageROI(
            mask=mask,
            overlay=overlay,
            bounds=(x, y, inner_radius),
            method=method,
        )

    def _find_tea_region(self, frame: np.ndarray):
        height, width = frame.shape[:2]
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
        # Brown tea granules are darker and more saturated than the cup,
        # countertop, and milk-tea background.
        mask = cv2.inRange(hsv, (4, 35, 18), (32, 255, 190))
        mask = cv2.bitwise_and(mask, cv2.inRange(lab[:, :, 0], 0, 175))
        kernel = np.ones((11, 11), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        contours, _hierarchy = cv2.findContours(
            mask,
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE,
        )
        min_area = frame.shape[0] * frame.shape[1] * 0.006
        candidates = []
        image_center = np.array([width / 2.0, height / 2.0])
        for contour in contours:
            area = cv2.contourArea(contour)
            if area < min_area:
                continue
            (x, y), radius = cv2.minEnclosingCircle(contour)
            if radius <= 0:
                continue
            circle_area = np.pi * radius * radius
            fill = area / circle_area
            if fill < 0.35:
                continue
            distance = np.linalg.norm(np.array([x, y]) - image_center)
            centrality = 1.0 - min(1.0, distance / max(image_center))
            score = area * (0.65 + centrality * 0.35) * min(fill, 1.0)
            candidates.append((score, int(x), int(y), int(radius)))
        if not candidates:
            return None
        _score, x, y, radius = max(candidates, key=lambda item: item[0])
        return x, y, radius

    def _find_cup_circle(self, frame: np.ndarray):
        height, width = frame.shape[:2]
        scale = min(1.0, 1000.0 / max(width, height))
        small = cv2.resize(frame, None, fx=scale, fy=scale) if scale < 1 else frame
        gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
        gray = cv2.medianBlur(gray, 7)
        min_side = min(gray.shape[:2])
        circles = cv2.HoughCircles(
            gray,
            cv2.HOUGH_GRADIENT,
            dp=1.2,
            minDist=max(40, min_side // 4),
            param1=90,
            param2=28,
            minRadius=max(25, min_side // 12),
            maxRadius=max(35, min_side // 2),
        )
        if circles is None:
            return None

        center = np.array([gray.shape[1] / 2.0, gray.shape[0] / 2.0])
        best = None
        best_score = -1.0
        for x, y, radius in np.round(circles[0]).astype(int):
            if radius <= 0:
                continue
            distance = np.linalg.norm(np.array([x, y]) - center)
            centrality = 1.0 - min(1.0, distance / max(center))
            size_score = min(1.0, radius / (min_side * 0.35))
            score = centrality * 0.65 + size_score * 0.35
            if score > best_score:
                best_score = score
                best = (x, y, radius)

        if best is None:
            return None
        x, y, radius = best
        return (
            int(x / scale),
            int(y / scale),
            int(radius / scale),
        )

    @staticmethod
    def _fallback_circle(frame: np.ndarray):
        height, width = frame.shape[:2]
        radius = int(min(width, height) * 0.28)
        return width // 2, height // 2, radius
