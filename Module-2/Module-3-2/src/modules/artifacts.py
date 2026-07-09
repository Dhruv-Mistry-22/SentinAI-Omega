import io
from PIL import Image, ImageChops, ImageEnhance
import numpy as np

def perform_ela(img_pil, quality=90):
    """
    Performs Error Level Analysis (ELA) on an image.
    Saves image at a known quality, takes the difference, and enhances it.
    Returns: (ELA Image, AI Score)
    """
    img = img_pil.convert('RGB')
    
    # Save to memory buffer
    buffer = io.BytesIO()
    img.save(buffer, 'JPEG', quality=quality)
    buffer.seek(0)
    
    # Open the re-compressed image
    resaved_img = Image.open(buffer)
    
    # Calculate difference
    ela_img = ImageChops.difference(img, resaved_img)
    
    # Enhance difference to make it visible
    extrema = ela_img.getextrema()
    max_diff = max([ex[1] for ex in extrema])
    if max_diff == 0:
        max_diff = 1
    
    scale = 255.0 / max_diff
    ela_img = ImageEnhance.Brightness(ela_img).enhance(scale)
    
    # Calculate a rough score based on variance
    # High variance usually means real (edges, textures). 
    # Low uniform variance can sometimes mean AI generated.
    # Note: Modern AI often bypasses this, so score is kept close to 0.5 (neutral).
    img_array = np.array(ela_img)
    mean_diff = np.mean(img_array)
    
    # Very heuristic scoring
    if mean_diff < 10:
        score = 0.6  # Unusually smooth compression, slight AI lean
        note = "Unusually smooth compression (AI lean)"
    elif mean_diff > 40:
        score = 0.4  # High compression artifacts, slight Real lean
        note = "High edge artifacts (Real lean)"
    else:
        score = 0.5
        note = "Standard compression pattern (Neutral)"
        
    return ela_img, score, note
