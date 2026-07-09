"""
SentinAI — Forensic Detector
==============================
Analyses image statistics (entropy, FFT frequency spectrum) to detect
anomalies that indicate AI generation or digital manipulation.

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
    "name":        "Forensic Analyser",
    "description": "Examines pixel-level statistics: entropy (randomness) and FFT frequency "
                   "spectrum patterns. AI images often show unnatural regularity in these signals.",
    "model_file":  None,
    "version":     "v1.1",
    "category":    "statistical",
    "speed":       "very fast",
    "priority":    3,
}


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
    Analyse image forensic signals.

    Returns standard result dict with:
        verdict, confidence, ai_probability, real_probability, reasons, raw, error
    """
    result = {
        "detector":         "Forensic Analyser",
        "verdict":          None,
        "confidence":       0.0,
        "ai_probability":   0.5,
        "real_probability": 0.5,
        "reasons":          [],
        "raw":              {},
        "error":            None,
    }

    try:
        import cv2
        import numpy as np
        from scipy.stats import entropy

        img = cv2.imread(image_path)
        if img is None:
            result["error"] = f"Cannot read image: {image_path}"
            result["reasons"].append("❌ Could not open image file.")
            return result

        img   = cv2.resize(img, (512, 512))
        gray  = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # ── Entropy (randomness of pixel distribution) ──
        histogram = np.histogram(gray, bins=256, range=(0, 256))[0]
        ent = float(entropy(histogram + 1))

        # ── FFT (frequency domain analysis) ──
        fft_shifted = np.fft.fftshift(np.fft.fft2(gray))
        fft_magnitude = np.log(np.abs(fft_shifted) + 1)
        fft_std = float(np.std(fft_magnitude))

        # ── Noise level (local variance) ──
        laplacian_var = float(cv2.Laplacian(gray, cv2.CV_64F).var())

        # ── Score calculation ──
        ai_score = 0.0
        reasons  = []

        # Low entropy → uniform/smooth image → AI-like
        if ent < 4.5:
            ai_score += 0.45
            reasons.append(
                f"⚠️  Low pixel entropy ({ent:.2f} < 4.5) — image is unusually uniform, "
                "a common sign of AI generation."
            )
        elif ent < 5.5:
            ai_score += 0.15
            reasons.append(
                f"🟡 Slightly low entropy ({ent:.2f}) — minor uniformity detected."
            )
        else:
            reasons.append(
                f"✅ Normal entropy ({ent:.2f}) — natural pixel distribution."
            )

        # Low FFT std → unnatural frequency regularity
        if fft_std < 0.9:
            ai_score += 0.45
            reasons.append(
                f"⚠️  Abnormal FFT spectrum (std={fft_std:.3f} < 0.9) — frequency patterns "
                "too regular, indicating possible AI synthesis."
            )
        elif fft_std < 1.5:
            ai_score += 0.10
            reasons.append(
                f"🟡 Slightly uniform FFT spectrum (std={fft_std:.3f}) — minor anomaly."
            )
        else:
            reasons.append(
                f"✅ Natural frequency spectrum (FFT std={fft_std:.3f})."
            )

        # Very low Laplacian variance → too smooth (AI often over-smooths)
        if laplacian_var < 50:
            ai_score += 0.10
            reasons.append(
                f"⚠️  Very low sharpness variance ({laplacian_var:.1f}) — image may be "
                "over-smoothed, typical of GAN/diffusion outputs."
            )
        else:
            reasons.append(
                f"✅ Normal sharpness variance ({laplacian_var:.1f})."
            )

        ai_score   = min(ai_score, 1.0)
        real_score = 1.0 - ai_score

        result["ai_probability"]   = round(ai_score, 4)
        result["real_probability"] = round(real_score, 4)
        result["confidence"]       = round(max(ai_score, real_score), 4)
        result["verdict"]          = "AI" if ai_score > 0.5 else "REAL"
        result["reasons"]          = reasons
        result["raw"]              = {
            "entropy":       round(ent, 4),
            "fft_std":       round(fft_std, 4),
            "laplacian_var": round(laplacian_var, 2),
            "ai_score":      round(ai_score, 4),
        }

    except Exception as exc:
        result["error"]  = str(exc)
        result["reasons"].append(f"❌ Forensic analysis failed: {exc}")

    return result