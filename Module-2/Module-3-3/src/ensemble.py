import os
from .detectors.efficientnet import EfficientNetDetector
from .detectors.artifact import ArtifactDetector
from .detectors.metadata import MetadataDetector

class WatchBrainEnsemble:
    def __init__(self, model_path='models/best_watch_detector.pth'):
        print("Initializing Watch Brain V2.0...")
        self.efficientnet = EfficientNetDetector(model_path)
        self.artifact_det = ArtifactDetector()
        self.metadata_det = MetadataDetector()
        
    def evaluate(self, image_path: str):
        # 1. Get raw scores (probability of being AI)
        eff_score = self.efficientnet.predict(image_path)
        art_score = self.artifact_det.predict(image_path)
        meta_score = self.metadata_det.predict(image_path)
        
        # 2. Apply weights
        final_score = (eff_score * 0.70) + (art_score * 0.20) + (meta_score * 0.10)
        
        verdict = "AI" if final_score > 0.5 else "Real"
        
        # Determine reasoning based on highest contributing anomaly (if AI) or authentic signal (if Real)
        reason = ""
        if verdict == "AI":
            if art_score > 0.7:
                reason = "Strong synthetic texture patterns or unnatural blur/sharpness detected."
            elif meta_score > 0.8:
                reason = "Image metadata strongly suggests synthetic generation (Missing/altered EXIF)."
            else:
                reason = "Deep visual features strongly match known AI generation patterns."
        else:
            if meta_score < 0.3:
                reason = "Authentic camera metadata and natural visual patterns detected."
            else:
                reason = "Visual textures and features strongly align with real photography."
                
        # 3. Format professional output
        print("\n" + "="*40)
        print("         WATCH BRAIN V2.0 RESULTS")
        print("="*40)
        print(f"Final Verdict : {verdict}")
        print(f"Confidence    : {max(final_score, 1 - final_score) * 100:.1f}%\n")
        
        print(f"EfficientNet  : {eff_score * 100:.1f}%")
        print(f"Artifact      : {art_score * 100:.1f}%")
        print(f"Metadata      : {meta_score * 100:.1f}%\n")
        
        print("Reason:")
        print(reason)
        print("="*40 + "\n")
        
        return final_score
