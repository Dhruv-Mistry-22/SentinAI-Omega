"""
SentinAI — Generalized Voting Engine
======================================
Accepts a list of detector results (any number, any mix) and produces
an ensemble consensus vote + confidence adjustment.

Works with the pluggable detector pattern — no hardcoded detector names.
"""

from __future__ import annotations


# ──────────────────────────────────────────────
# CONSENSUS VOTING
# ──────────────────────────────────────────────

def consensus_voting(detector_results: list[dict]) -> dict:
    """
    Run ensemble voting across all detector results.

    Each detector gets one vote (AI or REAL) weighted by its confidence.

    Args:
        detector_results: List of standard result dicts from detect() calls.

    Returns:
        consensus_vote       : "AI" | "REAL"
        ai_votes             : int
        real_votes           : int
        total_voters         : int
        agreement_percentage : float (0-100)
        confidence_level     : str description
        voter_details        : list[dict] per-detector info
        explanation          : str
    """
    votes      = {"AI": 0, "REAL": 0}
    voter_details = []

    for res in detector_results:
        verdict    = res.get("verdict")
        confidence = res.get("confidence", 0.5)
        detector   = res.get("detector", "Unknown")

        if verdict not in ("AI", "REAL"):
            continue   # Skip errored / inconclusive detectors

        votes[verdict] += 1
        voter_details.append({
            "detector":   detector,
            "vote":       verdict,
            "confidence": round(confidence * 100, 2),
            "ai_prob":    round(res.get("ai_probability", 0.5), 4),
            "real_prob":  round(res.get("real_probability", 0.5), 4),
        })

    total     = votes["AI"] + votes["REAL"]
    ai_votes  = votes["AI"]
    real_votes = votes["REAL"]

    if total == 0:
        return {
            "consensus_vote":        "UNKNOWN",
            "ai_votes":              0,
            "real_votes":            0,
            "total_voters":          0,
            "agreement_percentage":  0.0,
            "confidence_level":      "❓ NO_CONSENSUS",
            "voter_details":         [],
            "explanation":           "No detectors produced a valid result.",
        }

    if ai_votes > real_votes:
        consensus      = "AI"
        agreement_pct  = round((ai_votes / total) * 100, 2)
    elif real_votes > ai_votes:
        consensus      = "REAL"
        agreement_pct  = round((real_votes / total) * 100, 2)
    else:
        # Tie — look at average AI probability as tiebreaker
        avg_ai = sum(r.get("ai_probability", 0.5) for r in detector_results) / len(detector_results)
        consensus     = "AI" if avg_ai > 0.5 else "REAL"
        agreement_pct = 50.0

    if agreement_pct >= 85:
        confidence_level = "🔐 VERY_HIGH_CONSENSUS"
    elif agreement_pct >= 70:
        confidence_level = "✅ STRONG_CONSENSUS"
    elif agreement_pct >= 57:
        confidence_level = "🟡 SLIGHT_CONSENSUS"
    else:
        confidence_level = "❓ WEAK_CONSENSUS"

    return {
        "consensus_vote":        consensus,
        "ai_votes":              ai_votes,
        "real_votes":            real_votes,
        "total_voters":          total,
        "agreement_percentage":  agreement_pct,
        "confidence_level":      confidence_level,
        "voter_details":         voter_details,
        "explanation":           (
            f"{ai_votes} detector(s) voted AI, {real_votes} voted REAL "
            f"({agreement_pct:.1f}% agreement)."
        ),
    }


# ──────────────────────────────────────────────
# VOTING THRESHOLD ADJUSTMENT
# ──────────────────────────────────────────────

def apply_voting_threshold(voting_result: dict, base_confidence: float) -> dict:
    """
    Adjust the weighted confidence score based on ensemble consensus.

    Args:
        voting_result    : output of consensus_voting()
        base_confidence  : weighted average AI confidence (0-100)

    Returns:
        original_confidence, adjustment, adjusted_confidence, reason
    """
    adjustment = 0

    agreement  = voting_result.get("agreement_percentage", 50)
    consensus  = voting_result.get("consensus_vote", "UNKNOWN")

    if agreement >= 85:
        # Strong consensus — boost confidence in the voted direction
        adjustment = +5 if consensus == "AI" else -5
    elif agreement <= 50:
        # Weak / tied — reduce confidence (uncertain result)
        adjustment = -10

    adjusted = max(0.0, min(100.0, base_confidence + adjustment))

    return {
        "original_confidence":  round(base_confidence, 2),
        "adjustment":           adjustment,
        "adjusted_confidence":  round(adjusted, 2),
        "reason": (
            f"Voting adjustment ({voting_result.get('confidence_level', '?')}): "
            f"{'+' if adjustment >= 0 else ''}{adjustment} points"
        ),
    }
