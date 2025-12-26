#!/usr/bin/env python3
"""
🚗 TRAINING SCRIPT - Car Segmentation Model
============================================
Train a U-Net model on the Carvana dataset for Spyne-quality segmentation.

Usage:
    python train_segmentation.py --data-dir ./data --epochs 50 --batch-size 8

Requirements:
    pip install torch torchvision albumentations tqdm segmentation-models-pytorch
"""

import os
import argparse
from pathlib import Path
from datetime import datetime

import numpy as np
from PIL import Image
from tqdm import tqdm

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
import torchvision.transforms.functional as TF

# Check for GPU
DEVICE = torch.device('cuda' if torch.cuda.is_available() else 'mps' if torch.backends.mps.is_available() else 'cpu')
print(f"🖥️  Using device: {DEVICE}")


# ============== DATASET ==============

class CarSegmentationDataset(Dataset):
    """
    Dataset for car segmentation training.
    Works with Carvana-style data (image + mask pairs).
    """
    
    def __init__(self, images_dir: str, masks_dir: str, transform=None, image_size: int = 512):
        self.images_dir = Path(images_dir)
        self.masks_dir = Path(masks_dir)
        self.transform = transform
        self.image_size = image_size
        
        # Get all image files
        self.images = sorted([f for f in self.images_dir.glob('*.jpg')] + 
                            [f for f in self.images_dir.glob('*.png')])
        
        print(f"📁 Found {len(self.images)} images")
    
    def __len__(self):
        return len(self.images)
    
    def __getitem__(self, idx):
        # Load image
        img_path = self.images[idx]
        image = Image.open(img_path).convert('RGB')
        
        # Find corresponding mask
        mask_name = img_path.stem + '_mask.png'
        mask_path = self.masks_dir / mask_name
        
        if not mask_path.exists():
            # Try without _mask suffix
            mask_path = self.masks_dir / (img_path.stem + '.png')
        
        if not mask_path.exists():
            # Try same name as image
            mask_path = self.masks_dir / img_path.name.replace('.jpg', '.png')
        
        mask = Image.open(mask_path).convert('L')
        
        # Resize
        image = image.resize((self.image_size, self.image_size), Image.BILINEAR)
        mask = mask.resize((self.image_size, self.image_size), Image.NEAREST)
        
        # Convert to tensors
        image = TF.to_tensor(image)
        mask = torch.from_numpy(np.array(mask) / 255.0).float().unsqueeze(0)
        
        # Normalize image
        image = TF.normalize(image, mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        
        return image, mask


# ============== MODEL ==============

class DoubleConv(nn.Module):
    """Double convolution block for U-Net."""
    
    def __init__(self, in_channels, out_channels):
        super().__init__()
        self.conv = nn.Sequential(
            nn.Conv2d(in_channels, out_channels, 3, padding=1),
            nn.BatchNorm2d(out_channels),
            nn.ReLU(inplace=True),
            nn.Conv2d(out_channels, out_channels, 3, padding=1),
            nn.BatchNorm2d(out_channels),
            nn.ReLU(inplace=True)
        )
    
    def forward(self, x):
        return self.conv(x)


class UNet(nn.Module):
    """
    U-Net architecture for image segmentation.
    This is similar to what Spyne likely uses.
    """
    
    def __init__(self, in_channels=3, out_channels=1, features=[64, 128, 256, 512]):
        super().__init__()
        
        self.downs = nn.ModuleList()
        self.ups = nn.ModuleList()
        self.pool = nn.MaxPool2d(2, 2)
        
        # Encoder (downsampling)
        for feature in features:
            self.downs.append(DoubleConv(in_channels, feature))
            in_channels = feature
        
        # Bottleneck
        self.bottleneck = DoubleConv(features[-1], features[-1] * 2)
        
        # Decoder (upsampling)
        for feature in reversed(features):
            self.ups.append(nn.ConvTranspose2d(feature * 2, feature, 2, 2))
            self.ups.append(DoubleConv(feature * 2, feature))
        
        # Output
        self.final_conv = nn.Conv2d(features[0], out_channels, 1)
    
    def forward(self, x):
        skip_connections = []
        
        # Encoder
        for down in self.downs:
            x = down(x)
            skip_connections.append(x)
            x = self.pool(x)
        
        x = self.bottleneck(x)
        skip_connections = skip_connections[::-1]
        
        # Decoder
        for idx in range(0, len(self.ups), 2):
            x = self.ups[idx](x)
            skip = skip_connections[idx // 2]
            
            # Handle size mismatch
            if x.shape != skip.shape:
                x = TF.resize(x, size=skip.shape[2:])
            
            x = torch.cat([skip, x], dim=1)
            x = self.ups[idx + 1](x)
        
        return torch.sigmoid(self.final_conv(x))


# ============== LOSS FUNCTIONS ==============

class DiceLoss(nn.Module):
    """Dice loss for segmentation."""
    
    def __init__(self, smooth=1e-6):
        super().__init__()
        self.smooth = smooth
    
    def forward(self, pred, target):
        pred = pred.view(-1)
        target = target.view(-1)
        
        intersection = (pred * target).sum()
        dice = (2. * intersection + self.smooth) / (pred.sum() + target.sum() + self.smooth)
        
        return 1 - dice


class CombinedLoss(nn.Module):
    """Combined BCE + Dice loss."""
    
    def __init__(self):
        super().__init__()
        self.bce = nn.BCELoss()
        self.dice = DiceLoss()
    
    def forward(self, pred, target):
        return self.bce(pred, target) + self.dice(pred, target)


# ============== TRAINING ==============

def train_epoch(model, loader, optimizer, criterion, device):
    """Train for one epoch."""
    model.train()
    total_loss = 0
    
    pbar = tqdm(loader, desc="Training")
    for images, masks in pbar:
        images = images.to(device)
        masks = masks.to(device)
        
        # Forward
        predictions = model(images)
        loss = criterion(predictions, masks)
        
        # Backward
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
        
        total_loss += loss.item()
        pbar.set_postfix({'loss': f'{loss.item():.4f}'})
    
    return total_loss / len(loader)


def validate(model, loader, criterion, device):
    """Validate the model."""
    model.eval()
    total_loss = 0
    total_dice = 0
    
    with torch.no_grad():
        for images, masks in loader:
            images = images.to(device)
            masks = masks.to(device)
            
            predictions = model(images)
            loss = criterion(predictions, masks)
            total_loss += loss.item()
            
            # Calculate Dice score
            pred_binary = (predictions > 0.5).float()
            dice = 2 * (pred_binary * masks).sum() / (pred_binary.sum() + masks.sum() + 1e-6)
            total_dice += dice.item()
    
    return total_loss / len(loader), total_dice / len(loader)


def main():
    parser = argparse.ArgumentParser(description='Train car segmentation model')
    parser.add_argument('--data-dir', type=str, default='./data', help='Data directory')
    parser.add_argument('--epochs', type=int, default=50, help='Number of epochs')
    parser.add_argument('--batch-size', type=int, default=8, help='Batch size')
    parser.add_argument('--lr', type=float, default=1e-4, help='Learning rate')
    parser.add_argument('--image-size', type=int, default=512, help='Image size')
    parser.add_argument('--output', type=str, default='car_segmentation_model.pth', help='Output model path')
    args = parser.parse_args()
    
    print("🚗 Car Segmentation Model Training")
    print("=" * 50)
    
    # Paths
    data_dir = Path(args.data_dir)
    train_images = data_dir / 'train'
    train_masks = data_dir / 'train_masks'
    
    if not train_images.exists():
        print(f"❌ Training images not found at {train_images}")
        print("\n📥 Download the Carvana dataset from:")
        print("   https://www.kaggle.com/c/carvana-image-masking-challenge/data")
        print("\n   Then extract:")
        print(f"   - train.zip → {train_images}")
        print(f"   - train_masks.zip → {train_masks}")
        return
    
    # Create dataset
    print("\n📦 Loading dataset...")
    dataset = CarSegmentationDataset(train_images, train_masks, image_size=args.image_size)
    
    # Split into train/val
    train_size = int(0.9 * len(dataset))
    val_size = len(dataset) - train_size
    train_dataset, val_dataset = torch.utils.data.random_split(dataset, [train_size, val_size])
    
    train_loader = DataLoader(train_dataset, batch_size=args.batch_size, shuffle=True, num_workers=4)
    val_loader = DataLoader(val_dataset, batch_size=args.batch_size, shuffle=False, num_workers=4)
    
    print(f"   Train: {len(train_dataset)} images")
    print(f"   Val: {len(val_dataset)} images")
    
    # Create model
    print("\n🏗️  Creating U-Net model...")
    model = UNet().to(DEVICE)
    
    # Count parameters
    params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    print(f"   Parameters: {params:,}")
    
    # Loss and optimizer
    criterion = CombinedLoss()
    optimizer = optim.Adam(model.parameters(), lr=args.lr)
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode='min', patience=5, factor=0.5)
    
    # Training loop
    print(f"\n🏋️  Training for {args.epochs} epochs...")
    print("=" * 50)
    
    best_dice = 0
    
    for epoch in range(args.epochs):
        print(f"\nEpoch {epoch + 1}/{args.epochs}")
        
        # Train
        train_loss = train_epoch(model, train_loader, optimizer, criterion, DEVICE)
        
        # Validate
        val_loss, val_dice = validate(model, val_loader, criterion, DEVICE)
        
        # Update scheduler
        scheduler.step(val_loss)
        
        print(f"   Train Loss: {train_loss:.4f}")
        print(f"   Val Loss: {val_loss:.4f} | Val Dice: {val_dice:.4f}")
        
        # Save best model
        if val_dice > best_dice:
            best_dice = val_dice
            torch.save({
                'epoch': epoch,
                'model_state_dict': model.state_dict(),
                'optimizer_state_dict': optimizer.state_dict(),
                'dice_score': val_dice,
            }, args.output)
            print(f"   ✅ Saved best model (Dice: {val_dice:.4f})")
    
    print("\n" + "=" * 50)
    print(f"✅ Training complete!")
    print(f"   Best Dice Score: {best_dice:.4f}")
    print(f"   Model saved to: {args.output}")
    print("\n📝 To use the model:")
    print(f"   python segment_with_trained.py {args.output} image.jpg")


if __name__ == "__main__":
    main()

