import torch
import timm
from PIL import Image
import warnings
import os

warnings.simplefilter('ignore', Image.DecompressionBombWarning)

class EfficientNetDetector:
    def __init__(self, model_path='models/best_watch_detector.pth'):
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.model = timm.create_model('efficientnet_b3', pretrained=False, num_classes=2)
        
        # Load weights
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model file not found at {model_path}")
            
        state_dict = torch.load(model_path, map_location=self.device)
        if 'state_dict' in state_dict:
            state_dict = state_dict['state_dict']
        elif 'model' in state_dict:
            state_dict = state_dict['model']
            
        self.model.load_state_dict(state_dict)
        self.model.to(self.device)
        self.model.eval()
        
        # Prepare transform
        data_config = timm.data.resolve_data_config({}, model=self.model)
        self.transform = timm.data.create_transform(**data_config, is_training=False)
        
    def predict(self, image_path: str) -> float:
        """
        Returns the probability of the image being AI-generated (0.0 to 1.0).
        """
        try:
            img = Image.open(image_path).convert('RGB')
            img_tensor = self.transform(img).unsqueeze(0).to(self.device)
        except Exception as e:
            print(f"Error loading image in EfficientNet: {e}")
            return 0.5 # Neutral if error
            
        with torch.no_grad():
            outputs = self.model(img_tensor)
            probabilities = torch.nn.functional.softmax(outputs, dim=1)[0]
            # Index 0 is Ai, Index 1 is Real based on our mapping
            ai_prob = probabilities[0].item()
            
        return ai_prob
