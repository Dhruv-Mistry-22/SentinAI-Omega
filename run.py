#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SentinAI - AI Image Detection System
======================================
Run with:  python run.py

Flow:
  1. Detector selection menu (terminal)
  2. File-picker window opens  (tkinter)
  3. Detection runs
  4. Detailed report prints

Optional flags:
  --all       Skip menu, run all available detectors
  --list      List all installed detectors and exit
  --no-save   Don't save JSON report to reports/
"""

from __future__ import annotations

import sys
import io
import json
import os
import time
import argparse
from datetime import datetime
from pathlib import Path

# ── Force UTF-8 on Windows ──────────────────────────────────────────────────
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")


# ══════════════════════════════════════════════════════════════════════════════
# ANSI COLOUR HELPERS
# ══════════════════════════════════════════════════════════════════════════════

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


_C = _supports_color()
R   = "\033[0m"       if _C else ""
B   = "\033[1m"       if _C else ""
DIM = "\033[2m"       if _C else ""
RED = "\033[91m"      if _C else ""
GRN = "\033[92m"      if _C else ""
YLW = "\033[93m"      if _C else ""
BLU = "\033[94m"      if _C else ""
CYN = "\033[96m"      if _C else ""
WHT = "\033[97m"      if _C else ""
ORG = "\033[38;5;208m" if _C else ""


def _cv(text: str, pct: float) -> str:
    """Colour-code a string based on AI confidence %."""
    if pct >= 70:   return f"{RED}{B}{text}{R}"
    if pct >= 55:   return f"{ORG}{B}{text}{R}"
    if pct >= 35:   return f"{YLW}{B}{text}{R}"
    return f"{GRN}{B}{text}{R}"


def _bar(prob: float, width: int = 32) -> str:
    filled = round(prob * width)
    empty  = width - filled
    return f"[{'█' * filled}{'░' * empty}] {prob*100:5.1f}%"


def _sep(ch: str = "─", w: int = 70) -> str:
    return ch * w


def _dbl(w: int = 70) -> str:
    return "═" * w


# ══════════════════════════════════════════════════════════════════════════════
# FILE PICKER  (tkinter)
# ══════════════════════════════════════════════════════════════════════════════

def _pick_image() -> str | None:
    """Open a native file-picker dialog. Returns path or None if cancelled."""
    try:
        import tkinter as tk
        from tkinter import filedialog

        root = tk.Tk()
        root.withdraw()               # Hide the root window
        root.attributes("-topmost", True)   # Bring dialog to front

        path = filedialog.askopenfilename(
            title="SentinAI — Select Image to Analyse",
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


# ══════════════════════════════════════════════════════════════════════════════
# PRINT HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def _header():
    print()
    print(f"{CYN}{B}" + _sep("=") + R)
    print(f"{CYN}{B}   SentinAI  —  AI Shoe & Image Detection System{R}")
    print(f"{DIM}   Shoe-Focused  |  Pluggable  |  Terminal-Native{R}")
    print(f"{CYN}{B}" + _sep("=") + R)
    print()


def _print_image_info(image_path: str):
    from PIL import Image
    p = Path(image_path)
    try:
        with Image.open(image_path) as img:
            w, h = img.size
            fmt  = img.format or "?"
        sz   = p.stat().st_size / 1024
        size = f"{sz:.1f} KB" if sz < 1024 else f"{sz/1024:.2f} MB"
        print(f"  {B}Image   :{R}  {p.name}")
        print(f"  {B}Format  :{R}  {fmt}  |  {w}x{h} px  |  {size}")
    except Exception:
        print(f"  {B}Image   :{R}  {p.name}")
    print(f"  {B}Run at  :{R}  {datetime.now().strftime('%Y-%m-%d  %H:%M:%S')}")
    print()


def _print_detector_table(all_detectors: list, available_ids: set):
    """Print all detectors as a numbered table."""
    print(f"  {B}Installed Detectors:{R}\n")
    print(f"  {'#':<4} {'Status':<14} {'Name':<35} {'Category':<22} {'Speed'}")
    print(f"  {DIM}" + _sep("-", 72) + R)

    for i, d in enumerate(all_detectors, 1):
        ok      = d["id"] in available_ids
        is_primary = d.get("priority", 99) == 1
        status  = f"{GRN}[OK] Ready  {R}" if ok else f"{RED}[!!] Missing{R}"
        cat     = d.get("category", "general")
        speed   = d.get("speed", "?")
        name    = d["name"]
        primary_tag = f"  {YLW}{B}<-- PRIMARY{R}" if is_primary and ok else ""
        print(f"  {B}{i:<4}{R} {status}  {WHT}{name:<35}{R} {DIM}{cat:<22}  {speed}{R}{primary_tag}")

    print()


def _prompt_selection(available: list[dict]) -> list[dict]:
    """
    Show available detectors and return the user's chosen subset.
    Shoe detector (priority=1) is always shown first and is the default (press Enter).
    Supports:  1   |   1,3   |   1 3   |   A  (all)
    """
    # Find the primary (shoe) detector index
    primary_idx = 1
    for i, d in enumerate(available, 1):
        if d.get("priority", 99) == 1:
            primary_idx = i
            break

    print(f"  {B}Select Detector(s) to Run:{R}\n")
    for i, d in enumerate(available, 1):
        is_primary = d.get("priority", 99) == 1
        tag = f"  {YLW}{B}[PRIMARY — press Enter to select]{R}" if is_primary else ""
        print(f"  {CYN}{B}[{i}]{R}  {WHT}{d['name']}{R}{tag}")
        desc = d.get("description", "")
        short = desc[:90] + ("…" if len(desc) > 90 else "")
        print(f"       {DIM}{short}{R}")
    print(f"\n  {CYN}{B}[A]{R}  Run ALL available detectors")
    print()

    while True:
        raw = input(f"  {CYN}Your choice [{primary_idx}]: {R}").strip()

        # Default — just press Enter → pick shoe detector
        if not raw:
            raw = str(primary_idx)

        if raw.upper() == "A":
            return available

        parts   = [p.strip() for p in raw.replace(",", " ").split()]
        chosen  = []
        ok      = True
        for part in parts:
            if not part.isdigit():
                print(f"  {RED}  Invalid: '{part}' — enter numbers separated by commas/spaces, or A.{R}")
                ok = False
                break
            idx = int(part)
            if idx < 1 or idx > len(available):
                print(f"  {RED}  No detector #{idx} — valid range: 1-{len(available)}.{R}")
                ok = False
                break
            det = available[idx - 1]
            if det not in chosen:
                chosen.append(det)

        if ok and chosen:
            return chosen


def _print_detector_result(result: dict, index: int, total: int):
    name       = result.get("detector", "Unknown")
    verdict    = result.get("verdict", "UNKNOWN")
    confidence = result.get("confidence", 0.0)
    ai_prob    = result.get("ai_probability", 0.5)
    real_prob  = result.get("real_probability", 0.5)
    reasons    = result.get("reasons", [])
    error      = result.get("error")

    print(f"\n  {DIM}" + _sep() + R)
    print(f"  {B}DETECTOR {index}/{total}:  {name}{R}")
    print(f"  {DIM}" + _sep() + R)

    if error and verdict is None:
        print(f"  {RED}  Status : ERROR — {error}{R}")
    else:
        pct = confidence * 100
        print(f"  {B}Verdict   :{R}  {_cv(verdict, pct)}")
        print(f"  {B}Confidence:{R}  {_cv(f'{pct:.1f}%', pct)}")
        print()
        print(f"  AI Generated   {RED}{_bar(ai_prob)}{R}")
        print(f"  Real / Camera  {GRN}{_bar(real_prob)}{R}")

    if reasons:
        print(f"\n  {B}Evidence:{R}")
        for r in reasons:
            print(f"    • {r}")


def _print_voting_summary(voting: dict, adjustment: dict):
    ai_v   = voting.get("ai_votes", 0)
    real_v = voting.get("real_votes", 0)
    total  = voting.get("total_voters", 0)
    agr    = voting.get("agreement_percentage", 0)
    level  = voting.get("confidence_level", "?")
    expl   = voting.get("explanation", "")
    adj    = adjustment.get("adjustment", 0)
    orig   = adjustment.get("original_confidence", 0)
    final  = adjustment.get("adjusted_confidence", 0)

    print(f"\n  {_dbl()}")
    print(f"  {B}ENSEMBLE VOTING SUMMARY{R}")
    print(f"  {_dbl()}")
    print(f"  AI Votes   : {RED}{B}{ai_v}{R} / {total}")
    print(f"  REAL Votes : {GRN}{B}{real_v}{R} / {total}")
    print(f"  Agreement  : {agr:.1f}%   {level}")
    print(f"  {DIM}{expl}{R}")
    sign = "+" if adj >= 0 else ""
    print(f"  Confidence : {sign}{adj} pts  ({orig:.1f}% → {final:.1f}%)")

    voters = voting.get("voter_details", [])
    if voters:
        print(f"\n  {B}Per-Detector Votes:{R}")
        for v in voters:
            vstr = f"{RED}AI  {R}" if v["vote"] == "AI" else f"{GRN}REAL{R}"
            print(f"    {v['detector']:<32}  {vstr}  {v['confidence']:.1f}%")


def _print_final(report: dict):
    cat   = report.get("category", "UNKNOWN")
    conf  = report.get("final_confidence", 0)
    erred = report.get("detectors_errored", 0)

    print()
    print(f"  {_dbl()}")
    print(f"  {B}FINAL VERDICT  :  {_cv(cat, conf)}{R}")
    print(f"  {B}FINAL CONFIDENCE: {_cv(f'{conf:.1f}%', conf)}{R}")
    if erred:
        print(f"  {YLW}  [!] {erred} detector(s) had errors and were excluded.{R}")
    print(f"  {_dbl()}")
    print()


# ══════════════════════════════════════════════════════════════════════════════
# REPORT SAVER
# ══════════════════════════════════════════════════════════════════════════════

def _make_safe(obj):
    if isinstance(obj, dict):
        return {k: _make_safe(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_make_safe(v) for v in obj]
    if isinstance(obj, float) and obj != obj:
        return None
    return obj


def _save_report(report: dict, image_path: str) -> str:
    rep_dir = Path(__file__).parent / "reports"
    rep_dir.mkdir(exist_ok=True)
    ts   = datetime.now().strftime("%Y%m%d_%H%M%S")
    stem = Path(image_path).stem
    fp   = rep_dir / f"{stem}_{ts}.json"
    with open(fp, "w", encoding="utf-8") as f:
        json.dump(_make_safe(report), f, indent=2, ensure_ascii=False)
    return str(fp)


# ══════════════════════════════════════════════════════════════════════════════
# ARGUMENT PARSER
# ══════════════════════════════════════════════════════════════════════════════

def _args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="run.py",
        description="SentinAI — AI Image Detection System",
        add_help=True,
    )
    p.add_argument("--all",     action="store_true", help="Run ALL available detectors")
    p.add_argument("--list",    action="store_true", help="List installed detectors and exit")
    p.add_argument("--save",    action="store_true", help="Force-save JSON report")
    p.add_argument("--no-save", action="store_true", help="Do NOT save JSON report")
    return p.parse_args()


# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════

def main():
    args = _args()

    from engines.registry import DetectorRegistry
    registry = DetectorRegistry()

    _header()

    # ── --list mode ──────────────────────────────────────────────────────────
    if args.list:
        avail_ids = {d["id"] for d in registry.available_detectors}
        _print_detector_table(registry.all_detectors, avail_ids)
        n = len(registry.available_detectors)
        if n:
            print(f"  {GRN}{n} detector(s) ready.  Run  python run.py  to start.{R}\n")
        else:
            print(f"  {YLW}No detectors ready. Add model files to models/<name>/.{R}\n")
        return

    # ── Check detectors ───────────────────────────────────────────────────────
    if not registry.available_detectors:
        print(f"  {RED}No detectors are currently available.{R}")
        print(f"  Run  {CYN}python run.py --list{R}  to see what's installed.\n")
        sys.exit(1)

    # ── Step 1: Detector selection ────────────────────────────────────────────
    avail_ids = {d["id"] for d in registry.available_detectors}
    _print_detector_table(registry.all_detectors, avail_ids)

    if args.all:
        selected = registry.available_detectors
        print(f"  {B}Mode:{R}  Running ALL {len(selected)} available detectors\n")
    else:
        selected = _prompt_selection(registry.available_detectors)

    names = ", ".join(d["name"] for d in selected)
    print(f"\n  {GRN}Selected:{R}  {names}")

    # ── Step 2: Image file picker ─────────────────────────────────────────────
    print(f"\n  {CYN}{B}[>] Opening file picker — select an image to analyse…{R}\n")
    image_path = _pick_image()

    if not image_path:
        print(f"\n  {YLW}No image selected. Exiting.{R}\n")
        sys.exit(0)

    if not Path(image_path).exists():
        print(f"\n  {RED}File not found: {image_path}{R}\n")
        sys.exit(1)

    print(f"  {GRN}Image selected:{R}  {image_path}\n")
    _print_image_info(image_path)

    # ── Step 3: Run detectors ─────────────────────────────────────────────────
    print(f"  {DIM}" + _sep() + R)
    print(f"  {B}Running {len(selected)} detector(s)…{R}")
    print(f"  {DIM}" + _sep() + R + "\n")

    detector_results = []
    total = len(selected)

    for i, det in enumerate(selected, 1):
        module = det["module"]
        name   = det["name"]
        print(f"  {DIM}  [{i}/{total}] {name}…{R}", end="", flush=True)
        t0 = time.time()
        try:
            res = module.detect(image_path)
        except Exception as exc:
            res = {
                "detector": name, "verdict": None, "confidence": 0.0,
                "ai_probability": 0.5, "real_probability": 0.5,
                "reasons": [f"Unexpected error: {exc}"], "raw": {}, "error": str(exc),
            }
        elapsed = time.time() - t0
        verdict = res.get("verdict") or "ERROR"
        print(f"\r  {GRN}  [{i}/{total}] {name:<36}{R}  {DIM}{verdict}  ({elapsed:.2f}s){R}")
        detector_results.append(res)

    # ── Step 4: Generate & print report ──────────────────────────────────────
    from engines.risk_engine import generate_report
    report = generate_report(detector_results, image_path)

    print()
    print(f"{B}" + _sep("=") + R)
    print(f"{B}  DETECTION REPORT{R}")
    print(f"{B}" + _sep("=") + R)

    for i, res in enumerate(detector_results, 1):
        _print_detector_result(res, i, total)

    if total > 1:
        _print_voting_summary(
            report.get("ensemble_voting", {}),
            report.get("voting_adjustment", {}),
        )

    _print_final(report)

    # ── Step 5: Save report ───────────────────────────────────────────────────
    from config import AUTO_SAVE_REPORTS
    should_save = (AUTO_SAVE_REPORTS or args.save) and not args.no_save

    if should_save:
        try:
            saved = _save_report(report, image_path)
            print(f"  {DIM}  Report saved  →  {saved}{R}\n")
        except Exception as exc:
            print(f"  {YLW}  [!] Could not save report: {exc}{R}\n")

    # ── Prompt to run again ───────────────────────────────────────────────────
    print(f"  {DIM}  Press Enter to exit, or type 'again' to analyse another image:{R} ", end="")
    again = input().strip().lower()
    if again in ("again", "y", "yes", "r"):
        main()


if __name__ == "__main__":
    main()
