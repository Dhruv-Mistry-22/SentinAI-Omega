#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Smart Image Classifier & Router
=================================
Unified CLI entry-point for the three AI-vs-Real detection modules:

  Module-3-1  →  Shoe      (SentinAI, EfficientNet-B0)
  Module-3-2  →  Handbag   (EfficientNet-B3 + ELA + FFT + Metadata)
  Module-3-3  →  Watch     (WatchBrain V2.0 Ensemble)

Usage:
  python classifier.py                    # file picker + auto-detect category
  python classifier.py image.jpg          # pass image directly
  python classifier.py image.jpg --cat shoe    # force a category
  python classifier.py --list             # show which modules are available
  python classifier.py --help

Flow:
  1.  Pick image (file-picker or CLI arg)
  2.  CLIP classifies image → shoe / handbag / watch
  3.  Route to correct specialist module
  4.  If module unavailable → try fallback modules
  5.  Print colour-coded report
"""

from __future__ import annotations

import sys
import io
import os
import time
import argparse
from pathlib import Path
from datetime import datetime

# ──────────────────────────────────────────────────────────────────────────────
# Force UTF-8 on Windows
# ──────────────────────────────────────────────────────────────────────────────
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")


# ──────────────────────────────────────────────────────────────────────────────
# ANSI COLOUR HELPERS
# ──────────────────────────────────────────────────────────────────────────────

def _supports_color() -> bool:
    if os.environ.get("NO_COLOR"):
        return False
    if sys.platform == "win32":
        try:
            import ctypes
            ctypes.windll.kernel32.SetConsoleMode(
                ctypes.windll.kernel32.GetStdHandle(-11), 7
            )
            return True
        except Exception:
            return False
    return hasattr(sys.stdout, "isatty") and sys.stdout.isatty()


_C   = _supports_color()
R    = "\033[0m"        if _C else ""
B    = "\033[1m"        if _C else ""
DIM  = "\033[2m"        if _C else ""
RED  = "\033[91m"       if _C else ""
GRN  = "\033[92m"       if _C else ""
YLW  = "\033[93m"       if _C else ""
BLU  = "\033[94m"       if _C else ""
CYN  = "\033[96m"       if _C else ""
WHT  = "\033[97m"       if _C else ""
ORG  = "\033[38;5;208m" if _C else ""
MAG  = "\033[95m"       if _C else ""

COLOR_HELPERS = dict(B=B, DIM=DIM, RED=RED, GRN=GRN, YLW=YLW,
                     BLU=BLU, CYN=CYN, WHT=WHT, ORG=ORG, MAG=MAG, R=R)

CATEGORY_COLORS = {
    "shoe":    BLU,
    "handbag": MAG,
    "watch":   ORG,
}

CATEGORY_EMOJI = {
    "shoe":    "👟",
    "handbag": "👜",
    "watch":   "⌚",
}


def _sep(ch: str = "─", w: int = 70) -> str:
    return ch * w


def _dbl(w: int = 70) -> str:
    return "═" * w


def _bar(prob: float, width: int = 32) -> str:
    filled = round(prob * width)
    empty  = width - filled
    return f"[{'█' * filled}{'░' * empty}] {prob * 100:5.1f}%"


def _cv(text: str, pct: float) -> str:
    """Colour-code text based on AI confidence %."""
    if pct >= 70:   return f"{RED}{B}{text}{R}"
    if pct >= 55:   return f"{ORG}{B}{text}{R}"
    if pct >= 35:   return f"{YLW}{B}{text}{R}"
    return f"{GRN}{B}{text}{R}"


# ──────────────────────────────────────────────────────────────────────────────
# MODULE PATHS
# ──────────────────────────────────────────────────────────────────────────────

_ROOT   = Path(__file__).resolve().parent
M1_DIR  = _ROOT / "Module-3-1"   # Shoe
M2_DIR  = _ROOT / "Module-3-2"   # Handbag
M3_DIR  = _ROOT / "Module-3-3"   # Watch


# ──────────────────────────────────────────────────────────────────────────────
# MODULE AVAILABILITY CHECKS
# ──────────────────────────────────────────────────────────────────────────────

def _shoe_available() -> bool:
    return (M1_DIR / "models" / "shoe" / "best_shoe_detector.pth").exists()


def _handbag_available() -> bool:
    return (M2_DIR / "models" / "best_handbag_detector_v2.pth").exists()


def _watch_available() -> bool:
    return (M3_DIR / "models" / "best_watch_detector.pth").exists()


MODULE_INFO = {
    "shoe": {
        "name":      "SentinAI — Shoe Detector",
        "desc":      "EfficientNet-B0 fine-tuned on shoe images. "
                     "Detects AI stitching anomalies, impossible geometry & over-smooth textures.",
        "dir":       M1_DIR,
        "available": _shoe_available,
        "color":     BLU,
    },
    "handbag": {
        "name":      "Handbag AI Detector",
        "desc":      "EfficientNet-B3 + Error Level Analysis + FFT Spectral + Metadata forensics.",
        "dir":       M2_DIR,
        "available": _handbag_available,
        "color":     MAG,
    },
    "watch": {
        "name":      "WatchBrain V2.0",
        "desc":      "EfficientNet-B3 + Artifact Detector + Metadata ensemble for watch images.",
        "dir":       M3_DIR,
        "available": _watch_available,
        "color":     ORG,
    },
}

CATEGORY_ORDER = ["shoe", "handbag", "watch"]


# ──────────────────────────────────────────────────────────────────────────────
# BANNER / HEADER
# ──────────────────────────────────────────────────────────────────────────────

def _header():
    print()
    print(f"{CYN}{B}" + _sep("═") + R)
    print(f"{CYN}{B}   Smart Image Classifier  —  AI vs Real Detection Router{R}")
    print(f"{DIM}   Shoe • Handbag • Watch  |  CLIP-Powered  |  Terminal-Native{R}")
    print(f"{CYN}{B}" + _sep("═") + R)
    print()


# ──────────────────────────────────────────────────────────────────────────────
# LIST MODE
# ──────────────────────────────────────────────────────────────────────────────

def _print_module_list():
    print(f"  {B}Available Specialist Modules:{R}\n")
    print(f"  {'Category':<12} {'Status':<16} {'Module Name':<30} {'Description'}")
    print(f"  {DIM}" + _sep("-", 80) + R)
    for cat in CATEGORY_ORDER:
        info = MODULE_INFO[cat]
        ok   = info["available"]()
        col  = info["color"]
        status = f"{GRN}[OK] Ready    {R}" if ok else f"{RED}[!!] Missing  {R}"
        emoji  = CATEGORY_EMOJI[cat]
        print(
            f"  {col}{B}{emoji} {cat.capitalize():<10}{R} "
            f"{status} "
            f"{WHT}{info['name']:<30}{R} "
            f"{DIM}{info['desc'][:50]}…{R}"
        )
    print()
    n_ready = sum(1 for c in CATEGORY_ORDER if MODULE_INFO[c]["available"]())
    if n_ready:
        print(f"  {GRN}{n_ready} module(s) ready.  Run  python classifier.py  to start.{R}\n")
    else:
        print(f"  {RED}No modules are ready. Ensure .pth model files exist inside each Module-3-X/models/ folder.{R}\n")


# ──────────────────────────────────────────────────────────────────────────────
# FILE PICKER
# ──────────────────────────────────────────────────────────────────────────────

def _pick_image() -> str | None:
    try:
        import tkinter as tk
        from tkinter import filedialog

        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        path = filedialog.askopenfilename(
            title="Smart Classifier — Select Image to Analyse",
            filetypes=[
                ("Image files", "*.jpg *.jpeg *.png *.bmp *.webp *.tiff *.tif"),
                ("JPEG",        "*.jpg *.jpeg"),
                ("PNG",         "*.png"),
                ("All files",   "*.*"),
            ],
        )
        root.destroy()
        return path if path else None
    except Exception as exc:
        print(f"\n{YLW}  [!] Could not open file picker: {exc}{R}")
        print(f"  Enter image path manually: ", end="")
        raw = input().strip()
        return raw if raw else None


# ──────────────────────────────────────────────────────────────────────────────
# IMAGE INFO
# ──────────────────────────────────────────────────────────────────────────────

def _print_image_info(image_path: str):
    from PIL import Image
    p = Path(image_path)
    try:
        with Image.open(image_path) as img:
            w, h = img.size
            fmt  = img.format or "?"
        sz   = p.stat().st_size / 1024
        size = f"{sz:.1f} KB" if sz < 1024 else f"{sz / 1024:.2f} MB"
        print(f"  {B}Image   :{R}  {p.name}")
        print(f"  {B}Format  :{R}  {fmt}  |  {w}x{h} px  |  {size}")
    except Exception:
        print(f"  {B}Image   :{R}  {p.name}")
    print(f"  {B}Run at  :{R}  {datetime.now().strftime('%Y-%m-%d  %H:%M:%S')}")
    print()


# ──────────────────────────────────────────────────────────────────────────────
# CATEGORY DETECTION (CLIP)
# ──────────────────────────────────────────────────────────────────────────────

def _detect_category(image_path: str, forced_cat: str | None = None) -> tuple[str, float, dict, str]:
    """
    Returns (category, confidence, scores_dict, method).
    If forced_cat is given, skip CLIP and return immediately.
    """
    if forced_cat:
        scores = {c: (1.0 if c == forced_cat else 0.0) for c in CATEGORY_ORDER}
        return forced_cat, 1.0, scores, "forced"

    # Use CLIP router
    sys.path.insert(0, str(_ROOT))
    from category_router import route
    return route(image_path, color_helpers=COLOR_HELPERS)


def _print_category_result(cat: str, conf: float, scores: dict, method: str):
    col   = CATEGORY_COLORS.get(cat, CYN)
    emoji = CATEGORY_EMOJI.get(cat, "?")
    meth_label = {
        "open_clip":    "CLIP (open-clip-torch)",
        "transformers": "CLIP (HuggingFace transformers)",
        "manual":       "Manual selection",
        "forced":       "CLI flag (--cat)",
    }.get(method, method)

    print(f"  {_sep()}")
    print(f"  {B}STEP 1 — Category Detection{R}")
    print(f"  {_sep()}")
    print(f"  {B}Method   :{R}  {DIM}{meth_label}{R}")
    print()
    for c in CATEGORY_ORDER:
        prob   = scores.get(c, 0.0)
        c_col  = CATEGORY_COLORS.get(c, CYN)
        marker = f"  {GRN}{B}◄ DETECTED{R}" if c == cat else ""
        print(f"  {CATEGORY_EMOJI[c]} {c_col}{c.capitalize():<10}{R}  {_bar(prob)}{marker}")
    print()
    print(f"  {B}Category  :{R}  {col}{B}{emoji} {cat.capitalize()}{R}  "
          f"({conf * 100:.1f}% confidence)")
    print()


# ──────────────────────────────────────────────────────────────────────────────
# MODULE RUNNERS  (thin adapters for each module's API)
# ──────────────────────────────────────────────────────────────────────────────

def _run_shoe(image_path: str) -> dict:
    """Adapter for Module-3-1 (SentinAI shoe detector)."""
    m1 = str(M1_DIR)
    if m1 not in sys.path:
        sys.path.insert(0, m1)

    from detectors.shoe_detector import detect
    return detect(image_path)


def _run_handbag(image_path: str) -> dict:
    """Adapter for Module-3-2 (Handbag forensic pipeline)."""
    m2_src = str(M2_DIR / "src")
    m2     = str(M2_DIR)
    for p in [m2, m2_src]:
        if p not in sys.path:
            sys.path.insert(0, p)

    # Module-3-2 uses relative imports from src/ so we must add it to path
    from modules.classifier import predict
    from modules.metadata   import analyze_metadata
    from modules.artifacts  import perform_ela
    from modules.spectral   import analyze_frequency
    from config import WEIGHTS

    from PIL import Image as PILImage
    img_pil = PILImage.open(image_path).convert("RGB")

    pred_label, ai_prob, _, _ = predict(img_pil)
    meta_score, meta_note     = analyze_metadata(image_path)
    _, ela_score, ela_note    = perform_ela(img_pil)
    _, fft_score, fft_note    = analyze_frequency(img_pil)

    final_score = (
        (ai_prob    * WEIGHTS["classifier"]) +
        (meta_score * WEIGHTS["metadata"]) +
        (ela_score  * WEIGHTS["ela"]) +
        (fft_score  * WEIGHTS["fft"])
    )

    verdict   = "AI" if final_score >= 0.5 else "REAL"
    real_prob = 1.0 - final_score

    return {
        "detector":         "Handbag AI Detector",
        "verdict":          verdict,
        "confidence":       round(max(final_score, real_prob), 4),
        "ai_probability":   round(final_score, 4),
        "real_probability": round(real_prob, 4),
        "reasons": [
            f"Core model ({pred_label}): {ai_prob * 100:.1f}% AI probability",
            f"EXIF Metadata: {meta_score * 100:.0f}% — {meta_note}",
            f"ELA: {ela_score * 100:.0f}% — {ela_note}",
            f"FFT Spectral: {fft_score * 100:.0f}%",
        ],
        "raw": {
            "model_score": ai_prob,
            "meta_score":  meta_score,
            "ela_score":   ela_score,
            "fft_score":   fft_score,
        },
        "error": None,
    }


def _run_watch(image_path: str) -> dict:
    """Adapter for Module-3-3 (WatchBrain V2.0 ensemble)."""
    m3 = str(M3_DIR)
    if m3 not in sys.path:
        sys.path.insert(0, m3)

    from src.ensemble import WatchBrainEnsemble

    ensemble = WatchBrainEnsemble(model_path=str(M3_DIR / "models" / "best_watch_detector.pth"))

    # Call the individual detectors directly so we control the output (no prints)
    eff_score  = ensemble.efficientnet.predict(image_path)
    art_score  = ensemble.artifact_det.predict(image_path)
    meta_score = ensemble.metadata_det.predict(image_path)

    final_score = (eff_score * 0.70) + (art_score * 0.20) + (meta_score * 0.10)
    verdict     = "AI" if final_score > 0.5 else "REAL"
    real_prob   = 1.0 - final_score

    reasons = [
        f"EfficientNet-B3: {eff_score * 100:.1f}% AI probability (weight 70%)",
        f"Artifact Detector: {art_score * 100:.1f}% AI score (weight 20%)",
        f"Metadata Detector: {meta_score * 100:.1f}% AI score (weight 10%)",
    ]
    if verdict == "AI":
        if art_score > 0.7:
            reasons.append("Strong synthetic texture patterns or unnatural blur/sharpness detected.")
        elif meta_score > 0.8:
            reasons.append("Image metadata strongly suggests synthetic generation (missing/altered EXIF).")
        else:
            reasons.append("Deep visual features strongly match known AI generation patterns.")
    else:
        if meta_score < 0.3:
            reasons.append("Authentic camera metadata and natural visual patterns detected.")
        else:
            reasons.append("Visual textures and features strongly align with real photography.")

    return {
        "detector":         "WatchBrain V2.0",
        "verdict":          verdict,
        "confidence":       round(max(final_score, real_prob), 4),
        "ai_probability":   round(final_score, 4),
        "real_probability": round(real_prob, 4),
        "reasons":          reasons,
        "raw": {
            "efficientnet": eff_score,
            "artifact":     art_score,
            "metadata":     meta_score,
        },
        "error": None,
    }


MODULE_RUNNERS = {
    "shoe":    _run_shoe,
    "handbag": _run_handbag,
    "watch":   _run_watch,
}


# ──────────────────────────────────────────────────────────────────────────────
# FALLBACK ROUTING
# ──────────────────────────────────────────────────────────────────────────────

def _get_run_order(primary_cat: str) -> list[str]:
    """
    Returns ordered list of categories to try.
    Primary category is first; others follow in default order.
    """
    others = [c for c in CATEGORY_ORDER if c != primary_cat]
    return [primary_cat] + others


def _find_runnable_module(primary_cat: str) -> tuple[str, bool] | tuple[None, None]:
    """
    Returns (category_to_run, is_fallback).
    is_fallback=True if we had to skip the primary category.
    """
    order = _get_run_order(primary_cat)
    for i, cat in enumerate(order):
        if MODULE_INFO[cat]["available"]():
            return cat, (i > 0)
    return None, None


# ──────────────────────────────────────────────────────────────────────────────
# RESULT PRINTER
# ──────────────────────────────────────────────────────────────────────────────

def _print_result(result: dict, module_cat: str, primary_cat: str, is_fallback: bool):
    col    = CATEGORY_COLORS.get(module_cat, CYN)
    emoji  = CATEGORY_EMOJI.get(module_cat, "?")
    name   = result.get("detector", "Unknown")
    verdict    = result.get("verdict", "UNKNOWN")
    confidence = result.get("confidence", 0.0)
    ai_prob    = result.get("ai_probability",   0.5)
    real_prob  = result.get("real_probability", 0.5)
    reasons    = result.get("reasons", [])
    error      = result.get("error")
    pct        = confidence * 100

    print(f"  {_sep()}")
    print(f"  {B}STEP 2 — Detection Result{R}")
    print(f"  {_sep()}")
    print(f"  {B}Module    :{R}  {col}{B}{emoji} {name}{R}")

    if is_fallback:
        p_col = CATEGORY_COLORS.get(primary_cat, CYN)
        p_emo = CATEGORY_EMOJI.get(primary_cat, "?")
        print(
            f"\n  {YLW}{B}[!] FALLBACK MODE{R}  "
            f"{YLW}Primary module ({p_col}{p_emo} {primary_cat.capitalize()}{YLW}) "
            f"model file not found.{R}"
        )
        print(
            f"  {YLW}    Running closest available module instead: "
            f"{col}{emoji} {module_cat.capitalize()}{R}\n"
        )

    if error and verdict is None:
        print(f"\n  {RED}  Status : ERROR — {error}{R}")
    else:
        print()
        print(f"  {B}Verdict   :{R}  {_cv(verdict, pct)}")
        print(f"  {B}Confidence:{R}  {_cv(f'{pct:.1f}%', pct)}")
        print()
        print(f"  AI Generated   {RED}{_bar(ai_prob)}{R}")
        print(f"  Real / Camera  {GRN}{_bar(real_prob)}{R}")

    if reasons:
        print(f"\n  {B}Evidence:{R}")
        for r in reasons:
            print(f"    • {r}")

    print()
    print(f"  {_dbl()}")
    if verdict:
        print(f"  {B}FINAL VERDICT  :  {_cv(verdict, pct)}{R}")
        print(f"  {B}FINAL CONFIDENCE: {_cv(f'{pct:.1f}%', pct)}{R}")
    print(f"  {_dbl()}")
    print()


# ──────────────────────────────────────────────────────────────────────────────
# ARGUMENT PARSER
# ──────────────────────────────────────────────────────────────────────────────

def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="classifier.py",
        description="Smart Image Classifier — AI vs Real Detection Router (Shoe / Handbag / Watch)",
    )
    p.add_argument(
        "image", nargs="?", default=None,
        help="Path to the image to analyse (optional — opens file picker if omitted)",
    )
    p.add_argument(
        "--cat", choices=["shoe", "handbag", "watch"], default=None,
        help="Force a category instead of auto-detecting with CLIP",
    )
    p.add_argument(
        "--list", action="store_true",
        help="List all modules and their availability, then exit",
    )
    return p.parse_args()


# ──────────────────────────────────────────────────────────────────────────────
# MAIN
# ──────────────────────────────────────────────────────────────────────────────

def main():
    args = _parse_args()

    _header()

    # ── --list mode ──────────────────────────────────────────────────────────
    if args.list:
        _print_module_list()
        return

    # ── Check that at least one module is ready ───────────────────────────────
    ready = [c for c in CATEGORY_ORDER if MODULE_INFO[c]["available"]()]
    if not ready:
        print(f"  {RED}No detection modules are available.{R}")
        print(f"  Run  {CYN}python classifier.py --list{R}  to diagnose.\n")
        sys.exit(1)

    # ── Step 1: Pick image ────────────────────────────────────────────────────
    image_path = args.image
    if not image_path:
        print(f"  {CYN}{B}[>] Opening file picker — select an image to analyse…{R}\n")
        image_path = _pick_image()

    if not image_path:
        print(f"\n  {YLW}No image selected. Exiting.{R}\n")
        sys.exit(0)

    if not Path(image_path).exists():
        print(f"\n  {RED}File not found: {image_path}{R}\n")
        sys.exit(1)

    print(f"  {GRN}Image selected:{R}  {image_path}\n")
    _print_image_info(image_path)

    # ── Step 2: Detect category via CLIP ──────────────────────────────────────
    print(f"  {DIM}" + _sep() + R)
    if args.cat:
        print(f"  {B}Category forced via --cat flag: {CATEGORY_COLORS[args.cat]}{B}{args.cat.capitalize()}{R}\n")
    else:
        print(f"  {B}Detecting image category with CLIP…{R}\n")

    t0 = time.time()
    primary_cat, clip_conf, clip_scores, clip_method = _detect_category(image_path, args.cat)
    elapsed_clip = time.time() - t0

    if args.cat:
        # Skip printing CLIP table for forced category
        pass
    else:
        _print_category_result(primary_cat, clip_conf, clip_scores, clip_method)
        print(f"  {DIM}  Category detection took {elapsed_clip:.2f}s{R}\n")

    # ── Step 3: Route to correct module (with fallback) ───────────────────────
    run_cat, is_fallback = _find_runnable_module(primary_cat)

    if run_cat is None:
        print(f"  {RED}No detection module is available for any category.{R}")
        print(f"  Run  {CYN}python classifier.py --list{R}  for details.\n")
        sys.exit(1)

    col   = CATEGORY_COLORS[run_cat]
    emoji = CATEGORY_EMOJI[run_cat]
    print(f"  {DIM}" + _sep() + R)
    print(f"  {B}Routing to:{R}  {col}{B}{emoji} {MODULE_INFO[run_cat]['name']}{R}")
    print(f"  {DIM}" + _sep() + R)
    print()

    # ── Step 4: Run detector ──────────────────────────────────────────────────
    print(f"  {DIM}  Running detector…{R}", end="", flush=True)
    t0 = time.time()
    try:
        result = MODULE_RUNNERS[run_cat](image_path)
    except Exception as exc:
        result = {
            "detector":         MODULE_INFO[run_cat]["name"],
            "verdict":          None,
            "confidence":       0.0,
            "ai_probability":   0.5,
            "real_probability": 0.5,
            "reasons":          [f"Unexpected error: {exc}"],
            "raw":              {},
            "error":            str(exc),
        }
    elapsed_det = time.time() - t0
    verdict = result.get("verdict") or "ERROR"
    print(f"\r  {GRN}  Detection complete:{R}  {verdict}  {DIM}({elapsed_det:.2f}s){R}\n")

    # ── Step 5: Print report ──────────────────────────────────────────────────
    print(f"{B}" + _sep("═") + R)
    print(f"{B}  DETECTION REPORT{R}")
    print(f"{B}" + _sep("═") + R)
    print()

    _print_result(result, run_cat, primary_cat, is_fallback)

    # ── Prompt to run again ───────────────────────────────────────────────────
    print(f"  {DIM}  Press Enter to exit, or type 'again' to analyse another image: {R}", end="")
    again = input().strip().lower()
    if again in ("again", "y", "yes", "r"):
        main()


if __name__ == "__main__":
    main()
