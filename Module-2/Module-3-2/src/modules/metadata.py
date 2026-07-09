import piexif
from PIL import Image

def analyze_metadata(img_path_or_pil):
    """
    Returns an AI probability score based on EXIF:
    - 1.0 if explicit AI signature found (Midjourney, DALL-E)
    - 0.0 if explicit camera hardware found (Apple, Canon, Sony)
    - 0.5 if no EXIF (neutral, common for social media)
    """
    ai_signatures = ["midjourney", "dall-e", "stable diffusion", "automatic1111", "comfyui"]
    camera_brands = ["apple", "canon", "nikon", "sony", "fujifilm", "samsung", "google"]
    
    # We need a file path to reliably read EXIF if it's a file, or try from PIL
    try:
        if isinstance(img_path_or_pil, str):
            exif_dict = piexif.load(img_path_or_pil)
        else:
            if "exif" in img_path_or_pil.info:
                exif_dict = piexif.load(img_path_or_pil.info["exif"])
            else:
                return 0.5, "No EXIF data found (Neutral)."
    except:
        return 0.5, "Could not parse EXIF data (Neutral)."

    # Flatten EXIF values to strings for searching
    exif_strings = []
    for ifd in ("0th", "Exif", "GPS", "1st"):
        for tag in exif_dict.get(ifd, {}):
            val = exif_dict[ifd][tag]
            if isinstance(val, bytes):
                try:
                    exif_strings.append(val.decode('utf-8').lower())
                except:
                    pass
            elif isinstance(val, str):
                exif_strings.append(val.lower())
                
    exif_text = " ".join(exif_strings)
    
    for sig in ai_signatures:
        if sig in exif_text:
            return 1.0, f"Found AI Signature: {sig.title()}"
            
    for brand in camera_brands:
        if brand in exif_text:
            return 0.0, f"Found Camera Hardware: {brand.title()}"
            
    # Check if there is basic photo info
    if len(exif_text) > 10:
        return 0.3, "Generic metadata found, likely Real but inconclusive."
        
    return 0.5, "Minimal metadata found (Neutral)."
