import torch
import torch.nn as nn
import torch.optim as optim
from torchvision import datasets, transforms
from torch.utils.data import DataLoader
import timm
import json
import time
from pathlib import Path

# Config
DATA_DIR = r"D:\Others\Hackathon\Module-3-2\dataset\handbagdataset4k\dataset"
MODEL_SAVE_PATH = r"D:\Others\Hackathon\Module-3-2\models\best_handbag_detector_v2.pth"
CLASSES_JSON = r"D:\Others\Hackathon\Module-3-2\models\handbag_classes_v2.json"
EPOCHS = 5
BATCH_SIZE = 32

Path(r"D:\Others\Hackathon\Module-3-2\models").mkdir(parents=True, exist_ok=True)

# Transforms with RandomResizedCrop as previously discussed to prevent shortcut learning
train_transform = transforms.Compose([
    transforms.RandomResizedCrop(300, scale=(0.5, 1.0)),
    transforms.RandomHorizontalFlip(),
    transforms.ColorJitter(brightness=0.2, contrast=0.2),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
])

# Load Dataset
print(f"Loading dataset from {DATA_DIR}...")
full_dataset = datasets.ImageFolder(root=DATA_DIR, transform=train_transform)
class_map = full_dataset.class_to_idx

with open(CLASSES_JSON, "w") as f:
    json.dump(class_map, f)
print(f"Classes saved: {class_map}")

train_loader = DataLoader(full_dataset, batch_size=BATCH_SIZE, shuffle=True, num_workers=4, pin_memory=True)

# Model
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"Training on: {device}")
model = timm.create_model("efficientnet_b3", pretrained=True, num_classes=len(class_map))
model.to(device)

criterion = nn.CrossEntropyLoss()
optimizer = optim.Adam(model.parameters(), lr=0.001)

# Training Loop
print("Starting training...")
best_loss = float('inf')

for epoch in range(EPOCHS):
    model.train()
    running_loss = 0.0
    start_time = time.time()
    
    for inputs, labels in train_loader:
        inputs, labels = inputs.to(device), labels.to(device)
        
        optimizer.zero_grad()
        outputs = model(inputs)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()
        
        running_loss += loss.item() * inputs.size(0)
        
    epoch_loss = running_loss / len(full_dataset)
    epoch_time = time.time() - start_time
    
    print(f"Epoch {epoch+1}/{EPOCHS} - Loss: {epoch_loss:.4f} - Time: {epoch_time:.1f}s")
    
    if epoch_loss < best_loss:
        best_loss = epoch_loss
        torch.save(model.state_dict(), MODEL_SAVE_PATH)
        print(f"  --> Saved new best model!")

print("Training complete! Model recreated.")
