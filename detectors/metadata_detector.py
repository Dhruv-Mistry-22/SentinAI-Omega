"""
SentinAI — Metadata Detector
==============================
Reads EXIF data embedded in image files to determine if the image
was captured by a real camera or created/edited by AI software.

Standard Interface:
    DETECTOR_INFO  – metadata dict
    is_available() – always True (no model file needed)
    detect(path)   – returns standard result dict
"""

from __future__ import annotations

# ──────────────────────────────────────────────
# DETECTOR METADATA
# ──────────────────────────────────────────────

DETECTOR_INFO = {
    "name":        "Metadata / EXIF Detector",
    "description": "Inspects image EXIF metadata: camera make/model, creation software, "
                   "GPS data, and timestamps. AI-generated images almost never have camera EXIF.",
    "model_file":  None,
    "version":     "v1.2",
    "category":    "metadata",
    "speed":       "very fast",
    "priority":    4,
}

# Known AI/editing tool signatures (lowercase)
_AI_TOOLS = [
    "midjourney", "stable diffusion", "dall-e", "dalle",
    "adobe firefly", "runway", "pika", "emu", "imagen",
    "leonardo", "nightcafe", "dreamstudio", "civitai",
    "novelai", "holara", "artbreeder",
    "photoshop", "gimp", "lightroom", "canva",
]


# ──────────────────────────────────────────────
# AVAILABILITY — always ready
# ──────────────────────────────────────────────

def is_available() -> bool:
    return True


# ──────────────────────────────────────────────
# MAIN DETECT FUNCTION
# ──────────────────────────────────────────────

def detect(image_path: str) -> dict:
    """
    Analyse EXIF metadata of the image.

    Returns standard result dict.
    """
    result = {
        "detector":         "Metadata / EXIF Detector",
        "verdict":          None,
        "confidence":       0.0,
        "ai_probability":   0.5,
        "real_probability": 0.5,
        "reasons":          [],
        "raw":              {},
        "error":            None,
    }

    try:
        from PIL import Image, ExifTags

        img  = Image.open(image_path)
        exif = img.getexif()

        has_exif     = bool(exif)
        camera_make  = None
        camera_model = None
        software     = None
        gps_present  = False
        datetime_val = None

        if has_exif:
            meta = {ExifTags.TAGS.get(k, str(k)): str(v) for k, v in exif.items()}
            camera_make  = meta.get("Make")
            camera_model = meta.get("Model")
            software     = meta.get("Software")
            datetime_val = meta.get("DateTime") or meta.get("DateTimeOriginal")
            # GPS IFD tag = 34853
            gps_present  = 34853 in exif

        # ── AI tool fingerprint ──
        matched_tool = None
        if software:
            soft_lower = software.lower()
            for tool in _AI_TOOLS:
                if tool in soft_lower:
                    matched_tool = software
                    break

        # ── Score calculation ──
        ai_score = 0.20   # Base — most AI images simply have no EXIF

        if not has_exif:
            ai_score += 0.30
            result["reasons"].append(
                "⚠️  No EXIF metadata found. AI-generated images almost never "
                "contain embedded camera data."
            )
        else:
            result["reasons"].append("✅ EXIF metadata is present.")

        if has_exif and not camera_make and not camera_model:
            ai_score += 0.20
            result["reasons"].append(
                "⚠️  No camera Make/Model in EXIF. Real photos always record the device."
            )
        elif camera_make or camera_model:
            ai_score = max(0, ai_score - 0.25)
            result["reasons"].append(
                f"✅ Camera device detected: {camera_make or ''} {camera_model or ''}. "
                "Strong indicator of a real photograph."
            )

        if matched_tool:
            ai_score = min(ai_score + 0.40, 1.0)
            result["reasons"].append(
                f"🚨 AI/editing software fingerprint found: '{matched_tool}'. "
                "This image was processed by a known AI or editing tool."
            )
        elif software:
            result["reasons"].append(f"ℹ️  Software tag: '{software}' — not a known AI tool.")

        if gps_present:
            ai_score = max(0, ai_score - 0.10)
            result["reasons"].append(
                "✅ GPS data present — strongly suggests a real-world camera capture."
            )

        if datetime_val:
            result["reasons"].append(f"ℹ️  Image timestamp: {datetime_val}")

        ai_score   = min(max(ai_score, 0.0), 1.0)
        real_score = 1.0 - ai_score

        result["ai_probability"]   = round(ai_score, 4)
        result["real_probability"] = round(real_score, 4)
        result["confidence"]       = round(max(ai_score, real_score), 4)
        result["verdict"]          = "AI" if ai_score > 0.5 else "REAL"
        result["raw"]              = {
            "has_exif":     has_exif,
            "camera_make":  camera_make,
            "camera_model": camera_model,
            "software":     software,
            "gps_present":  gps_present,
            "matched_tool": matched_tool,
            "ai_score":     round(ai_score, 4),
        }

    except Exception as exc:
        result["error"]  = str(exc)
        result["reasons"].append(f"❌ Metadata analysis failed: {exc}")

    return result