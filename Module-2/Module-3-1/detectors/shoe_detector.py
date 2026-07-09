"""
SentinAI — Shoe / Object Detector
====================================
EfficientNet-B0 trained specifically to classify shoe images as
AI-generated or real.  Demonstrates the pluggable detector pattern:
add more object-specific detectors (bags, faces, cars…) in the same way.

Standard Interface:
    DETECTOR_INFO  – metadata dict
    is_available() – True if model file exists
    detect(path)   – returns standard result dict
"""

from __future__ import annotations
import json
from pathlib import Path

# ──────────────────────────────────────────────
# DETECTOR METADATA
# ──────────────────────────────────────────────

DETECTOR_INFO = {
    "name":        "Shoe AI Detector  [PRIMARY]",
    "description": "PRIMARY DETECTOR — EfficientNet-B0 fine-tuned specifically on shoe images "
                   "to classify footwear as AI-generated or real. Catches stitching anomalies, "
                   "impossible geometry, over-smooth textures, and unnatural sole patterns.",
    "model_file":  "models/shoe/best_shoe_detector.pth",
    "version":     "v1.0",
    "category":    "shoe-specific  [PRIMARY]",
    "speed":       "fast",
    "priority":    1,
}

# ──────────────────────────────────────────────
# PATHS
# ──────────────────────────────────────────────

_ROOT       = Path(__file__).resolve().parent.parent
_MODEL_PATH = _ROOT / "models" / "shoe" / "best_shoe_detector.pth"
_CLASS_PATH = _ROOT / "models" / "shoe" / "shoe_classes.json"

# ──────────────────────────────────────────────
# AVAILABILITY
# ──────────────────────────────────────────────

def is_available() -> bool:
    return _MODEL_PATH.exists()


# ──────────────────────────────────────────────
# LAZY MODEL CACHE
# ──────────────────────────────────────────────

_model     = None
_transform = None
_device    = None
_classes   = ["AI_SHOE", "REAL_SHOE"]   # default; overridden if classes file exists


def _load_model():
    global _model, _transform, _device, _classes

    if _model is not None:
        return

    import torch
    from torchvision import transforms

    # Try to load class labels
    if _CLASS_PATH.exists():
        with open(_CLASS_PATH) as f:
            _classes = json.load(f)

    _device = "cuda" if torch.cuda.is_available() else "cpu"

    # weights_only=False required — timm saves full model objects (pickled custom classes)
    loaded = torch.load(_MODEL_PATH, map_location=_device, weights_only=False)

    # Detect save style:
    #   Full model object  → use directly   (timm: torch.save(model, path))
    #   State dict         → build arch + load weights
    if isinstance(loaded, dict):
        try:
            import timm
            base = timm.create_model(
                "efficientnet_b0", pretrained=False, num_classes=len(_classes)
            )
        except ImportError:
            import torch.nn as nn
            from torchvision import models
            base = models.efficientnet_b0(weights=None)
            base.classifier[1] = nn.Linear(
                base.classifier[1].in_features, len(_classes)
            )
        base.load_state_dict(loaded, strict=False)
        _model = base
    else:
        # Full model save — loaded IS the model
        _model = loaded

    _model = _model.to(_device)
    _model.eval()

    _transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(
            mean=[0.485, 0.456, 0.406],
            std=[0.229, 0.224, 0.225],
        ),
    ])


# ──────────────────────────────────────────────
# MAIN DETECT FUNCTION
# ──────────────────────────────────────────────

def detect(image_path: str) -> dict:
    """
    Classify shoe/object image as AI-generated or real.

    Returns standard result dict.
    """
    result = {
        "detector":         DETECTOR_INFO["name"],
        "verdict":          None,
        "confidence":       0.0,
        "ai_probability":   0.5,
        "real_probability": 0.5,
        "reasons":          [],
        "raw":              {},
        "error":            None,
    }

    if not is_available():
        result["error"] = f"Model not found: {_MODEL_PATH}"
        result["reasons"].append("❌ Shoe model file missing — detector unavailable.")
        return result

    try:
        import torch
        from PIL import Image as PILImage

        _load_model()

        img    = PILImage.open(image_path).convert("RGB")
        tensor = _transform(img).unsqueeze(0).to(_device)

        with torch.no_grad():
            output = _model(tensor)
            probs  = torch.softmax(output, dim=1)[0]

        # Class 0 = AI_SHOE, Class 1 = REAL_SHOE
        ai_prob   = round(probs[0].item(), 4)
        real_prob = round(probs[1].item(), 4)

        result["ai_probability"]   = ai_prob
        result["real_probability"] = real_prob
        result["confidence"]       = round(max(ai_prob, real_prob), 4)
        result["verdict"]          = "AI" if ai_prob > real_prob else "REAL"
        result["raw"]              = {
            "ai_shoe_prob":   ai_prob,
            "real_shoe_prob": real_prob,
            "classes":        _classes,
        }

        if ai_prob > real_prob:
            result["reasons"].append(
                f"Object detector flags footwear as AI-generated ({ai_prob*100:.1f}% confidence)."
            )
            if ai_prob > 0.80:
                result["reasons"].append(
                    "Very high confidence — shoe exhibits AI texture artifacts "
                    "(over-smooth sole, unnatural stitching, impossible geometry)."
                )
        else:
            result["reasons"].append(
                f"Object detector classifies footwear as real ({real_prob*100:.1f}% confidence)."
            )
            if real_prob > 0.80:
                result["reasons"].append(
                    "Very high confidence — shoe displays natural manufacturing imperfections "
                    "and realistic material texture."
                )

        result["reasons"].append(
            "ℹ️  Note: This detector is optimised for shoe images. "
            "Results on non-shoe images may be unreliable."
        )

    except Exception as exc:
        result["error"]  = str(exc)
        result["reasons"].append(f"❌ Shoe detection failed: {exc}")

    return result
