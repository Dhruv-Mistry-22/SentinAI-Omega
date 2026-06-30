"""
SentinAI — Central Configuration
=================================
All model paths, thresholds, and system-wide settings live here.
Change paths here if you move model files.
"""

from pathlib import Path

# ──────────────────────────────────────────────
# ROOT PATHS
# ──────────────────────────────────────────────

ROOT_DIR      = Path(__file__).resolve().parent
MODELS_DIR    = ROOT_DIR / "models"
DETECTORS_DIR = ROOT_DIR / "detectors"
REPORTS_DIR   = ROOT_DIR / "reports"

# ──────────────────────────────────────────────
# MODEL PATHS  (one sub-folder per detector)
# ──────────────────────────────────────────────

MODEL_PATHS = {
    "cnn":      MODELS_DIR / "cnn"  / "best_deepfake_detector_v2.pth",
    "shoe":     MODELS_DIR / "shoe" / "best_shoe_detector.pth",
    "shoe_cls": MODELS_DIR / "shoe" / "shoe_classes.json",
}

# ──────────────────────────────────────────────
# DETECTION THRESHOLDS
# ──────────────────────────────────────────────

THRESHOLDS = {
    "HIGH_RISK_AI":    70,   # ≥70 % → HIGH_RISK_AI_GENERATED
    "LIKELY_AI":       55,   # ≥55 % → LIKELY_AI_GENERATED
    "SUSPICIOUS":      35,   # ≥35 % → SUSPICIOUS_UNCLEAR
    "PROBABLY_REAL":   20,   # ≥20 % → PROBABLY_REAL
    # < 20 %           →  LIKELY_REAL_AUTHENTIC
}

# ──────────────────────────────────────────────────────────────────────────────
# ENGINE WEIGHTS
# ──────────────────────────────────────────────────────────────────────────────
# The shoe detector is the domain expert — it carries the most weight.
# General models (CNN/CLIP) are useful signals but should NOT override a
# dedicated shoe model. Lower their weights so they assist, not mislead.
# These are raw weights — risk_engine normalises them to sum to 1.0.
# ──────────────────────────────────────────────────────────────────────────────

ENGINE_WEIGHTS = {
    "shoe":     0.60,   # PRIMARY — trained specifically on shoes
    "cnn":      0.05,   # Very low — CIFAKE (general images, not shoe-specific)
    "forensic": 0.20,   # Medium — pixel-level signals, domain-agnostic
    "metadata": 0.05,   # Low — EXIF check (useful but limited)
    "semantic": 0.10,   # Low — CLIP misclassifies shoes as CGI frequently
}

# ──────────────────────────────────────────────
# REPORT SETTINGS
# ──────────────────────────────────────────────

AUTO_SAVE_REPORTS = True        # Save JSON report after every run
REPORT_FORMAT     = "json"      # "json" | "txt" (future)

# ──────────────────────────────────────────────
# TERMINAL DISPLAY
# ──────────────────────────────────────────────

BAR_WIDTH = 30      # Width of ASCII confidence bars
USE_COLOR = True    # ANSI colour output (set False if terminal doesn't support)
