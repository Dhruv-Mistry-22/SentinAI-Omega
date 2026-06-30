"""
utils.py — Helper utilities for the Assignment Plagiarism Detection System.

Provides:
- CLI progress bar
- Colored/styled console output
- Time formatting
- PDF-safe text encoding
"""

import sys


# ────────────────────── PROGRESS BAR ──────────────────────

def progress_bar(current, total, prefix="Progress", length=40):
    """Display a text-based progress bar in the terminal."""
    if total == 0:
        return
    percent = current / total
    filled = int(length * percent)
    bar = "#" * filled + "-" * (length - filled)
    sys.stdout.write(f"\r  {prefix}: [{bar}] {percent:.0%} ({current}/{total})")
    sys.stdout.flush()
    if current >= total:
        print()  # newline after completion


# ────────────────────── CONSOLE OUTPUT ──────────────────────

def print_header(text):
    """Print a styled section header."""
    width = 60
    print("\n" + "=" * width)
    print(f"  {text}")
    print("=" * width)


def print_success(msg):
    """Print a success message."""
    print(f"  [OK] {msg}")


def print_error(msg):
    """Print an error message."""
    print(f"  [ERROR] {msg}")


def print_warning(msg):
    """Print a warning message."""
    print(f"  [WARNING] {msg}")


def print_info(msg):
    """Print an informational message."""
    print(f"  [INFO] {msg}")


# ────────────────────── FORMATTING ──────────────────────

def format_time(seconds):
    """Format elapsed seconds into a human-readable string."""
    if seconds < 60:
        return f"{seconds:.1f}s"
    minutes = int(seconds // 60)
    secs = seconds % 60
    return f"{minutes}m {secs:.1f}s"


def truncate(text, max_length=80):
    """Truncate text with an ellipsis if it exceeds max_length."""
    if len(text) <= max_length:
        return text
    return text[:max_length - 3] + "..."


# ────────────────────── PDF SAFETY ──────────────────────

def make_pdf_safe(text):
    """
    Replace Unicode characters that can't be encoded in latin-1
    with safe ASCII alternatives. Required for FPDF's built-in fonts.
    """
    replacements = {
        "•": "-",
        "✔": "[OK]",
        "❌": "[X]",
        "↔": "<->",
        "→": "->",
        "←": "<-",
        "–": "-",
        "—": "-",
        "\u201c": '"',
        "\u201d": '"',
        "\u2018": "'",
        "\u2019": "'",
        "≥": ">=",
        "≤": "<=",
        "…": "...",
    }
    for k, v in replacements.items():
        text = text.replace(k, v)
    return text.encode("latin-1", "replace").decode("latin-1")
