"""
SentinAI — CNN Image Detector
==============================
EfficientNet-B0 trained on real vs AI-generated images.
Lazy-loads model on first call to detect() — import is always safe.

Standard Interface:
    DETECTOR_INFO  – metadata dict
    is_available() – True if model file exists
    detect(path)   – returns standard result dict
"""

from __future__ import annotations
from pathlib import Path

# ──────────────────────────────────────────────
# DETECTOR METADATA  (required by DetectorRegistry)
# ──────────────────────────────────────────────

DETECTOR_INFO = {
    "name":        "CIFAKE CNN Detector",
    "description": "EfficientNet-B0 trained on the CIFAKE dataset (60,000 real CIFAR-10 photos "
                   "+ 60,000 AI-generated equivalents). Detects general AI generation patterns: "
                   "texture regularity, frequency artifacts, and GAN/diffusion signatures. "
                   "NOTE: Trained on general images — use Shoe AI Detector as primary for shoes.",
    "model_file":  "models/cnn/best_deepfake_detector_v2.pth",
    "version":     "v2.0  (CIFAKE)",
    "category":    "general  (CIFAKE)",
    "speed":       "fast",
    "priority":    2,
}

# ──────────────────────────────────────────────
# PATHS
# ──────────────────────────────────────────────

_MODEL_PATH = Path(__file__).resolve().parent.parent / "models" / "cnn" / "best_deepfake_detector_v2.pth"

# ──────────────────────────────────────────────
# AVAILABILITY CHECK
# ──────────────────────────────────────────────

def is_available() -> bool:
    """Return True if the trained model file exists on disk."""
    return _MODEL_PATH.exists()


# ──────────────────────────────────────────────
# LAZY MODEL LOADER
# ──────────────────────────────────────────────

_model = None
_transform = None
_device = None


def _load_model():
    """Load model once and cache it in module-level variables."""
    global _model, _transform, _device

    if _model is not None:
        return  # Already loaded

    import torch
    import torch.nn as nn
    from torchvision import models, transforms

    _device = "cuda" if torch.cuda.is_available() else "cpu"

    base = models.efficientnet_b0(weights=None)
    num_features = base.classifier[1].in_features
    base.classifier = nn.Sequential(
        nn.Dropout(p=0.2, inplace=True),
        nn.Linear(num_features, 128),
        nn.ReLU(),
        nn.Dropout(0.3),
        nn.Linear(128, 2),
    )

    checkpoint = torch.load(_MODEL_PATH, map_location=_device)
    base.load_state_dict(checkpoint, strict=False)
    base = base.to(_device)
    base.eval()

    _model = base
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
    Analyse image with the CNN classifier.

    Returns:
        verdict          : "AI" | "REAL"
        confidence       : float 0-1 (probability of verdict)
        ai_probability   : float 0-1
        real_probability : float 0-1
        reasons          : list[str]  human-readable explanation
        raw              : dict       raw scores for engine aggregation
        error            : str | None
    """
    result = {
        "detector":       "CNN Image Classifier",
        "verdict":        None,
        "confidence":     0.0,
        "ai_probability": 0.5,
        "real_probability": 0.5,
        "reasons":        [],
        "raw":            {},
        "error":          None,
    }

    if not is_available():
        result["error"] = f"Model not found: {_MODEL_PATH}"
        result["reasons"].append("❌ CNN model file missing — detector unavailable.")
        return result

    try:
        import torch
        from PIL import Image as PILImage

        _load_model()

        img = PILImage.open(image_path).convert("RGB")
        tensor = _transform(img).unsqueeze(0).to(_device)

        with torch.no_grad():
            outputs = _model(tensor)
            probs = torch.softmax(outputs, dim=1)[0]

        ai_prob   = round(probs[0].item(), 4)
        real_prob = round(probs[1].item(), 4)

        result["ai_probability"]   = ai_prob
        result["real_probability"] = real_prob
        result["raw"]              = {"ai_prob": ai_prob, "real_prob": real_prob}

        if ai_prob > real_prob:
            result["verdict"]    = "AI"
            result["confidence"] = ai_prob
            result["reasons"].append(
                f"General CNN (CIFAKE) is {ai_prob*100:.1f}% confident this is AI-generated."
            )
            if ai_prob > 0.85:
                result["reasons"].append(
                    "Very high confidence — strong AI pattern signatures found (trained on CIFAKE dataset)."
                )
            elif ai_prob > 0.65:
                result["reasons"].append(
                    "Moderate-high confidence — AI generation artifacts detected (CIFAKE-trained model)."
                )
        else:
            result["verdict"]    = "REAL"
            result["confidence"] = real_prob
            result["reasons"].append(
                f"General CNN (CIFAKE) is {real_prob*100:.1f}% confident this is a real photograph."
            )
            result["reasons"].append(
                "NOTE: This model is trained on CIFAKE (general images). "
                "For shoe-specific analysis, the Shoe AI Detector is more reliable."
            )

    except Exception as exc:
        result["error"]  = str(exc)
        result["reasons"].append(f"❌ CNN detection failed: {exc}")

    return result