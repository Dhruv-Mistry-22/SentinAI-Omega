# 🛡️ SentinAI — AI vs Real Image Detection System

> **A modular, pluggable, terminal-native AI image detection framework.**
> Designed to tell you whether an image is **AI-generated** or a **real photograph** — with evidence.

---

## 🎯 What This System Does

SentinAI analyses images and produces a **detailed, evidence-backed verdict**:

| Verdict | Meaning |
|---------|---------|
| ✅ LIKELY_REAL_AUTHENTIC | Very likely a real photograph |
| ✔  PROBABLY_REAL | Probably real, minor signals |
| ❓ SUSPICIOUS_UNCLEAR | Mixed signals, hard to tell |
| ⚠️ LIKELY_AI_GENERATED | Strong signs of AI generation |
| 🚨 HIGH_RISK_AI_GENERATED | Almost certainly AI-generated |

It does this by running one or more **specialist detectors**, each looking for different evidence,
then combining their results using a **weighted ensemble voting system**.

---

## 🏗️ How It Works — System Architecture

```
python run.py
      │
      ▼
┌─────────────────────────────────────────────────┐
│          STEP 1: Detector Selection Menu         │
│  Choose which detector(s) to run (or press A)   │
└─────────────────────┬───────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────┐
│          STEP 2: File Picker Window              │
│  Native OS file browser — pick your image       │
└─────────────────────┬───────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────┐
│          STEP 3: Detectors Run in Order          │
│                                                 │
│  [1] Shoe AI Detector     ← PRIMARY (63%)       │
│  [2] Forensic Analyser    ← pixel stats (21%)   │
│  [3] Metadata Detector    ← EXIF check  (5%)    │
│  [4] CLIP Semantic        ← zero-shot   (10%)   │
│  [5] CIFAKE CNN           ← general     (5%)    │
└─────────────────────┬───────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────┐
│          STEP 4: Risk Engine                     │
│  Weighted average of all AI probability scores  │
│  Shoe detector = 63% of the final score         │
└─────────────────────┬───────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────┐
│          STEP 5: Ensemble Voting                 │
│  Each detector votes AI or REAL                 │
│  Consensus adjusts final confidence ±5-10 pts   │
└─────────────────────┬───────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────┐
│          STEP 6: Terminal Report                 │
│  Per-detector verdict + ASCII confidence bars   │
│  Evidence reasons for every decision            │
│  JSON report auto-saved to reports/             │
└─────────────────────────────────────────────────┘
```

---

## 🔍 Current Detectors

### 1. 🥇 Shoe AI Detector `[PRIMARY]`
- **Weight: 63%** — dominates the final score
- **Model:** `models/shoe/best_shoe_detector.pth` (EfficientNet-B0, fine-tuned on shoe images)
- **What it checks:** AI-generated vs real footwear at the pixel and structural level
- **Catches:**
  - Over-smooth soles (AI doesn't know how rubber wears)
  - Impossible stitching geometry
  - Unnatural lace symmetry
  - Texture uniformity typical of GAN/diffusion outputs
- **Trained on:** Labelled AI-generated shoe images vs real product photographs
- **Status:** ✅ Ready — model file present

---

### 2. 🔬 Forensic Analyser
- **Weight: 21%**
- **No model needed** — pure mathematical analysis
- **What it checks:** Pixel-level statistical signals in the image
  - **Entropy:** Measures pixel randomness. AI images tend to be too uniform (low entropy)
  - **FFT (Fast Fourier Transform):** Analyses frequency spectrum. AI images show unnatural regularity
  - **Laplacian Variance:** Measures sharpness. AI images are often over-smooth
- **Works on:** Any image type — domain-agnostic
- **Status:** ✅ Ready — always available

---

### 3. 📋 Metadata / EXIF Detector
- **Weight: 5%**
- **No model needed** — reads image file metadata
- **What it checks:**
  - Does the image have EXIF data? (Real camera photos always do)
  - Is there a camera Make/Model recorded? (AI images almost never have this)
  - Does the software tag match a known AI tool? (Midjourney, DALL-E, Stable Diffusion, etc.)
  - Is GPS data present? (Strong real-photo indicator)
- **Known limitation:** Many social media platforms strip EXIF — absence ≠ AI
- **Status:** ✅ Ready — always available

---

### 4. 🧠 CLIP Semantic Detector
- **Weight: 10%**
- **Model:** Downloads `openai/clip-vit-base-patch32` (~600 MB, first run only)
- **What it checks:** Semantic understanding — what *kind* of image is this?
  - Runs zero-shot classification against: Real photo / AI-generated / CGI / Illustration
- **Known limitation for shoes:** Product/studio shoe photos often score high as "CGI"
  because of clean backgrounds and even lighting. **This is a known false positive.**
  The system keeps CLIP's weight low (10%) precisely because of this.
- **Status:** ✅ Ready — downloads on first use

---

### 5. 🤖 CIFAKE CNN Detector
- **Weight: 5%** (intentionally very low)
- **Model:** `models/cnn/best_deepfake_detector_v2.pth` (EfficientNet-B0)
- **Trained on:** [CIFAKE dataset](https://www.kaggle.com/datasets/birdy654/cifake-real-and-ai-generated-synthetic-images)
  — 60,000 real CIFAR-10 photos + 60,000 AI-generated equivalents
- **What it checks:** General AI-generation patterns in pixel textures and frequencies
- **Why low weight:** Trained on generic small images (32×32 CIFAR-10 scale),
  not shoe-specific. It is a useful **cross-check signal**, not a domain expert.
- **Status:** ❌ Model file missing (`models/cnn/best_deepfake_detector_v2.pth`)

---

## ⚖️ The Weight System — Why It Matters

The final confidence score is a **weighted average** of all detector AI-probability scores:

```
Final Score = Σ (detector_ai_probability × detector_weight)
```

**Current weights (normalised):**

```
Shoe AI Detector  [PRIMARY]  ████████████████████████████████  63%
Forensic Analyser             ████████████                     21%
CLIP Semantic Detector        ████                             10%
Metadata / EXIF Detector      ██                                5%
CIFAKE CNN Detector           ██                                5%
```

**Why shoe gets 63%:**
The shoe detector is the **domain expert**. It was specifically trained to distinguish
AI-generated shoes from real ones. General models like CLIP and CIFAKE CNN were not
trained on shoes and frequently misfire on product photography. Their low weight means
they add useful *signal* without being able to *override* the domain expert.

**Real-world impact:**
On a real shoe photo where CLIP incorrectly said AI at 83.9%:
- Old system (equal weights): `SUSPICIOUS_UNCLEAR` at 39.7% ❌
- New system (shoe-weighted): `LIKELY_REAL_AUTHENTIC` at 16.7% ✅

---

## 🚀 Quick Start

### Install
```bash
pip install -r requirements.txt
```

### Run (interactive)
```bash
python run.py
```
1. Detector table shows → pick detector(s) or press **A** for all
2. Press **Enter** to auto-select the Shoe AI Detector (PRIMARY)
3. File picker window opens → select your image
4. Report prints in terminal
5. JSON report auto-saved to `reports/`

### Other modes
```bash
python run.py --list       # Show all installed detectors
python run.py --all        # Skip menu, run ALL detectors, then pick image
python run.py --no-save    # Don't write JSON to reports/
```

---

## 📁 Folder Structure

```
Module_3/
│
├── run.py                      ← MAIN ENTRY POINT — start here
├── config.py                   ← Central config (weights, thresholds, paths)
├── requirements.txt
├── README.md
│
├── detectors/                  ← One file = One detector (pluggable)
│   ├── __init__.py
│   ├── shoe_detector.py        ← PRIMARY: AI vs real shoe classifier
│   ├── forensic_detector.py    ← Entropy + FFT + sharpness (no model)
│   ├── metadata_detector.py    ← EXIF camera/software fingerprint (no model)
│   ├── semantic_detector.py    ← CLIP zero-shot semantic classifier
│   └── cnn_detector.py         ← CIFAKE EfficientNet general classifier
│
├── models/                     ← One sub-folder per detector's trained model
│   ├── shoe/
│   │   ├── best_shoe_detector.pth     ✅ Present
│   │   └── shoe_classes.json
│   └── cnn/
│       └── best_deepfake_detector_v2.pth   ❌ Missing (add to enable)
│
├── engines/                    ← Scoring, voting, and discovery logic
│   ├── __init__.py
│   ├── registry.py             ← Auto-discovers detectors from detectors/
│   ├── risk_engine.py          ← Combines detector results into final verdict
│   └── voting_engine.py        ← Ensemble consensus voting
│
├── datasets/                   ← Training data
├── Evaluation/                 ← Test images and CSV results
└── reports/                    ← Auto-saved JSON report from every run
```

---

## 🔌 How to Add a New Detector

Adding a new detector requires **one file** and a model:

### Step 1 — Create `detectors/my_detector.py`

```python
# 1. Metadata — required by the registry for auto-discovery
DETECTOR_INFO = {
    "name":        "My Detector",
    "description": "What this detector checks and how.",
    "model_file":  "models/mydetector/model.pth",  # or None if no model needed
    "version":     "v1.0",
    "category":    "my-category",
    "speed":       "fast",
    "priority":    6,   # Lower number = appears first in the menu
}

# 2. Availability check — called by the registry at startup
def is_available() -> bool:
    from pathlib import Path
    return Path("models/mydetector/model.pth").exists()

# 3. Main detection function — called by run.py
def detect(image_path: str) -> dict:
    # ... your logic here ...
    return {
        "detector":         DETECTOR_INFO["name"],
        "verdict":          "AI",      # "AI" | "REAL"
        "confidence":       0.85,      # 0.0 to 1.0
        "ai_probability":   0.85,
        "real_probability": 0.15,
        "reasons":          [          # Human-readable evidence
            "Reason 1 why this is AI",
            "Reason 2 supporting the verdict",
        ],
        "raw":              {},        # Optional raw scores for debugging
        "error":            None,
    }
```

### Step 2 — Add its weight to `engines/risk_engine.py`

```python
_PREFERRED_WEIGHTS: dict[str, float] = {
    "Shoe AI Detector  [PRIMARY]": 0.60,
    "My Detector":                 0.25,   # ← Add this line
    ...
}
```

### Step 3 — That's it
Run `python run.py --list` — your detector appears automatically. ✅

---

## 📊 Understanding the Terminal Report

```
  DETECTOR 1/4:  Shoe AI Detector  [PRIMARY]
  ──────────────────────────────────────────
  Verdict   :  REAL
  Confidence:  100.0%

  AI Generated   [░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░]   0.0%
  Real / Camera  [████████████████████████████████] 100.0%

  Evidence:
    • Object detector classifies footwear as real (100.0% confidence).
    • Very high confidence — shoe displays natural manufacturing imperfections.
```

Each block shows:
- **Verdict** — AI or REAL for that detector
- **Confidence** — how confident that detector is
- **ASCII bars** — visual AI vs Real probability
- **Evidence** — human-readable reasons behind the verdict

---

## ⚙️ Configuration (`config.py`)

All global settings in one place:

```python
# Detection thresholds
THRESHOLDS = {
    "HIGH_RISK_AI":  70,   # ≥ 70%  →  🚨 HIGH_RISK_AI_GENERATED
    "LIKELY_AI":     55,   # ≥ 55%  →  ⚠️  LIKELY_AI_GENERATED
    "SUSPICIOUS":    35,   # ≥ 35%  →  ❓ SUSPICIOUS_UNCLEAR
    "PROBABLY_REAL": 20,   # ≥ 20%  →  ✔  PROBABLY_REAL
    # < 20%          →  ✅ LIKELY_REAL_AUTHENTIC
}

# Detector weights (raw — normalised automatically)
ENGINE_WEIGHTS = {
    "shoe":     0.60,   # PRIMARY — domain expert
    "forensic": 0.20,   # pixel-level, domain-agnostic
    "semantic": 0.10,   # CLIP — general, keep low for shoes
    "cnn":      0.05,   # CIFAKE — general, keep very low
    "metadata": 0.05,   # EXIF — useful but limited
}

# Reports
AUTO_SAVE_REPORTS = True    # Save JSON to reports/ after every run
```

---

## 🗺️ Future Scope — Detector Roadmap

The system is designed to grow. Each future detector follows the same interface:
drop a file in `detectors/`, add a weight in `engines/risk_engine.py`.

| Phase | Detector | What it detects | Priority |
|-------|----------|-----------------|----------|
| **Phase 2** | `face_detector.py` | AI-generated faces, facial consistency | High |
| **Phase 2** | `eye_mouth_detector.py` | Eye symmetry, mouth artifacts, gaze | High |
| **Phase 2** | `skin_texture_detector.py` | Over-smooth skin, missing pores | High |
| **Phase 3** | `bag_detector.py` | AI vs real handbags/accessories | Medium |
| **Phase 3** | `scene_detector.py` | AI-generated backgrounds, landscapes | Medium |
| **Phase 3** | `text_in_image_detector.py` | Garbled AI-generated text in images | Medium |
| **Phase 3** | `gan_fingerprint_detector.py` | GAN checkerboard spectral artifacts | Medium |
| **Phase 4** | `video_frame_detector.py` | Run detection on every video frame | Future |
| **Phase 4** | `temporal_consistency.py` | Deepfake detection across video frames | Future |
| **Phase 4** | `audio_deepfake_detector.py` | AI-synthesised voice detection | Future |
| **Phase 5** | `meta_ensemble.py` | Train a model on top of all detectors | Future |
| **Phase 5** | `report_exporter.py` | Export reports as PDF/HTML | Future |

---

## 📋 Requirements

```
torch>=2.0.0
torchvision>=0.15.0
timm>=0.9.0
transformers>=4.35.0
Pillow>=10.0.0
opencv-python>=4.8.0
scipy>=1.11.0
numpy>=1.24.0
```

- **Python:** 3.10+
- **GPU:** Optional (3–5× faster for Shoe CNN and CLIP)
- **RAM:** 4 GB minimum, 8 GB recommended
- **Storage:** ~600 MB (CLIP downloads on first run)

---

## 🔄 Version History

| Version | Date | Key Changes |
|---------|------|-------------|
| **v3.1** | 2026-06-06 | Shoe detector promoted to PRIMARY (63% weight). CLIP/CNN weight cut to prevent general models overriding domain expert. CLIP CGI false-positive warning added. |
| v3.0 | 2026-06-06 | Full re-engineering. Modular pluggable architecture. Terminal CLI. Auto-discovery registry. JSON reports. |
| v2.1 | 2026-06-04 | Ensemble voting engine. Reweighted detectors. Lower thresholds. |
| v2.0 | — | 7-engine deepfake detector with CNN + facial analysis. |
| v1.0 | — | Initial CNN-only deepfake detector. |

---

## 💡 Key Design Principles

1. **Domain expert wins** — a detector trained on shoes knows shoes better than a general model
2. **Pluggable by design** — add new detectors without touching any existing code
3. **Transparent reasoning** — every verdict comes with human-readable evidence
4. **General models assist, they don't decide** — CLIP and CIFAKE CNN are cross-checks, not authorities
5. **No UI** — pure terminal, fast, scriptable

---

**Status:** ✅ Active Development
**Primary Focus:** Shoe AI Detection
**Interface:** Terminal
**Last Updated:** 2026-06-06
