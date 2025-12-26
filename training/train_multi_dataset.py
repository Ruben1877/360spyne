#!/usr/bin/env python3
"""
🚗 ADVANCED TRAINING - Multi-Dataset Car Segmentation
======================================================
Train on multiple datasets for Spyne-level (or better!) segmentation.

Supported datasets:
- Carvana (5,088 images) - Studio photos
- BDD100K (100,000 images) - Road scenes
- COCO Cars (~12,000 images) - Various contexts
- Custom data - Your own annotated images

Usage:
    python train_multi_dataset.py --datasets carvana bdd100k --epochs 100

The more data, the better the model!
"""

import os
import argparse
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Tuple

import numpy as np
from PIL import Image
from tqdm import tqdm

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader, ConcatDataset
import torchvision.transforms as T
import torchvision.transforms.functional as TF

# Import model from base training script
from train_segmentation import UNet, DiceLoss, CombinedLoss

DEVICE = torch.device('cuda' if torch.cuda.is_available() else 'mps' if torch.backends.mps.is_available() else 'cpu')


# ============== DATA AUGMENTATION ==============

class CarAugmentation:
    """
    Data augmentation for car images.
    This effectively multiplies your dataset size by 8-10x!
    """
    
    def __init__(self, image_size: int = 512):
        self.image_size = image_size
        
        # Augmentations that preserve mask alignment
        self.spatial_transforms = T.Compose([
            T.RandomHorizontalFlip(p=0.5),
            T.RandomRotation(degrees=5),
            T.RandomResizedCrop(image_size, scale=(0.8, 1.0)),
        ])
        
        # Color augmentations (image only)
        self.color_transforms = T.Compose([
            T.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.2, hue=0.1),
            T.RandomGrayscale(p=0.1),
        ])
    
    def __call__(self, image: Image.Image, mask: Image.Image) -> Tuple[torch.Tensor, torch.Tensor]:
        # Resize first
        image = image.resize((self.image_size, self.image_size), Image.BILINEAR)
        mask = mask.resize((self.image_size, self.image_size), Image.NEAREST)
        
        # Random horizontal flip (same for both)
        if torch.rand(1) > 0.5:
            image = TF.hflip(image)
            mask = TF.hflip(mask)
        
        # Random rotation (same angle for both)
        if torch.rand(1) > 0.5:
            angle = (torch.rand(1) * 10 - 5).item()  # -5 to +5 degrees
            image = TF.rotate(image, angle)
            mask = TF.rotate(mask, angle)
        
        # Color augmentation (image only)
        image = self.color_transforms(image)
        
        # To tensor
        image = TF.to_tensor(image)
        mask = torch.from_numpy(np.array(mask) / 255.0).float().unsqueeze(0)
        
        # Normalize image
        image = TF.normalize(image, mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        
        return image, mask


# ============== DATASET LOADERS ==============

class CarvanaDataset(Dataset):
    """Carvana dataset - Studio car photos with perfect masks."""
    
    def __init__(self, data_dir: str, transform=None):
        self.data_dir = Path(data_dir)
        self.transform = transform or CarAugmentation()
        
        self.images_dir = self.data_dir / 'train'
        self.masks_dir = self.data_dir / 'train_masks'
        
        self.images = sorted(list(self.images_dir.glob('*.jpg')))
        print(f"   📁 Carvana: {len(self.images)} images")
    
    def __len__(self):
        return len(self.images)
    
    def __getitem__(self, idx):
        img_path = self.images[idx]
        
        # Load image
        image = Image.open(img_path).convert('RGB')
        
        # Load mask (Carvana uses _mask.gif suffix)
        mask_path = self.masks_dir / (img_path.stem + '_mask.gif')
        if not mask_path.exists():
            mask_path = self.masks_dir / (img_path.stem + '_mask.png')
        
        mask = Image.open(mask_path).convert('L')
        
        return self.transform(image, mask)


class BDD100KDataset(Dataset):
    """BDD100K dataset - Road scenes with car segmentation."""
    
    def __init__(self, data_dir: str, transform=None):
        self.data_dir = Path(data_dir)
        self.transform = transform or CarAugmentation()
        
        self.images_dir = self.data_dir / 'images' / '10k' / 'train'
        self.labels_dir = self.data_dir / 'labels' / 'sem_seg' / 'masks' / 'train'
        
        self.images = sorted(list(self.images_dir.glob('*.jpg')))
        print(f"   📁 BDD100K: {len(self.images)} images")
    
    def __len__(self):
        return len(self.images)
    
    def __getitem__(self, idx):
        img_path = self.images[idx]
        
        # Load image
        image = Image.open(img_path).convert('RGB')
        
        # Load mask
        mask_path = self.labels_dir / (img_path.stem + '.png')
        mask_full = Image.open(mask_path)
        
        # BDD100K class 13 = car - extract only cars
        mask_array = np.array(mask_full)
        car_mask = (mask_array == 13).astype(np.uint8) * 255
        mask = Image.fromarray(car_mask)
        
        return self.transform(image, mask)


class COCOCarsDataset(Dataset):
    """COCO dataset filtered for cars only."""
    
    def __init__(self, data_dir: str, transform=None):
        self.data_dir = Path(data_dir)
        self.transform = transform or CarAugmentation()
        
        self.images_dir = self.data_dir / 'train2017'
        self.annotations_file = self.data_dir / 'annotations' / 'instances_train2017.json'
        
        # Load COCO annotations
        with open(self.annotations_file, 'r') as f:
            coco = json.load(f)
        
        # Find car category ID (usually 3)
        car_cat_id = None
        for cat in coco['categories']:
            if cat['name'] == 'car':
                car_cat_id = cat['id']
                break
        
        # Filter annotations for cars
        self.car_annotations = [
            ann for ann in coco['annotations']
            if ann['category_id'] == car_cat_id and ann.get('segmentation')
        ]
        
        # Create image lookup
        self.images_dict = {img['id']: img for img in coco['images']}
        
        print(f"   📁 COCO Cars: {len(self.car_annotations)} images")
    
    def __len__(self):
        return len(self.car_annotations)
    
    def __getitem__(self, idx):
        ann = self.car_annotations[idx]
        img_info = self.images_dict[ann['image_id']]
        
        # Load image
        img_path = self.images_dir / img_info['file_name']
        image = Image.open(img_path).convert('RGB')
        
        # Create mask from segmentation
        from pycocotools import mask as coco_mask
        
        h, w = img_info['height'], img_info['width']
        
        if isinstance(ann['segmentation'], list):
            # Polygon format
            rles = coco_mask.frPyObjects(ann['segmentation'], h, w)
            rle = coco_mask.merge(rles)
        else:
            # RLE format
            rle = ann['segmentation']
        
        mask_array = coco_mask.decode(rle) * 255
        mask = Image.fromarray(mask_array.astype(np.uint8))
        
        return self.transform(image, mask)


class CustomDataset(Dataset):
    """Your own custom annotated car images."""
    
    def __init__(self, data_dir: str, transform=None):
        self.data_dir = Path(data_dir)
        self.transform = transform or CarAugmentation()
        
        self.images_dir = self.data_dir / 'images'
        self.masks_dir = self.data_dir / 'masks'
        
        self.images = sorted(list(self.images_dir.glob('*.jpg')) + 
                            list(self.images_dir.glob('*.png')))
        print(f"   📁 Custom: {len(self.images)} images")
    
    def __len__(self):
        return len(self.images)
    
    def __getitem__(self, idx):
        img_path = self.images[idx]
        
        image = Image.open(img_path).convert('RGB')
        
        # Try different mask naming conventions
        mask_path = self.masks_dir / (img_path.stem + '_mask.png')
        if not mask_path.exists():
            mask_path = self.masks_dir / (img_path.stem + '.png')
        
        mask = Image.open(mask_path).convert('L')
        
        return self.transform(image, mask)


# ============== TRAINING ==============

def train_epoch(model, loader, optimizer, criterion, device):
    model.train()
    total_loss = 0
    
    pbar = tqdm(loader, desc="Training")
    for images, masks in pbar:
        images = images.to(device)
        masks = masks.to(device)
        
        predictions = model(images)
        loss = criterion(predictions, masks)
        
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
        
        total_loss += loss.item()
        pbar.set_postfix({'loss': f'{loss.item():.4f}'})
    
    return total_loss / len(loader)


def validate(model, loader, criterion, device):
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
            
            pred_binary = (predictions > 0.5).float()
            dice = 2 * (pred_binary * masks).sum() / (pred_binary.sum() + masks.sum() + 1e-6)
            total_dice += dice.item()
    
    return total_loss / len(loader), total_dice / len(loader)


def main():
    parser = argparse.ArgumentParser(description='Multi-dataset car segmentation training')
    parser.add_argument('--datasets', nargs='+', default=['carvana'], 
                       choices=['carvana', 'bdd100k', 'coco', 'custom'],
                       help='Datasets to use')
    parser.add_argument('--data-root', type=str, default='./data', help='Root data directory')
    parser.add_argument('--epochs', type=int, default=100, help='Number of epochs')
    parser.add_argument('--batch-size', type=int, default=8, help='Batch size')
    parser.add_argument('--lr', type=float, default=1e-4, help='Learning rate')
    parser.add_argument('--image-size', type=int, default=512, help='Image size')
    parser.add_argument('--output', type=str, default='car_segmentation_pro.pth', help='Output model')
    args = parser.parse_args()
    
    print("🚗 Multi-Dataset Car Segmentation Training")
    print("=" * 60)
    print(f"🖥️  Device: {DEVICE}")
    print(f"📊 Datasets: {', '.join(args.datasets)}")
    print()
    
    # Load datasets
    print("📦 Loading datasets...")
    datasets = []
    data_root = Path(args.data_root)
    
    transform = CarAugmentation(args.image_size)
    
    if 'carvana' in args.datasets:
        carvana_path = data_root / 'carvana'
        if carvana_path.exists():
            datasets.append(CarvanaDataset(carvana_path, transform))
        else:
            print(f"   ⚠️ Carvana not found at {carvana_path}")
    
    if 'bdd100k' in args.datasets:
        bdd_path = data_root / 'bdd100k'
        if bdd_path.exists():
            datasets.append(BDD100KDataset(bdd_path, transform))
        else:
            print(f"   ⚠️ BDD100K not found at {bdd_path}")
    
    if 'coco' in args.datasets:
        coco_path = data_root / 'coco'
        if coco_path.exists():
            datasets.append(COCOCarsDataset(coco_path, transform))
        else:
            print(f"   ⚠️ COCO not found at {coco_path}")
    
    if 'custom' in args.datasets:
        custom_path = data_root / 'custom'
        if custom_path.exists():
            datasets.append(CustomDataset(custom_path, transform))
        else:
            print(f"   ⚠️ Custom data not found at {custom_path}")
    
    if not datasets:
        print("\n❌ No datasets found! Please download at least one dataset.")
        print("\n📥 Dataset download instructions:")
        print("   Carvana: https://www.kaggle.com/c/carvana-image-masking-challenge")
        print("   BDD100K: https://bdd-data.berkeley.edu/")
        print("   COCO: https://cocodataset.org/")
        return
    
    # Combine datasets
    combined = ConcatDataset(datasets)
    total_images = len(combined)
    
    print(f"\n📊 Total training images: {total_images:,}")
    
    # Split
    train_size = int(0.9 * total_images)
    val_size = total_images - train_size
    train_dataset, val_dataset = torch.utils.data.random_split(combined, [train_size, val_size])
    
    train_loader = DataLoader(train_dataset, batch_size=args.batch_size, shuffle=True, num_workers=4)
    val_loader = DataLoader(val_dataset, batch_size=args.batch_size, shuffle=False, num_workers=4)
    
    print(f"   Train: {train_size:,} images")
    print(f"   Val: {val_size:,} images")
    
    # Model
    print("\n🏗️  Creating U-Net model...")
    model = UNet().to(DEVICE)
    params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    print(f"   Parameters: {params:,}")
    
    # Training setup
    criterion = CombinedLoss()
    optimizer = optim.AdamW(model.parameters(), lr=args.lr, weight_decay=0.01)
    scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=args.epochs)
    
    # Training loop
    print(f"\n🏋️  Training for {args.epochs} epochs...")
    print("=" * 60)
    
    best_dice = 0
    
    for epoch in range(args.epochs):
        print(f"\nEpoch {epoch + 1}/{args.epochs} (LR: {scheduler.get_last_lr()[0]:.2e})")
        
        train_loss = train_epoch(model, train_loader, optimizer, criterion, DEVICE)
        val_loss, val_dice = validate(model, val_loader, criterion, DEVICE)
        
        scheduler.step()
        
        print(f"   Train Loss: {train_loss:.4f}")
        print(f"   Val Loss: {val_loss:.4f} | Val Dice: {val_dice:.4f}")
        
        if val_dice > best_dice:
            best_dice = val_dice
            torch.save({
                'epoch': epoch,
                'model_state_dict': model.state_dict(),
                'optimizer_state_dict': optimizer.state_dict(),
                'dice_score': val_dice,
                'datasets': args.datasets,
                'total_images': total_images,
            }, args.output)
            print(f"   ✅ New best model saved! (Dice: {val_dice:.4f})")
    
    print("\n" + "=" * 60)
    print(f"✅ Training complete!")
    print(f"   Best Dice Score: {best_dice:.4f}")
    print(f"   Total images trained: {total_images:,}")
    print(f"   Model saved: {args.output}")


if __name__ == "__main__":
    main()

