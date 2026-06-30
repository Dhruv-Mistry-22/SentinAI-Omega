# 🧠 SentienOmega — Unified AI Detection Platform

> A hackathon-grade, multi-module AI detection platform combining **Document Plagiarism & AI Writing Detection** with **Smart Image Forgery Classification** — served through a single unified FastAPI web interface.

---

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Folder Structure](#folder-structure)
- [Modules](#modules)
  - [Module 1 - Document Plagiarism & AI Detection](#module-1---document-plagiarism--ai-detection)
  - [Module 2 - Smart Image Classifier](#module-2---smart-image-classifier-ai-vs-real)
- [Web Application](#web-application)
- [API Reference](#api-reference)
- [Installation & Setup](#installation--setup)
- [Running the System](#running-the-system)
- [Testing](#testing)
- [Tech Stack](#tech-stack)
- [Known Fixes & Engineering Notes](#known-fixes--engineering-notes)

---

## Overview

SentienOmega is a dual-capability AI detection system built for academic and commercial use cases. It provides:

1. **Document Analysis** - Upload two or more student assignments / documents. The system detects plagiarism using a 4-layer similarity engine and also analyzes the AI-writing characteristics of each document. A detailed color-coded **PDF report is auto-generated and downloaded**.

2. **Image Classification** - Upload any image of a shoe, handbag, or watch. The system uses **CLIP** to auto-detect the object category, then routes it to a specialized **AI-vs-Real forgery detector** powered by fine-tuned EfficientNet models + forensic analysis.

---

## Architecture

```
User Browser
    |
    v
FastAPI Server  (app.py - port 8000)
    |
    |---> /api/module1/analyze  --->  api_module1.py  --->  Module-1/src/*
    |                                                        (PDF report returned)
    |
    +---> /api/module2/classify --->  api_module2.py  --->  Module-2/classifier.py
                                                              |-- Module-3-1 (Shoe)
                                                              |-- Module-3-2 (Handbag)
                                                              +-- Module-3-3 (Watch)
```

---

## Folder Structure

```
SentienOmega/
|
|-- app.py                    # Main FastAPI server - routes, CORS, static serving
|-- api_module1.py            # Web wrapper for Module 1 (document analysis + PDF)
|-- api_module2.py            # Web wrapper for Module 2 (image classification)
|-- requirements_web.txt      # Web server dependencies only
|-- test_endpoints.py         # API smoke tests (runs against live server)
|-- test_import.py            # Import path debugging utility
|-- README.md                 # This file
|
|-- static/                   # Frontend web application
|   |-- index.html            # Main SPA page (sidebar navigation)
|   |-- styles.css            # Full dark-theme glassmorphism CSS
|   +-- script.js             # API calls, drag-drop, PDF download logic
|
|-- Module-1/                 # Document Plagiarism & AI Writing Detection
|   |-- main.py               # Standalone CLI entry point
|   |-- requirements.txt      # Module 1 Python dependencies
|   |-- sample_assignments/   # Test documents (student_A.txt, student_B.txt)
|   |-- output/               # CLI-generated PDF/Excel reports
|   |-- tests/                # Unit tests for Module 1
|   +-- src/                  # Core engine
|       |-- __init__.py
|       |-- reader.py         # File reader (TXT, PDF, DOCX + metadata extraction)
|       |-- cleaner.py        # Text normalization and NLTK preprocessing
|       |-- analyzer.py       # 4-layer similarity engine (TF-IDF, Jaccard, etc.)
|       |-- classifier.py     # Plagiarism verdict classifier
|       |-- sentence_matcher.py  # Sentence-level evidence finder
|       |-- ai_detector.py    # AI writing characteristics analyzer (v4)
|       |-- style_analyzer.py # Writing style fingerprinting
|       |-- report_generator.py  # Professional PDF report generator (fpdf2)
|       |-- excel_exporter.py # Excel summary exporter
|       +-- utils.py          # PDF-safe encoding, progress bar, console helpers
|
+-- Module-2/                 # Smart Image Classifier (AI vs Real Detection Router)
    |-- classifier.py         # Main unified router + CLIP category detection
    |-- category_router.py    # Standalone CLIP category routing
    |-- run_tests.py          # Module 2 test runner
    |-- requirements.txt      # Module 2 Python dependencies
    |-- independent_test/     # Test images (ai_watch.jpg, etc.)
    |
    |-- Module-3-1/           # Shoe AI Detector - SentinAI (EfficientNet-B0)
    |   |-- run.py            # Standalone CLI
    |   |-- config.py         # Model config and thresholds
    |   |-- detectors/        # CNN, forensic, metadata, semantic, shoe detectors
    |   |-- engines/          # Inference engines
    |   |-- models/           # .pth model weights (shoe/best_shoe_detector.pth)
    |   |-- datasets/         # Training datasets
    |   |-- Evaluation/       # Evaluation scripts and results
    |   +-- reports/          # Generated analysis reports
    |
    |-- Module-3-2/           # Handbag AI Detector (EfficientNet-B3 + Forensics)
    |   |-- src/
    |   |   |-- cli.py        # CLI interface
    |   |   |-- config.py     # Model config
    |   |   |-- modules/      # artifacts, classifier, metadata, spectral detectors
    |   |   +-- retrain.py    # Model retraining script
    |   |-- models/           # .pth model weights (best_handbag_detector_v2.pth)
    |   |-- dataset/          # Handbag training images
    |   +-- independent_test/ # Test handbag images
    |
    +-- Module-3-3/           # Watch AI Detector - WatchBrain V2.0 (Ensemble)
        |-- app.py            # Standalone CLI app
        |-- src/
        |   |-- ensemble.py   # WatchBrainEnsemble class
        |   +-- detectors/
        |       |-- efficientnet.py   # EfficientNet-B3 fine-tuned detector
        |       |-- artifact.py       # Synthetic artifact forensic detector
        |       +-- metadata.py       # EXIF metadata forensic detector
        |-- models/           # .pth model weights (best_watch_detector.pth)
        +-- data/             # Watch training data
```

---

## Modules

### Module 1 - Document Plagiarism & AI Detection

Analyzes 2+ text documents (TXT, PDF, DOCX) for plagiarism and AI-generated writing patterns.

#### Processing Pipeline

**Step 1 - File Reading** (`reader.py`)
- Reads TXT, PDF (via PyPDF2), and DOCX (via python-docx)
- Extracts metadata: filename, word count, file size, timestamps

**Step 2 - Text Cleaning** (`cleaner.py`)
- Lowercases, removes punctuation, stop words
- Uses NLTK tokenization and lemmatization

**Step 3 - 4-Layer Similarity Analysis** (`analyzer.py`)

| Layer | Method | Weight |
|-------|--------|--------|
| 1 | TF-IDF Cosine Similarity | 40% |
| 2 | N-gram Jaccard Similarity | 30% |
| 3 | Structural Fingerprinting | 15% |
| 4 | Writing Style Analysis | 15% |

**Step 4 - Classification** (`classifier.py`)

| Score | Verdict |
|-------|---------|
| >= 85% | COPIED |
| 50-84% | SUSPICIOUS |
| < 50% | ORIGINAL |

Also determines *who copied whom* based on timestamps and content order.

**Step 5 - AI Writing Characteristics** (`ai_detector.py` v4)
- Analyzes hedge word density, bigram repetition, transition phrase frequency, lexical diversity
- Scores each document 0-100% for AI-like characteristics
- Verdicts: `REVIEW RECOMMENDED`, `NOTABLE SIGNALS`, `CONSISTENT WITH HUMAN WRITING`

**Step 6 - PDF Report Auto-Generation** (`report_generator.py`)

Multi-section professional PDF with:
1. Title page with summary statistics
2. Executive summary
3. Per-document verdicts table
4. Color-coded similarity matrix (landscape)
5. Flagged pair analysis with sentence evidence
6. Recommendations section
7. AI writing characteristics per document

The PDF is automatically downloaded to the user's browser.

---

### Module 2 - Smart Image Classifier (AI vs Real)

Classifies images of **shoes**, **handbags**, and **watches** as AI-generated or real photographs.

#### Processing Pipeline

**Step 1 - Category Detection** (`classifier.py` using CLIP)
- Uses OpenAI CLIP (ViT-B-32) zero-shot classification to detect image category
- Falls back to keyword heuristic if CLIP is unavailable
- Supports forced category override from the UI

**Step 2 - Module Routing**

| Category | Module | Detector Name |
|----------|--------|--------------|
| Shoe | Module-3-1 | SentinAI (EfficientNet-B0 + forensics) |
| Handbag | Module-3-2 | Handbag AI Detector (EfficientNet-B3 + ELA + FFT + EXIF) |
| Watch | Module-3-3 | WatchBrain V2.0 (Ensemble) |

**Step 3 - Specialist Detection**

- **Shoe (Module-3-1):** EfficientNet-B0 fine-tuned on shoe datasets + CNN forensic + metadata + semantic detectors
- **Handbag (Module-3-2):** EfficientNet-B3 core model + Error Level Analysis (ELA) + FFT spectral analysis + EXIF metadata forensics
- **Watch (Module-3-3 - WatchBrain V2.0):** Three-component weighted ensemble:
  - EfficientNet-B3: 70% weight (fine-tuned deep visual features)
  - Artifact Detector: 20% weight (synthetic texture / sharpness anomalies)
  - Metadata Detector: 10% weight (EXIF forensics, missing GPS/timestamp)

**Fallback Mechanism:** If the primary module's `.pth` model weights are missing, the system automatically falls back to the next available module.

---

## Web Application

Single-page dark-theme application served at `http://localhost:8000`.

### Features
- Sidebar navigation between Document Analysis and Image Classification
- **Module 1:** Drag-and-drop or file-browse multi-upload (TXT, PDF, DOCX) - triggers auto-PDF download on completion
- **Module 2:** Drag-and-drop image upload with live preview - displays AI/Real verdict with confidence bars and forensic reasons
- Optional Force Category selector (Auto-detect / Shoe / Handbag / Watch)
- Loading spinners during server analysis

---

## API Reference

### `GET /`
Serves the frontend HTML application.

---

### `POST /api/module1/analyze`

Analyze multiple documents for plagiarism and AI writing.

**Request:** `multipart/form-data`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `files` | File[] | Yes | 2 or more documents (TXT, PDF, DOCX) |

**Response:** `application/pdf` downloaded as `SentienOmega_Report.pdf`

**Error (400/500):**
```json
{ "error": "At least 2 documents are required for analysis." }
```

---

### `POST /api/module2/classify`

Classify an image as AI-generated or real.

**Request:** `multipart/form-data`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `image` | File | Yes | Image file (JPG, PNG, WEBP, etc.) |
| `category` | string | No | Force category: `shoe`, `handbag`, or `watch` |

**Response (200):**
```json
{
  "success": true,
  "detected_category": "watch",
  "clip_confidence": 0.92,
  "is_fallback": false,
  "run_category": "watch",
  "result": {
    "detector": "WatchBrain V2.0",
    "verdict": "AI",
    "confidence": 0.8449,
    "ai_probability": 0.8449,
    "real_probability": 0.1551,
    "reasons": [
      "EfficientNet-B3: 99.9% AI probability (weight 70%)",
      "Artifact Detector: 30.0% AI score (weight 20%)",
      "Metadata Detector: 85.0% AI score (weight 10%)",
      "Image metadata strongly suggests synthetic generation (missing/altered EXIF)."
    ],
    "raw": {
      "efficientnet": 0.9999,
      "artifact": 0.3,
      "metadata": 0.85
    },
    "error": null
  }
}
```

---

## Installation & Setup

### Prerequisites
- Python 3.10 or higher
- pip

### Step 1 - Install Web Server Dependencies

```bash
pip install -r requirements_web.txt
```

Contents: `fastapi`, `uvicorn`, `python-multipart`, `jinja2`

### Step 2 - Install Module 1 Dependencies

```bash
pip install -r Module-1/requirements.txt
```

Contents: `scikit-learn`, `PyPDF2`, `python-docx`, `fpdf2`, `nltk`, `openpyxl`

NLTK data is automatically downloaded on first run. To pre-download manually:
```python
import nltk
nltk.download('punkt')
nltk.download('stopwords')
nltk.download('wordnet')
```

### Step 3 - Install Module 2 Dependencies

```bash
pip install -r Module-2/requirements.txt
```

Contents: `torch`, `torchvision`, `timm`, `transformers`, `open-clip-torch`, `Pillow`, `opencv-python`, `numpy`, `scipy`, `piexif`, `rich`

> GPU (CUDA) is optional but recommended for faster EfficientNet inference.

### Step 4 - Model Weights

Ensure the following pre-trained `.pth` files are present:

| Model | Path |
|-------|------|
| Shoe Detector | `Module-2/Module-3-1/models/shoe/best_shoe_detector.pth` |
| Handbag Detector | `Module-2/Module-3-2/models/best_handbag_detector_v2.pth` |
| Watch Detector | `Module-2/Module-3-3/models/best_watch_detector.pth` |

If a model file is missing, the system gracefully falls back to the next available detector.

---

## Running the System

```bash
python app.py
```

Server starts at: **http://localhost:8000**

Alternative (with reload):
```bash
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

---

## Testing

### API Smoke Tests (server must be running first)

```bash
python test_endpoints.py
```

Expected output:
```
Testing Module 1 (Document Analysis)...
[SUCCESS] Module 1 Test Passed!
Files analyzed: 2
Verdicts: ['student_A.txt', 'student_B.txt']

Testing Module 2 (Image Classification)...
[SUCCESS] Module 2 Test Passed!
Detected Category: watch
Verdict: AI
Confidence: 0.8449
```

Test files used:
- Module 1: `Module-1/sample_assignments/student_A.txt` and `student_B.txt`
- Module 2: `Module-2/independent_test/ai_watch.jpg`

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Web Server | FastAPI + Uvicorn |
| Frontend | Vanilla HTML / CSS / JavaScript |
| UI Theme | Dark mode glassmorphism |
| Document Parsing | PyPDF2, python-docx |
| NLP & Similarity | scikit-learn (TF-IDF), NLTK |
| PDF Generation | fpdf2 |
| Excel Export | openpyxl |
| Image Deep Learning | PyTorch, timm (EfficientNet-B0/B3) |
| Zero-shot Routing | OpenAI CLIP (open-clip-torch, ViT-B-32) |
| Image Forensics | OpenCV, scipy (FFT), piexif (EXIF) |
| Terminal CLI | rich (Module-3-2 standalone only) |

---

## Known Fixes & Engineering Notes

### Fix 1 - `src` Namespace Collision (`api_module2.py`)

**Problem:** Both `Module-1/src/` and `Module-2/Module-3-3/src/` use the same Python package name `src`. When both modules are active in the same Python process, importing `src.ensemble` (Module-3-3) would fail silently by picking up Module-1's `src` package instead.

**Fix:** `api_module2.py` implements a safe swap before calling Module 2's detector:
1. Temporarily removes all `Module-1` entries from `sys.path`
2. Pops all `src` and `src.*` entries from `sys.modules`
3. Runs the Module 2 detector
4. Cleans up Module 2's `src` modules
5. Restores `sys.path` and the original `src` modules

This allows both modules to coexist safely in a single FastAPI process.

---

### Fix 2 - Unicode Characters Crashing PDF (`report_generator.py`)

**Problem:** The Helvetica font built into `fpdf2`'s standard mode only supports the latin-1 character set. The AI verdict strings produced by `ai_detector.py` contain em-dashes (`-`), en-dashes, smart quotes, and other Unicode characters that caused a crash during PDF generation.

**Fix:** All `pdf.cell()` calls in the AI Writing Characteristics section of `report_generator.py` now wrap their text with `make_pdf_safe()` (from `src/utils.py`), which replaces all unsupported Unicode characters with ASCII-safe equivalents before they are written.

---

### Fix 3 - Static File 404 Errors (`static/index.html`)

**Problem:** The HTML file referenced `styles.css` and `script.js` using bare relative paths. When served by FastAPI (not via a `file://` URL), these paths resolved relative to the server root rather than the static folder, causing 404 errors and a broken UI.

**Fix:** Changed to absolute server paths `/static/styles.css` and `/static/script.js`, which correctly route through FastAPI's mounted `StaticFiles` handler at `/static`.

---

### Fix 4 - Dynamic Import of `classifier.py` (`api_module2.py`)

**Problem:** `Module-2/classifier.py` cannot be imported via normal `import` statements because its parent directory name (`Module-2`) contains a hyphen, making it an invalid Python package name.

**Fix:** `api_module2.py` uses `importlib.util.spec_from_file_location()` to load `classifier.py` by its absolute file path, bypassing Python's package naming constraints entirely.

---

*SentienOmega - Built for Hackathon. Dual-module AI forensics platform.*
