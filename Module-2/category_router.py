"""
Category Router
===============
Uses OpenAI CLIP (via open-clip-torch) for zero-shot image classification.
Determines which of the three specialist modules should handle the image:
  - shoe     → Module-3-1 (SentinAI)
  - handbag  → Module-3-2 (Handbag AI Detector)
  - watch    → Module-3-3 (WatchBrain V2.0)

Falls back to manual user selection if CLIP is unavailable.
"""

from __future__ import annotations
from pathlib import Path

# ─────────────────────────────────────────────────────────────────────────────
# CLIP LABELS  — more descriptive prompts produce better zero-shot accuracy
# ─────────────────────────────────────────────────────────────────────────────

CLIP_PROMPTS = {
    "shoe": [
        "a photo of a shoe",
        "a photo of a sneaker",
        "a photo of footwear",
        "a photo of a boot",
        "a photo of a sandal",
    ],
    "handbag": [
        "a photo of a handbag",
        "a photo of a purse",
        "a photo of a luxury bag",
        "a photo of a fashion bag",
        "a photo of a tote bag",
    ],
    "watch": [
        "a photo of a wristwatch",
        "a photo of a luxury watch",
        "a photo of a timepiece",
        "a photo of a smartwatch",
        "a photo of a watch",
    ],
}

# Best single representative prompt per category (used as fallback / display)
CATEGORY_LABELS = {
    "shoe":    "a photo of a shoe or sneaker",
    "handbag": "a photo of a handbag or purse",
    "watch":   "a photo of a wristwatch",
}

CATEGORIES = list(CATEGORY_LABELS.keys())   # ["shoe", "handbag", "watch"]


# ─────────────────────────────────────────────────────────────────────────────
# CLIP availability check
# ─────────────────────────────────────────────────────────────────────────────

def _clip_available() -> bool:
    try:
        import open_clip  # noqa: F401
        return True
    except ImportError:
        pass
    try:
        import transformers  # noqa: F401
        return True
    except ImportError:
        pass
    return False


# ─────────────────────────────────────────────────────────────────────────────
# open-clip based routing (preferred)
# ─────────────────────────────────────────────────────────────────────────────

_clip_model   = None
_clip_preproc = None
_clip_tok     = None
_clip_device  = None


def _load_open_clip():
    global _clip_model, _clip_preproc, _clip_tok, _clip_device
    if _clip_model is not None:
        return

    import torch
    import open_clip

    _clip_device = "cuda" if torch.cuda.is_available() else "cpu"
    _clip_model, _, _clip_preproc = open_clip.create_model_and_transforms(
        "ViT-B-32", pretrained="openai"
    )
    _clip_model = _clip_model.to(_clip_device).eval()
    _clip_tok = open_clip.get_tokenizer("ViT-B-32")


def _route_with_open_clip(image_path: str) -> tuple[str, float, dict[str, float]]:
    """
    Returns (category, confidence, {cat: score, ...}) using open-clip.
    Confidence is in range 0–1 (normalised probability for winning category).
    """
    import torch
    from PIL import Image as PILImage

    _load_open_clip()

    img = PILImage.open(image_path).convert("RGB")
    img_t = _clip_preproc(img).unsqueeze(0).to(_clip_device)

    # Build one text prompt per category (average of all variant prompts)
    all_scores: dict[str, float] = {}

    with torch.no_grad():
        img_feat = _clip_model.encode_image(img_t)
        img_feat = img_feat / img_feat.norm(dim=-1, keepdim=True)

        for cat, prompts in CLIP_PROMPTS.items():
            tok = _clip_tok(prompts).to(_clip_device)
            txt_feat = _clip_model.encode_text(tok)
            txt_feat = txt_feat / txt_feat.norm(dim=-1, keepdim=True)
            # cosine similarity, averaged across variants
            sims = (img_feat @ txt_feat.T).squeeze(0)
            all_scores[cat] = sims.mean().item()

    # Softmax over category scores to get probabilities
    import math
    exp_scores = {k: math.exp(v * 100) for k, v in all_scores.items()}  # scale for sharper softmax
    total = sum(exp_scores.values())
    probs = {k: v / total for k, v in exp_scores.items()}

    winner = max(probs, key=probs.get)
    return winner, probs[winner], probs


# ─────────────────────────────────────────────────────────────────────────────
# HuggingFace transformers CLIP fallback
# ─────────────────────────────────────────────────────────────────────────────

def _route_with_transformers(image_path: str) -> tuple[str, float, dict[str, float]]:
    from transformers import CLIPProcessor, CLIPModel
    import torch
    from PIL import Image as PILImage

    model_id = "openai/clip-vit-base-patch32"
    model    = CLIPModel.from_pretrained(model_id)
    proc     = CLIPProcessor.from_pretrained(model_id)
    device   = "cuda" if torch.cuda.is_available() else "cpu"
    model    = model.to(device).eval()

    img    = PILImage.open(image_path).convert("RGB")
    labels = [CATEGORY_LABELS[c] for c in CATEGORIES]
    inputs = proc(text=labels, images=img, return_tensors="pt", padding=True)
    inputs = {k: v.to(device) for k, v in inputs.items()}

    with torch.no_grad():
        out    = model(**inputs)
        logits = out.logits_per_image[0]
        probs_t = logits.softmax(dim=0)

    probs = {CATEGORIES[i]: probs_t[i].item() for i in range(len(CATEGORIES))}
    winner = max(probs, key=probs.get)
    return winner, probs[winner], probs


# ─────────────────────────────────────────────────────────────────────────────
# Manual fallback
# ─────────────────────────────────────────────────────────────────────────────

def _route_manually(
    B: str, CYN: str, WHT: str, YLW: str, R: str
) -> tuple[str, float, dict[str, float]]:
    """Ask the user to choose the category themselves."""
    import os
    if os.environ.get("NON_INTERACTIVE") == "1":
        raise RuntimeError("CLIP models are not available. Please override classification in the UI.")

    print(f"\n  {YLW}[!] CLIP not available — please select the image category manually:{R}\n")
    for i, cat in enumerate(CATEGORIES, 1):
        print(f"  {CYN}{B}[{i}]{R}  {WHT}{cat.capitalize()}{R}")
    print()

    while True:
        raw = input(f"  {CYN}Your choice [1-{len(CATEGORIES)}]: {R}").strip()
        if raw.isdigit() and 1 <= int(raw) <= len(CATEGORIES):
            cat = CATEGORIES[int(raw) - 1]
            probs = {c: (1.0 if c == cat else 0.0) for c in CATEGORIES}
            return cat, 1.0, probs
        print(f"  {YLW}  Invalid — enter a number between 1 and {len(CATEGORIES)}.{R}")


# ─────────────────────────────────────────────────────────────────────────────
# PUBLIC API
# ─────────────────────────────────────────────────────────────────────────────

def route(
    image_path: str,
    *,
    color_helpers: dict | None = None,
) -> tuple[str, float, dict[str, float], str]:
    """
    Classify image into shoe / handbag / watch.

    Returns:
        (category, confidence, scores_dict, method)
        - category    : "shoe" | "handbag" | "watch"
        - confidence  : 0.0–1.0
        - scores_dict : {cat: prob, …}
        - method      : "open_clip" | "transformers" | "manual"
    """
    ch = color_helpers or {}
    B   = ch.get("B",   "")
    CYN = ch.get("CYN", "")
    WHT = ch.get("WHT", "")
    YLW = ch.get("YLW", "")
    R   = ch.get("R",   "")

    # Try open-clip first
    try:
        import open_clip  # noqa: F401
        cat, conf, scores = _route_with_open_clip(image_path)
        return cat, conf, scores, "open_clip"
    except ImportError:
        pass
    except Exception as exc:
        print(f"  {YLW}[!] open-clip error: {exc} — trying transformers…{R}")

    # Try HuggingFace transformers CLIP
    try:
        import transformers  # noqa: F401
        cat, conf, scores = _route_with_transformers(image_path)
        return cat, conf, scores, "transformers"
    except ImportError:
        pass
    except Exception as exc:
        print(f"  {YLW}[!] transformers error: {exc} — falling back to manual…{R}")

    # Final fallback: manual selection
    cat, conf, scores = _route_manually(B, CYN, WHT, YLW, R)
    return cat, conf, scores, "manual"
