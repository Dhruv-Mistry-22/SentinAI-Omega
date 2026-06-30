"""
SentinAI — Generalized Risk Engine
=====================================
Combines results from any set of detectors into a final verdict,
confidence score, and human-readable report.

Works with the pluggable detector pattern — adapts to however many
detectors were run (1 or many).
"""

from __future__ import annotations
from engines.voting_engine import consensus_voting, apply_voting_threshold


# ──────────────────────────────────────────────
# THRESHOLDS
# ──────────────────────────────────────────────

_T = {
    "HIGH_RISK_AI":  70,
    "LIKELY_AI":     55,
    "SUSPICIOUS":    35,
    "PROBABLY_REAL": 20,
}


def _category(confidence_pct: float) -> str:
    if confidence_pct >= _T["HIGH_RISK_AI"]:
        return "🚨 HIGH_RISK_AI_GENERATED"
    elif confidence_pct >= _T["LIKELY_AI"]:
        return "⚠️  LIKELY_AI_GENERATED"
    elif confidence_pct >= _T["SUSPICIOUS"]:
        return "❓ SUSPICIOUS_UNCLEAR"
    elif confidence_pct >= _T["PROBABLY_REAL"]:
        return "✔  PROBABLY_REAL"
    else:
        return "✅ LIKELY_REAL_AUTHENTIC"


# ──────────────────────────────────────────────
# MAIN REPORT GENERATOR
# ──────────────────────────────────────────────

def generate_report(detector_results: list[dict], image_path: str) -> dict:
    """
    Combine N detector results into a final SentinAI report.

    Args:
        detector_results : list of standard result dicts from detect() calls.
        image_path       : path to the analysed image (for report metadata).

    Returns:
        Full report dict with category, confidence, per-detector breakdown,
        ensemble voting, and all reasons.
    """
    # ── Filter out completely errored detectors ──
    valid = [r for r in detector_results if r.get("verdict") in ("AI", "REAL")]

    if not valid:
        return {
            "image_path":         image_path,
            "category":           "❓ INCONCLUSIVE",
            "final_confidence":   0.0,
            "verdict":            "UNKNOWN",
            "ensemble_voting":    {},
            "voting_adjustment":  {},
            "detector_results":   detector_results,
            "error":              "No detectors produced a valid result.",
        }

    # ── Weighted average AI probability ──
    # Equal weight if only 1 detector; else use per-detector weight hints.
    weights = _assign_weights(valid)

    weighted_ai = sum(
        r["ai_probability"] * weights[i]
        for i, r in enumerate(valid)
    )
    base_confidence = round(weighted_ai * 100, 2)

    # ── Ensemble voting ──
    voting   = consensus_voting(valid)
    adjusted = apply_voting_threshold(voting, base_confidence)

    final_confidence = adjusted["adjusted_confidence"]
    category         = _category(final_confidence)

    # ── Aggregate all reasons ──
    all_reasons: list[str] = []
    for r in detector_results:
        for reason in r.get("reasons", []):
            all_reasons.append(f"[{r.get('detector', '?')}] {reason}")

    return {
        "image_path":          image_path,
        "category":            category,
        "final_confidence":    final_confidence,
        "base_confidence":     base_confidence,
        "verdict":             "AI" if final_confidence >= 35 else "REAL",
        "ai_probability_avg":  round(weighted_ai, 4),
        "real_probability_avg": round(1 - weighted_ai, 4),
        "ensemble_voting":     voting,
        "voting_adjustment":   adjusted,
        "detector_results":    detector_results,
        "all_reasons":         all_reasons,
        "detectors_run":       [r.get("detector", "?") for r in detector_results],
        "detectors_valid":     len(valid),
        "detectors_errored":   len(detector_results) - len(valid),
    }


# ──────────────────────────────────────────────────────────────────────────
# WEIGHT ASSIGNMENT
# ──────────────────────────────────────────────────────────────────────────
#
# Shoe detector is the DOMAIN EXPERT — trained specifically on shoe images.
# It gets 60% of the vote. General models (CNN/CLIP) are useful cross-checks
# but must NOT override a dedicated shoe model — keep their weights low.
#
# Weights are RAW — _assign_weights() normalises to sum to 1.0 automatically.
# ──────────────────────────────────────────────────────────────────────────

_PREFERRED_WEIGHTS: dict[str, float] = {
    "Shoe AI Detector  [PRIMARY]": 0.60,   # DOMAIN EXPERT — shoe-specific model
    "Forensic Analyser":           0.20,   # domain-agnostic pixel stats — reliable
    "CLIP Semantic Detector":      0.10,   # general — often misreads shoes as CGI
    "CIFAKE CNN Detector":         0.05,   # trained on generic images, not shoes
    "Metadata / EXIF Detector":    0.05,   # useful EXIF signal, but limited
    # Legacy name kept for backward compat if older model files still exist
    "Shoe / Object Detector":      0.60,
    "CNN Image Classifier":        0.05,
}

_DEFAULT_WEIGHT = 0.05   # fallback for any new/unknown detector


def _assign_weights(valid_results: list[dict]) -> list[float]:
    """
    Assign weights to each detector result.
    Uses preferred weights where known; falls back to _DEFAULT_WEIGHT.
    Normalises so all weights sum to 1.0.
    """
    raw = []
    for r in valid_results:
        name = r.get("detector", "")
        raw.append(_PREFERRED_WEIGHTS.get(name, _DEFAULT_WEIGHT))

    total = sum(raw)
    if total == 0:
        equal = 1.0 / len(valid_results)
        return [equal] * len(valid_results)

    return [w / total for w in raw]
