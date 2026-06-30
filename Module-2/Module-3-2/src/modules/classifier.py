import torch
import timm
from torchvision import transforms
from PIL import Image
from config import MODEL_PATH, IDX_TO_NAME, IMG_SIZE, AI_LABEL

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = None
transform = None

def load_model():
    global model, transform
    if model is None:
        model = timm.create_model("efficientnet_b3", pretrained=False, num_classes=2)
        model.load_state_dict(torch.load(MODEL_PATH, map_location=device))
        model.to(device)
        model.eval()

        transform = transforms.Compose([
            transforms.Resize((IMG_SIZE, IMG_SIZE)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ])
    return model

def predict(img_path_or_pil):
    load_model()
    if isinstance(img_path_or_pil, str):
        img = Image.open(img_path_or_pil).convert("RGB")
    else:
        img = img_path_or_pil.convert("RGB")
        
    tensor = transform(img).unsqueeze(0).to(device)
    with torch.no_grad():
        outputs = model(tensor)
        probs = torch.softmax(outputs, dim=1)[0]
        
    # Get probability specifically for AI class (for consistent scoring)
    # AI_LABEL is either 0 or 1 depending on json
    ai_idx = None
    for idx, name in IDX_TO_NAME.items():
        if name == AI_LABEL:
            ai_idx = idx
            break
            
    ai_prob = probs[ai_idx].item()
    pred_idx = probs.argmax().item()
    pred_label = IDX_TO_NAME[pred_idx]
    
    return pred_label, ai_prob, tensor, outputs
