from pathlib import Path
import json

BASE_DIR = Path(__file__).resolve().parent

# Paths
MODEL_PATH = BASE_DIR.parent / "models" / "best_handbag_detector_v2.pth"
CLASSES_JSON = BASE_DIR.parent / "models" / "handbag_classes_v2.json"

# Load Classes
with open(CLASSES_JSON, "r") as f:
    CLASS_MAP = json.load(f)
IDX_TO_NAME = {v: k for k, v in CLASS_MAP.items()}
AI_LABEL = "AI"
REAL_LABEL = "Real"

# Scoring Weights (As per user feedback)
WEIGHTS = {
    "classifier": 0.85,
    "metadata": 0.05,
    "ela": 0.05,
    "fft": 0.05
}

# Image constants
IMG_SIZE = 300  # For EfficientNet-B3
