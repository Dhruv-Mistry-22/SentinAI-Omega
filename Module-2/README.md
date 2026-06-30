# 🔍 SentinAI Omega — Module 3: Object Detection System

> **AI vs Real Image Classifier** | CLIP-Powered Routing | Multi-Category Forensic Detection

A unified CLI system that automatically detects whether a product image (Shoe, Handbag, or Watch) was **AI-generated** or taken with a **real camera**, using a combination of deep learning models and forensic analysis.

---

## 🧠 How It Works

```
You provide an image
        ↓
CLIP (ViT-B-32) auto-detects category
        ↓
Routes to the correct specialist module:
  👟 Shoe    → Module-3-1  (SentinAI EfficientNet-B0)
  👜 Handbag → Module-3-2  (EfficientNet-B3 + ELA + FFT + EXIF)
  ⌚ Watch   → Module-3-3  (WatchBrain V2.0 Ensemble)
        ↓
Prints colour-coded verdict + confidence score
```

**Verified Accuracy:** 5/5 on independent test dataset (100% category routing + 100% AI/Real verdict)

---

## 📁 Repository Structure

```
Module-3/
├── classifier.py              ← 🚀 Main entry point (run this)
├── category_router.py         ← CLIP-based zero-shot category detector
├── run_tests.py               ← Batch accuracy tester
├── requirements.txt           ← All dependencies (install this first)
│
├── independent_test/          ← 5-image test dataset (AI + Real mix)
│   ├── ai_handbag.png
│   ├── ai_handbag2.jpg
│   ├── ai_watch.jpg
│   ├── real_handbag.jpg
│   └── real_watch2.jpg
│
├── Module-3-1/                ← 👟 Shoe AI Detector (SentinAI)
│   ├── run.py
│   ├── detectors/             ← CNN, forensic, metadata, semantic detectors
│   ├── engines/               ← Voting + risk engine
│   └── models/shoe/
│       └── best_shoe_detector.pth     ← Trained model (41 MB)
│
├── Module-3-2/                ← 👜 Handbag AI Detector
│   ├── src/
│   │   ├── cli.py
│   │   ├── config.py
│   │   └── modules/           ← classifier, metadata, artifacts, spectral
│   └── models/
│       └── best_handbag_detector_v2.pth   ← Trained model (41 MB)
│
└── Module-3-3/                ← ⌚ Watch AI Detector (WatchBrain V2.0)
    ├── app.py
    ├── src/
    │   ├── ensemble.py        ← WatchBrainEnsemble
    │   └── detectors/         ← EfficientNet, artifact, metadata
    └── models/
        └── best_watch_detector.pth    ← Trained model (41 MB)
```

---

## ⚙️ Setup — Get Running in 3 Steps

### Prerequisites
- **Python 3.10 or 3.12** (recommended)
- **pip** package manager
- ~2 GB free disk space (for PyTorch + CLIP model download)

---

### Step 1 — Clone the branch

```bash
git clone --branch object-detection https://github.com/Dhruv-Mistry-22/SentinAI-Omega.git
cd SentinAI-Omega
```

---

### Step 2 — Install all dependencies

```bash
pip install -r requirements.txt
```

> ⚠️ **PyTorch Note:** If you have a GPU (CUDA), install the GPU version of PyTorch first for faster inference:
> ```bash
> pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121
> pip install -r requirements.txt
> ```
> For CPU-only (works fine for inference), the default `pip install -r requirements.txt` is enough.

> 📝 **First run:** CLIP's model weights (~350 MB) will be auto-downloaded from HuggingFace on first use and cached locally. This only happens once.

---

### Step 3 — Run the classifier

```bash
python classifier.py
```

That's it. A file picker will open. Select any shoe, handbag, or watch image.

---

## 🖥️ Usage

```bash
# Interactive — opens file picker, CLIP auto-detects category
python classifier.py

# Direct path — CLIP auto-detects category from filename
python classifier.py path/to/image.jpg

# Force a specific category (skip CLIP, faster)
python classifier.py image.jpg --cat shoe
python classifier.py image.jpg --cat handbag
python classifier.py image.jpg --cat watch

# List all modules and check they are ready
python classifier.py --list

# Run independent accuracy test (5 images, shows ground truth vs prediction)
python run_tests.py
```

---

## 📊 Output Example

```
══════════════════════════════════════════════════════════════════════
   Smart Image Classifier  —  AI vs Real Detection Router
   Shoe • Handbag • Watch  |  CLIP-Powered  |  Terminal-Native
══════════════════════════════════════════════════════════════════════

  STEP 1 — Category Detection
  Method   :  CLIP (open-clip-torch)

  👟 Shoe        [░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░]   0.0%
  👜 Handbag     [████████████████████████████████] 100.0%  ◄ DETECTED
  ⌚ Watch       [░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░]   0.0%

  STEP 2 — Detection Result
  Module    :  👜 Handbag AI Detector

  Verdict   :  AI
  Confidence:  86.4%

  AI Generated   [█████████████████░░░░░░░░░░░░░░░]  86.4%
  Real / Camera  [███░░░░░░░░░░░░░░░░░░░░░░░░░░░░░]  13.6%

  FINAL VERDICT  :  AI GENERATED
  FINAL CONFIDENCE: 86.4%
```

---

## 🔬 Module Details

| Module | Category | Architecture | Extra Forensics |
|--------|----------|-------------|-----------------|
| Module-3-1 | 👟 Shoe | EfficientNet-B0 | CNN + Semantic + Forensic + Metadata ensemble |
| Module-3-2 | 👜 Handbag | EfficientNet-B3 | ELA (Error Level Analysis) + FFT Spectral + EXIF |
| Module-3-3 | ⌚ Watch | EfficientNet-B0 | WatchBrain V2.0 — Artifact + Metadata + CNN |

---

## 🛡️ Fallback Logic

If a module's model file is missing, the system **automatically falls back** to the next available module with a warning — it never crashes silently.

---

## 🧪 Independent Test Results

| Image | True Category | Predicted | True Label | Predicted | Confidence |
|-------|--------------|-----------|-----------|-----------|-----------|
| ai_handbag.png | Handbag | ✅ Handbag | AI | ✅ AI | 86.4% |
| ai_handbag2.jpg | Handbag | ✅ Handbag | AI | ✅ AI | 93.0% |
| ai_watch.jpg | Watch | ✅ Watch | AI | ✅ AI | 84.5% |
| real_handbag.jpg | Handbag | ✅ Handbag | REAL | ✅ REAL | 92.0% |
| real_watch2.jpg | Watch | ✅ Watch | REAL | ✅ REAL | 85.5% |

**Category Accuracy: 5/5 (100%) | Verdict Accuracy: 5/5 (100%)**

---

## ⚡ Performance

| Step | Time (after first run) |
|------|----------------------|
| CLIP category detection | ~0.5 – 1s |
| Handbag detection | ~0.15 – 0.7s |
| Watch detection | ~0.4 – 0.5s |
| Shoe detection | ~0.5 – 1s |

> First run only: CLIP downloads its weights (~350 MB) — takes ~60s once, then cached.

---

## 🛠️ Troubleshooting

| Issue | Fix |
|-------|-----|
| `ModuleNotFoundError: open_clip` | Run `pip install open-clip-torch` |
| `ModuleNotFoundError: piexif` | Run `pip install piexif` |
| `ModuleNotFoundError: rich` | Run `pip install rich` |
| `ModuleNotFoundError: timm` | Run `pip install timm` |
| CLIP takes 60s on first run | Normal — it's downloading weights. Will be fast after. |
| `tkinter` not found (Linux) | Run `sudo apt-get install python3-tk` |
| Model not found error | Make sure `.pth` files exist in each module's `models/` folder |

---

## 📦 Dependencies

| Package | Version | Used For |
|---------|---------|---------|
| `torch` | ≥ 2.0.0 | Deep learning inference |
| `torchvision` | ≥ 0.15.0 | Image transforms |
| `timm` | ≥ 0.9.0 | EfficientNet model loading |
| `open-clip-torch` | ≥ 3.2.0 | CLIP zero-shot category routing |
| `transformers` | ≥ 4.35.0 | HuggingFace fallback |
| `Pillow` | ≥ 10.0.0 | Image I/O |
| `opencv-python` | ≥ 4.8.0 | Image preprocessing |
| `numpy` | ≥ 1.24.0 | Numerical operations |
| `scipy` | ≥ 1.11.0 | FFT spectral analysis |
| `piexif` | ≥ 1.1.3 | EXIF metadata extraction |
| `rich` | ≥ 13.0.0 | Terminal UI (Module-3-2) |

---

*Built for SentinAI Omega Hackathon — Module 3: Object Detection Track*
