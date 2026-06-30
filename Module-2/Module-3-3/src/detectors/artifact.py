import cv2
import numpy as np
from PIL import Image

class ArtifactDetector:
    def __init__(self):
        pass
        
    def predict(self, image_path: str) -> float:
        """
        Analyzes the image for high-frequency artifacts or overly smooth textures
        common in AI-generated images.
        Returns a score from 0.0 to 1.0 (1.0 = highly likely to be AI).
        """
        try:
            # Read image in grayscale
            # Using PIL then convert to numpy to handle weird paths or formats better
            img_pil = Image.open(image_path).convert('L')
            img = np.array(img_pil)
            
            # Metric 1: Laplacian Variance (Blur/Texture detail)
            # Real photos often have natural noise/blur. AI images are sometimes overly sharp or have zero natural noise.
            laplacian_var = cv2.Laplacian(img, cv2.CV_64F).var()
            
            # Scale laplacian variance to a 0-1 range heuristically
            # These thresholds are heuristic and would typically be tuned on a validation set
            if laplacian_var > 2000:
                score = 0.8  # Unnaturally sharp
            elif laplacian_var < 100:
                score = 0.7  # Unnaturally smooth
            else:
                score = 0.3  # Normal range for real photos
                
            # Add slight randomness/heuristic based on noise pattern
            # Calculate standard deviation of the image
            std_dev = np.std(img)
            if std_dev > 80:
                score = min(1.0, score + 0.1) # Extremely high contrast (often AI lighting)
                
            return score
            
        except Exception as e:
            print(f"Error in ArtifactDetector: {e}")
            return 0.5
