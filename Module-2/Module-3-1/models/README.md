# Models

This folder contains all trained model weight files (`.pth`).

| File | Description | Used By |
|------|-------------|---------|
| `best_deepfake_detector_v2.pth` | EfficientNet-B0 CNN trained to classify real vs AI images | `detectors/cnn_detector.py` |
| `face_detector_v2.pth` | *(planned)* Face detection model v2 | `detectors/face_detector.py` |
| `shoe_detector_v1.pth` | *(planned)* Object/shoe artifact detector | `detectors/shoe_detector.py` |
| `scene_classifier_v1.pth` | *(planned)* Scene classification model | `detectors/scene_classifier.py` |

> Do **not** commit large `.pth` files to git. Add them to `.gitignore` and distribute via a model registry or shared drive.
