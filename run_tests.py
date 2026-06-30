#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Independent Dataset Batch Tester
==================================
Runs all 5 images in independent_test/ through the Smart Classifier
and produces a formatted accuracy report comparing predictions vs ground truth.

Usage:
    python run_tests.py
"""

from __future__ import annotations

import sys
import os
import time
from pathlib import Path

# Set encoding env before any imports (avoids double-wrapping stdout)
os.environ.setdefault("PYTHONIOENCODING", "utf-8")

# ── ANSI colours ─────────────────────────────────────────────────────────────
def _sc() -> bool:
    if sys.platform == "win32":
        try:
            import ctypes
            ctypes.windll.kernel32.SetConsoleMode(
                ctypes.windll.kernel32.GetStdHandle(-11), 7)
            return True
        except Exception:
            return False
    return True

_C  = _sc()
R   = "\033[0m"        if _C else ""
B   = "\033[1m"        if _C else ""
DIM = "\033[2m"        if _C else ""
RED = "\033[91m"       if _C else ""
GRN = "\033[92m"       if _C else ""
YLW = "\033[93m"       if _C else ""
CYN = "\033[96m"       if _C else ""
WHT = "\033[97m"       if _C else ""
ORG = "\033[38;5;208m" if _C else ""
MAG = "\033[95m"       if _C else ""
BLU = "\033[94m"       if _C else ""

def _sep(ch="─", w=72): return ch * w
def _dbl(w=72): return "═" * w

# ── Ground truth for each image ───────────────────────────────────────────────
# Format: filename → (true_category, true_label)
#   true_label: "AI" or "REAL"
GROUND_TRUTH = {
    "ai_handbag.png":   ("handbag", "AI"),
    "ai_handbag2.jpg":  ("handbag", "AI"),
    "ai_watch.jpg":     ("watch",   "AI"),
    "real_handbag.jpg": ("handbag", "REAL"),
    "real_watch2.jpg":  ("watch",   "REAL"),
}

CATEGORY_COL = {"shoe": BLU, "handbag": MAG, "watch": ORG}
CATEGORY_EMO = {"shoe": "👟", "handbag": "👜", "watch": "⌚"}

# ── Import classifier internals ───────────────────────────────────────────────
_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(_ROOT))

from classifier import (
    MODULE_INFO, MODULE_RUNNERS, CATEGORY_ORDER,
    _find_runnable_module, _detect_category, COLOR_HELPERS,
)

# ── Run one image ─────────────────────────────────────────────────────────────

def evaluate_image(img_path: str) -> dict:
    """Run CLIP + detector on one image, return results dict."""
    t0 = time.time()
    cat, conf, scores, method = _detect_category(img_path)
    clip_time = time.time() - t0

    run_cat, is_fallback = _find_runnable_module(cat)
    if run_cat is None:
        return {"error": "No module available", "clip_cat": cat}

    t1 = time.time()
    try:
        result = MODULE_RUNNERS[run_cat](img_path)
    except Exception as exc:
        result = {
            "verdict": None, "confidence": 0.0,
            "ai_probability": 0.5, "real_probability": 0.5,
            "error": str(exc),
        }
    det_time = time.time() - t1

    return {
        "clip_cat":    cat,
        "clip_conf":   conf,
        "clip_scores": scores,
        "clip_method": method,
        "clip_time":   clip_time,
        "run_cat":     run_cat,
        "is_fallback": is_fallback,
        "verdict":     result.get("verdict"),
        "confidence":  result.get("confidence", 0.0),
        "ai_prob":     result.get("ai_probability", 0.5),
        "real_prob":   result.get("real_probability", 0.5),
        "det_time":    det_time,
        "error":       result.get("error"),
    }

# ── Pretty result row ─────────────────────────────────────────────────────────

def verdict_color(v: str, pct: float) -> str:
    if pct >= 70: return f"{RED}{B}{v}{R}"
    if pct >= 55: return f"{ORG}{B}{v}{R}"
    if pct >= 35: return f"{YLW}{B}{v}{R}"
    return f"{GRN}{B}{v}{R}"

def bar(prob: float, w: int = 24) -> str:
    filled = round(prob * w)
    return f"[{'█' * filled}{'░' * (w - filled)}] {prob*100:5.1f}%"

# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    test_dir = _ROOT / "independent_test"
    images   = sorted([f for f in test_dir.iterdir()
                       if f.suffix.lower() in (".jpg", ".jpeg", ".png", ".bmp", ".webp")])

    print()
    print(f"{CYN}{B}" + _dbl() + R)
    print(f"{CYN}{B}  Independent Dataset Accuracy Test{R}")
    print(f"{DIM}  {len(images)} images  |  CLIP auto-routing  |  Ground Truth comparison{R}")
    print(f"{CYN}{B}" + _dbl() + R)
    print()

    results  = []
    correct  = 0
    cat_ok   = 0

    for idx, img_path in enumerate(images, 1):
        fname = img_path.name
        truth = GROUND_TRUTH.get(fname)
        true_cat, true_label = truth if truth else ("?", "?")

        print(f"  {B}[{idx}/{len(images)}]{R}  {WHT}{fname}{R}  "
              f"{DIM}(ground truth: {CATEGORY_EMO.get(true_cat,'?')} {true_cat.upper()} / {true_label}){R}")
        print(f"  {DIM}  Running...{R}", end="", flush=True)

        res = evaluate_image(str(img_path))

        clip_cat  = res.get("clip_cat", "?")
        verdict   = res.get("verdict") or "ERROR"
        conf_pct  = res.get("confidence", 0.0) * 100
        ai_prob   = res.get("ai_prob", 0.5)
        real_prob = res.get("real_prob", 0.5)
        clip_time = res.get("clip_time", 0)
        det_time  = res.get("det_time",  0)
        is_fb     = res.get("is_fallback", False)

        # Accuracy checks
        cat_match     = (clip_cat == true_cat)
        verdict_match = (verdict  == true_label)

        if cat_match:    cat_ok  += 1
        if verdict_match: correct += 1

        cat_tick  = f"{GRN}✓{R}" if cat_match    else f"{RED}✗{R}"
        vrd_tick  = f"{GRN}✓{R}" if verdict_match else f"{RED}✗{R}"
        col       = CATEGORY_COL.get(clip_cat, CYN)
        emo       = CATEGORY_EMO.get(clip_cat, "?")

        print(f"\r  {B}[{idx}/{len(images)}]{R}  {WHT}{fname}{R}  "
              f"{DIM}(ground truth: {CATEGORY_EMO.get(true_cat,'?')} {true_cat.upper()} / {true_label}){R}")
        print(f"         Category : {cat_tick}  {col}{B}{emo} {clip_cat.capitalize()}{R}  "
              f"(CLIP {res.get('clip_conf',0)*100:.0f}%)  "
              f"{'⚠ FALLBACK' if is_fb else ''}")
        print(f"         Verdict  : {vrd_tick}  {verdict_color(verdict, conf_pct)}  ({conf_pct:.1f}%)")
        print(f"         AI prob  : {RED}{bar(ai_prob, 20)}{R}   Real prob: {GRN}{bar(real_prob, 20)}{R}")
        print(f"         Timing   : {DIM}CLIP {clip_time:.1f}s  |  Detector {det_time:.2f}s{R}")

        if res.get("error") and not verdict_match:
            print(f"         {YLW}Error: {res['error'][:80]}{R}")

        print()
        results.append({
            "file": fname, "true_cat": true_cat, "true_label": true_label,
            "pred_cat": clip_cat, "pred_label": verdict,
            "cat_ok": cat_match, "verdict_ok": verdict_match,
            "confidence": conf_pct,
        })

    # ── Summary table ─────────────────────────────────────────────────────────
    n = len(images)
    cat_acc = cat_ok   / n * 100
    vrd_acc = correct  / n * 100

    print(_dbl())
    print(f"{B}  ACCURACY SUMMARY{R}")
    print(_dbl())
    print(f"  {'Image':<22} {'True Cat':<10} {'Pred Cat':<10} {'Cat?':<6} "
          f"{'True Label':<12} {'Pred Label':<12} {'Verdict?':<8} {'Confidence'}")
    print(f"  {DIM}" + _sep("-", 96) + R)

    for r in results:
        c_tick = f"{GRN}OK{R}" if r["cat_ok"]    else f"{RED}MISS{R}"
        v_tick = f"{GRN}OK{R}" if r["verdict_ok"] else f"{RED}MISS{R}"
        print(f"  {r['file']:<22} {r['true_cat']:<10} {r['pred_cat']:<10} {c_tick:<14} "
              f"{r['true_label']:<12} {r['pred_label']:<12} {v_tick:<16} {r['confidence']:.1f}%")

    print()
    print(f"  {_sep()}")
    print(f"  {B}Category Accuracy :{R}  "
          f"{'%s%d/%d (%.0f%%)%s' % (GRN if cat_acc == 100 else YLW, cat_ok, n, cat_acc, R)}")
    print(f"  {B}Verdict  Accuracy :{R}  "
          f"{'%s%d/%d (%.0f%%)%s' % (GRN if vrd_acc == 100 else YLW, correct, n, vrd_acc, R)}")
    print(f"  {_sep()}")
    print()

    if vrd_acc == 100:
        print(f"  {GRN}{B}🎉 PERFECT SCORE — All predictions correct!{R}\n")
    elif vrd_acc >= 80:
        print(f"  {GRN}{B}✅ GOOD — {correct}/{n} correct verdicts.{R}\n")
    elif vrd_acc >= 60:
        print(f"  {YLW}{B}⚠ FAIR — {correct}/{n} correct. Some misclassifications.{R}\n")
    else:
        print(f"  {RED}{B}✗ NEEDS IMPROVEMENT — Only {correct}/{n} correct.{R}\n")


if __name__ == "__main__":
    main()
