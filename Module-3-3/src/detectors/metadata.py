from PIL import Image, ExifTags

class MetadataDetector:
    def __init__(self):
        # Common EXIF tags found in real camera photos
        self.camera_tags = ['Make', 'Model', 'LensModel', 'FocalLength', 'ExposureTime', 'ISOSpeedRatings']
        
        # Software signatures common in AI generators or heavy editing
        self.ai_signatures = [
            'midjourney', 'stable diffusion', 'sdxl', 'flux', 'ideogram', 
            'dall-e', 'chatgpt', 'recraft', 'ai generated', 'gimp', 'photoshop'
        ]
        
    def predict(self, image_path: str) -> float:
        """
        Analyzes EXIF metadata.
        Returns a score from 0.0 to 1.0 (1.0 = highly likely to be AI).
        """
        try:
            img = Image.open(image_path)
            exif_data = img.getexif()
            
            if not exif_data:
                # No EXIF data is extremely common for AI generated images
                return 0.85 
                
            has_camera_info = False
            has_ai_sig = False
            
            for tag_id, value in exif_data.items():
                tag = ExifTags.TAGS.get(tag_id, tag_id)
                val_str = str(value).lower()
                
                # Check for camera info
                if tag in self.camera_tags:
                    has_camera_info = True
                    
                # Check for AI signatures in software tag or others
                if any(sig in val_str for sig in self.ai_signatures):
                    has_ai_sig = True
                    
            if has_ai_sig:
                return 1.0
            elif has_camera_info:
                return 0.1 # Very likely real
            else:
                return 0.7 # Has some EXIF but no camera details
                
        except Exception as e:
            print(f"Error in MetadataDetector: {e}")
            return 0.5
