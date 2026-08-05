"""SENTINEL AI - object & face detection.

Primary: Ultralytics YOLO (open-weight, on-device, no API).
Face detection: OpenCV Haar cascade (bundled, zero download) when
available, otherwise falls back to YOLO person/face classes.

Every import is lazy and wrapped so the module never crashes a
hackathon demo when a heavy package is missing.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

from backend.config import settings
from backend.core.logging import log

_MODELS: Dict[str, Any] = {}
_STACK: List[str] = []


def vision_stack() -> List[str]:
    """Describe which vision components are active (for the UI)."""
    if _STACK:
        return _STACK
    try:
        import cv2  # noqa: F401
        _STACK.append("opencv")
    except Exception:
        pass
    try:
        from ultralytics import YOLO  # noqa: F401
        _STACK.append("yolo")
    except Exception:
        pass
    try:
        import easyocr  # noqa: F401
        _STACK.append("easyocr")
    except Exception:
        pass
    return _STACK or ["pillow-only"]


def _get_yolo():
    if "yolo" in _MODELS:
        return _MODELS["yolo"]
    try:
        from ultralytics import YOLO
    except Exception as exc:
        log("warning", f"YOLO unavailable: {exc}")
        return None
    model_path = settings.models / "yolov8n.pt"
    try:
        if model_path.exists():
            model = YOLO(str(model_path))
        else:
            model = YOLO("yolov8n.pt")
            # stash the downloaded weights inside ai_models/
            cwd_model = Path.cwd() / "yolov8n.pt"
            if cwd_model.exists():
                cwd_model.replace(model_path)
        _MODELS["yolo"] = model
        log("info", "YOLO object detector loaded")
        return model
    except Exception as exc:
        log("warning", f"YOLO load failed: {exc}")
        return None


# COCO80 labels relevant to intelligence work.
_ANIMAL_SET = {
    "bird", "cat", "dog", "horse", "sheep", "cow", "elephant",
    "bear", "zebra", "giraffe",
}
_VEHICLE_SET = {
    "bicycle", "car", "motorcycle", "airplane", "bus", "train",
    "truck", "boat",
}
_WEAPON_OBJECTS = {"knife", "scissors", "sports ball"}


def detect_objects(image_path: str | Path) -> Dict[str, Any]:
    """Run YOLO and summarize detections into the vision schema shape."""
    out: Dict[str, Any] = {
        "persons": 0,
        "objects": [],
        "vehicles": [],
        "scenes": [],
    }
    model = _get_yolo()
    if model is None:
        return out

    try:
        results = model.predict(
            source=str(image_path), conf=0.35, verbose=False,
            device="cpu",
        )
        result = results[0]
        names = result.names
        for box in result.boxes:
            cls_id = int(box.cls[0])
            conf = float(box.conf[0])
            xyxy = [int(v) for v in box.xyxy[0].tolist()]
            label = names.get(cls_id, "object")
            entry = {"label": label, "confidence": round(conf, 3), "bbox": xyxy}
            if label == "person":
                out["persons"] += 1
                out["objects"].append(entry)
            elif label in _VEHICLE_SET:
                out["vehicles"].append(entry)
            elif label in _WEAPON_OBJECTS or cls_id not in _ANIMAL_SET and label not in (
                "person",
            ):
                out["objects"].append(entry)
        out["scenes"] = _scene_inference(out)
    except Exception as exc:
        log("warning", f"YOLO inference failed: {exc}")
    return out


def _scene_inference(out: Dict[str, Any]) -> List[str]:
    scenes: List[str] = []
    if out["persons"] > 5:
        scenes.append("crowd")
    if out["vehicles"]:
        scenes.append("traffic / transport environment")
    if out["persons"] == 1 and not out["vehicles"]:
        scenes.append("indoor or studio setting (possible)")
    return scenes or ["unclassified"]


def detect_faces(image_path: str | Path) -> Dict[str, Any]:
    """Detect human presence in the image.

    Preference: OpenCV Haar cascade (cv2 <5). On OpenCV 5+ (which dropped
    the legacy cascade API) we fall back to YOLO person detections, so
    face-presence reporting never silently breaks.
    """
    try:
        import cv2
    except Exception:
        pass
    else:
        cascade_cls = getattr(cv2, "CascadeClassifier", None)
        if cascade_cls is not None:
            try:
                img = cv2.imread(str(image_path))
                if img is not None:
                    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                    cascade = cascade_cls(
                        cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
                    )
                    faces = cascade.detectMultiScale(
                        gray, scaleFactor=1.1, minNeighbors=5, minSize=(32, 32)
                    )
                    if len(faces) > 0:
                        conf = min(0.98, 0.55 + 0.08 * len(faces))
                        return {
                            "detected": True,
                            "count": int(len(faces)),
                            "confidence": round(conf, 3),
                        }
            except Exception as exc:
                log("warning", f"Haar face detection failed: {exc}")

    # YOLO fallback: persons detected in frame => human presence.
    model = _get_yolo()
    if model is not None:
        try:
            results = model.predict(
                source=str(image_path), conf=0.35, verbose=False, device="cpu"
            )
            persons = sum(
                1
                for r in results
                for b in r.boxes
                if int(b.cls[0]) == 0
            )
            if persons > 0:
                return {
                    "detected": True,
                    "count": int(persons),
                    "confidence": 0.8,
                }
        except Exception as exc:
            log("warning", f"YOLO face-presence fallback failed: {exc}")

    return {"detected": False, "count": 0, "confidence": 0.0}


def estimate_clothing(image_path: str | Path) -> Dict[str, Any]:
    """Heuristic clothing/colour description from a region of interest.

    Full person-segmentation would need SAM/Segment; here we report
    overall image colour profile and region hints as evidence notes.
    """
    from backend.vision.metadata import dominant_colors

    colors = dominant_colors(image_path, k=3)
    return {"colors": colors}
