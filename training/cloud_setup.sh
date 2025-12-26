#!/bin/bash
# ☁️ CLOUD TRAINING SETUP
# =======================
# Script to run on a rented GPU server (Vast.ai, RunPod, etc.)
# 
# Usage:
#   1. Rent a GPU server (RTX 4090 recommended)
#   2. SSH into the server
#   3. Run: curl -sSL https://raw.githubusercontent.com/... | bash
#   Or copy this script and run it

echo "☁️ Cloud Training Setup for Car Segmentation"
echo "=============================================="
echo ""

# Update system
echo "📦 Updating system..."
apt-get update -qq

# Install Python and pip
echo "🐍 Installing Python..."
apt-get install -y python3 python3-pip python3-venv git wget unzip -qq

# Create virtual environment
echo "📁 Creating virtual environment..."
python3 -m venv /workspace/venv
source /workspace/venv/bin/activate

# Install PyTorch with CUDA
echo "🔥 Installing PyTorch with CUDA..."
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121 -q

# Install other dependencies
echo "📦 Installing dependencies..."
pip install numpy pillow tqdm albumentations -q

# Create workspace
echo "📁 Creating workspace..."
mkdir -p /workspace/training
cd /workspace/training

# Download training scripts
echo "📥 Downloading training scripts..."
cat > train_segmentation.py << 'SCRIPT'
#!/usr/bin/env python3
"""
Car Segmentation Training Script - Cloud Version
"""
import os
import argparse
from pathlib import Path
import numpy as np
from PIL import Image
from tqdm import tqdm

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
import torchvision.transforms.functional as TF
from torch.cuda.amp import autocast, GradScaler

DEVICE = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
print(f"🖥️ Device: {DEVICE}")
if torch.cuda.is_available():
    print(f"   GPU: {torch.cuda.get_device_name(0)}")
    print(f"   VRAM: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB")

class CarDataset(Dataset):
    def __init__(self, images_dir, masks_dir, size=512):
        self.images_dir = Path(images_dir)
        self.masks_dir = Path(masks_dir)
        self.size = size
        self.images = sorted(list(self.images_dir.glob('*.jpg')))
        print(f"📁 Found {len(self.images)} images")
    
    def __len__(self):
        return len(self.images)
    
    def __getitem__(self, idx):
        img_path = self.images[idx]
        image = Image.open(img_path).convert('RGB')
        
        mask_path = self.masks_dir / (img_path.stem + '_mask.gif')
        if not mask_path.exists():
            mask_path = self.masks_dir / (img_path.stem + '_mask.png')
        mask = Image.open(mask_path).convert('L')
        
        image = image.resize((self.size, self.size), Image.BILINEAR)
        mask = mask.resize((self.size, self.size), Image.NEAREST)
        
        # Augmentation
        if torch.rand(1) > 0.5:
            image = TF.hflip(image)
            mask = TF.hflip(mask)
        
        image = TF.to_tensor(image)
        mask = torch.from_numpy(np.array(mask) / 255.0).float().unsqueeze(0)
        image = TF.normalize(image, [0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
        
        return image, mask

class DoubleConv(nn.Module):
    def __init__(self, in_c, out_c):
        super().__init__()
        self.conv = nn.Sequential(
            nn.Conv2d(in_c, out_c, 3, padding=1),
            nn.BatchNorm2d(out_c),
            nn.ReLU(inplace=True),
            nn.Conv2d(out_c, out_c, 3, padding=1),
            nn.BatchNorm2d(out_c),
            nn.ReLU(inplace=True)
        )
    def forward(self, x):
        return self.conv(x)

class UNet(nn.Module):
    def __init__(self, features=[64, 128, 256, 512]):
        super().__init__()
        self.downs = nn.ModuleList()
        self.ups = nn.ModuleList()
        self.pool = nn.MaxPool2d(2, 2)
        
        in_c = 3
        for f in features:
            self.downs.append(DoubleConv(in_c, f))
            in_c = f
        
        self.bottleneck = DoubleConv(features[-1], features[-1] * 2)
        
        for f in reversed(features):
            self.ups.append(nn.ConvTranspose2d(f * 2, f, 2, 2))
            self.ups.append(DoubleConv(f * 2, f))
        
        self.final = nn.Conv2d(features[0], 1, 1)
    
    def forward(self, x):
        skips = []
        for down in self.downs:
            x = down(x)
            skips.append(x)
            x = self.pool(x)
        
        x = self.bottleneck(x)
        skips = skips[::-1]
        
        for i in range(0, len(self.ups), 2):
            x = self.ups[i](x)
            skip = skips[i // 2]
            if x.shape != skip.shape:
                x = TF.resize(x, skip.shape[2:])
            x = torch.cat([skip, x], dim=1)
            x = self.ups[i + 1](x)
        
        return torch.sigmoid(self.final(x))

def train():
    parser = argparse.ArgumentParser()
    parser.add_argument('--data', default='./data')
    parser.add_argument('--epochs', type=int, default=50)
    parser.add_argument('--batch', type=int, default=16)
    parser.add_argument('--lr', type=float, default=1e-4)
    parser.add_argument('--output', default='model.pth')
    args = parser.parse_args()
    
    print("🚗 Car Segmentation Training")
    print("=" * 50)
    
    data = Path(args.data)
    dataset = CarDataset(data / 'train', data / 'train_masks')
    
    train_size = int(0.9 * len(dataset))
    train_ds, val_ds = torch.utils.data.random_split(dataset, [train_size, len(dataset) - train_size])
    
    train_loader = DataLoader(train_ds, args.batch, shuffle=True, num_workers=4, pin_memory=True)
    val_loader = DataLoader(val_ds, args.batch, num_workers=4, pin_memory=True)
    
    model = UNet().to(DEVICE)
    criterion = nn.BCELoss()
    optimizer = optim.AdamW(model.parameters(), lr=args.lr)
    scaler = GradScaler()  # Mixed precision
    
    best_dice = 0
    
    for epoch in range(args.epochs):
        model.train()
        train_loss = 0
        
        pbar = tqdm(train_loader, desc=f"Epoch {epoch+1}/{args.epochs}")
        for imgs, masks in pbar:
            imgs, masks = imgs.to(DEVICE), masks.to(DEVICE)
            
            optimizer.zero_grad()
            with autocast():
                preds = model(imgs)
                loss = criterion(preds, masks)
            
            scaler.scale(loss).backward()
            scaler.step(optimizer)
            scaler.update()
            
            train_loss += loss.item()
            pbar.set_postfix({'loss': f'{loss.item():.4f}'})
        
        # Validation
        model.eval()
        val_dice = 0
        with torch.no_grad():
            for imgs, masks in val_loader:
                imgs, masks = imgs.to(DEVICE), masks.to(DEVICE)
                preds = (model(imgs) > 0.5).float()
                dice = 2 * (preds * masks).sum() / (preds.sum() + masks.sum() + 1e-6)
                val_dice += dice.item()
        
        val_dice /= len(val_loader)
        print(f"   Val Dice: {val_dice:.4f}")
        
        if val_dice > best_dice:
            best_dice = val_dice
            torch.save(model.state_dict(), args.output)
            print(f"   ✅ Saved (Dice: {val_dice:.4f})")
    
    print(f"\n✅ Done! Best Dice: {best_dice:.4f}")
    print(f"   Model: {args.output}")

if __name__ == "__main__":
    train()
SCRIPT

echo ""
echo "✅ Setup complete!"
echo ""
echo "📥 Next steps:"
echo ""
echo "1. Download Carvana dataset:"
echo "   kaggle competitions download -c carvana-image-masking-challenge"
echo "   unzip train.zip -d data/train"
echo "   unzip train_masks.zip -d data/train_masks"
echo ""
echo "2. Start training:"
echo "   python3 train_segmentation.py --epochs 50 --batch 16"
echo ""
echo "3. Download your model when done:"
echo "   scp user@server:/workspace/training/model.pth ."
echo ""

