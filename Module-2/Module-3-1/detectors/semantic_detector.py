"""
SentinAI — CLIP Semantic Detector
===================================
Uses OpenAI CLIP (ViT-B/32) to semantically classify the image into
categories: real photograph, AI-generated, CGI render, or digital illustration.

Standard Interface:
    DETECTOR_INFO  – metadata dict
    is_available() – True if transformers/torch are importable (no local model file)
    detect(path)   – returns standard result dict
"""

from __future__ import annotations

# ──────────────────────────────────────────────
# DETECTOR METADATA
# ──────────────────────────────────────────────

DETECTOR_INFO = {
    "name":        "CLIP Semantic Detector",
    "description": "Uses OpenAI CLIP (ViT-B/32) to semantically understand the image and score "
                   "it against categories: real photo / AI-generated / CGI / illustration.",
    "model_file":  "downloads openai/clip-vit-base-patch32 on first run",
    "version":     "v1.1",
    "category":    "semantic",
    "speed":       "medium (downloads ~600MB on first run)",
    "priority":    5,
}

# ──────────────────────────────────────────────
# LABELS used for CLIP zero-shot classification
# ──────────────────────────────────────────────

_LABELS = [
    "a real camera photograph taken by a person",
    "an AI-generated image made by a generative model",
    "a 3D CGI render or computer graphics",
    "a digital illustration or digital painting",
]

_LABEL_KEYS = ["real_photo", "ai_generated", "cgi", "illustration"]

# ──────────────────────────────────────────────
# LAZY MODEL CACHE
# ──────────────────────────────────────────────

_model = None
_processor = None
_device = None


def is_available() -> bool:
    """Check if transformers + torch are installed (no local file needed)."""
    try:
        import torch               # noqa: F401
        import transformers        # noqa: F401
        return True
    except ImportError:
        return False


def _load_model():
    global _model, _processor, _device

    if _model is not None:
        return

    import torch
    from transformers import CLIPProcessor, CLIPModel

    _device    = "cuda" if torch.cuda.is_available() else "cpu"
    _model     = CLIPModel.from_pretrained("openai/clip-vit-base-patch32").to(_device)
    _processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")


# ──────────────────────────────────────────────
# MAIN DETECT FUNCTION
# ──────────────────────────────────────────────

def detect(image_path: str) -> dict:
    """
    Semantic classification using CLIP.

    Returns standard result dict.
    """
    result = {
        "detector":         "CLIP Semantic Detector",
        "verdict":          None,
        "confidence":       0.0,
        "ai_probability":   0.5,
        "real_probability": 0.5,
        "reasons":          [],
        "raw":              {},
        "error":            None,
    }

    if not is_available():
        result["error"] = "torch / transformers not installed."
        result["reasons"].append("❌ Required libraries missing (torch, transformers).")
        return result

    try:
        import torch
        from PIL import Image as PILImage

        _load_model()

        image  = PILImage.open(image_path).convert("RGB")
        inputs = _processor(
            text=_LABELS, images=image,
            return_tensors="pt", padding=True,
        ).to(_device)

        with torch.no_grad():
            outputs = _model(**inputs)

        probs = outputs.logits_per_image.softmax(dim=1)[0].tolist()
        scores = dict(zip(_LABEL_KEYS, probs))

        real_prob = scores["real_photo"]
        ai_prob   = (
            scores["ai_generated"] * 0.60 +
            scores["cgi"]          * 0.25 +
            scores["illustration"] * 0.15
        )

        # Normalise to sum to 1
        total     = ai_prob + real_prob
        if total > 0:
            ai_prob   = ai_prob   / total
            real_prob = real_prob / total

        result["ai_probability"]   = round(ai_prob, 4)
        result["real_probability"] = round(real_prob, 4)
        result["confidence"]       = round(max(ai_prob, real_prob), 4)
        result["verdict"]          = "AI" if ai_prob > 0.5 else "REAL"
        result["raw"]              = {k: round(v, 4) for k, v in scores.items()}
        result["raw"]["ai_composite"] = round(ai_prob, 4)

        # Build human-readable reasons
        top_label = max(scores, key=scores.get)
        top_score = scores[top_label]
        label_names = {
            "real_photo":    "real camera photograph",
            "ai_generated":  "AI-generated image",
            "cgi":           "CGI / 3D render",
            "illustration":  "digital illustration",
        }

        result["reasons"].append(
            f"CLIP classifies this image most strongly as: "
            f"'{label_names[top_label]}' ({top_score*100:.1f}% score)."
        )

        if scores["ai_generated"] > 0.35:
            result["reasons"].append(
                f"⚠️  AI-generated label scored {scores['ai_generated']*100:.1f}% — "
                "CLIP sees semantic similarity to AI-generated content."
            )
        if scores["cgi"] > 0.25:
            result["reasons"].append(
                f"🟡 CGI/render label scored {scores['cgi']*100:.1f}% — "
                "image may be 3D rendered or computer-generated."
            )
            # Known CLIP limitation: studio/product shoe photos frequently
            # score high on CGI due to clean backgrounds and even lighting.
            result["reasons"].append(
                "ℹ️  Note: CLIP commonly misclassifies real product/studio shoe photos "
                "as CGI due to clean backgrounds and even lighting. "
                "This signal carries low weight (10%) in shoe analysis — "
                "the Shoe AI Detector result is far more reliable."
            )
        if scores["real_photo"] > 0.50:
            result["reasons"].append(
                f"✅ Real photo label scored {scores['real_photo']*100:.1f}% — "
                "CLIP finds this image semantically similar to real photographs."
            )

        result["reasons"].append(
            f"ℹ️  CLIP weight in this system: 10% (general model, "
            "not trained on shoes — use Shoe AI Detector as primary evidence)."
        )

    except Exception as exc:
        result["error"]  = str(exc)
        result["reasons"].append(f"❌ CLIP semantic detection failed: {exc}")

    return result