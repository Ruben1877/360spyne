#!/usr/bin/env python3
"""
📥 Download Sample Training Data
================================
Downloads sample car images with masks for testing the training pipeline.

For production training, use the full Carvana dataset from Kaggle.
"""

import os
import urllib.request
from pathlib import Path

# Sample images with masks (from open sources)
SAMPLE_DATA = [
    # Format: (image_url, mask_url, name)
    # These are placeholder URLs - in production use Carvana dataset
]

def download_file(url: str, path: str):
    """Download a file from URL."""
    print(f"   Downloading {Path(path).name}...")
    try:
        urllib.request.urlretrieve(url, path)
        return True
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False


def create_sample_mask(image_path: str, mask_path: str):
    """
    Create a sample mask for testing.
    In production, use real annotated masks.
    """
    import cv2
    import numpy as np
    
    # Load image
    img = cv2.imread(image_path)
    if img is None:
        return False
    
    h, w = img.shape[:2]
    
    # Create a simple center-focused mask for testing
    mask = np.zeros((h, w), dtype=np.uint8)
    
    # Assume car is in center 60% of image
    y1, y2 = int(h * 0.2), int(h * 0.9)
    x1, x2 = int(w * 0.15), int(w * 0.85)
    
    mask[y1:y2, x1:x2] = 255
    
    # Smooth edges
    mask = cv2.GaussianBlur(mask, (21, 21), 0)
    _, mask = cv2.threshold(mask, 127, 255, cv2.THRESH_BINARY)
    
    cv2.imwrite(mask_path, mask)
    return True


def main():
    print("📥 Sample Data Download")
    print("=" * 50)
    print()
    print("⚠️  For production-quality training, you need:")
    print()
    print("   🏆 CARVANA DATASET (5,088 images)")
    print("   https://www.kaggle.com/c/carvana-image-masking-challenge/data")
    print()
    print("   This dataset contains professional car photos with")
    print("   pixel-perfect masks - exactly what Spyne uses.")
    print()
    print("=" * 50)
    print()
    print("📝 How to get the Carvana dataset:")
    print()
    print("   1. Create a Kaggle account (free)")
    print("   2. Go to the competition page")
    print("   3. Accept the rules")
    print("   4. Download train.zip and train_masks.zip")
    print("   5. Extract to training/data/")
    print()
    print("   Structure:")
    print("   training/")
    print("   └── data/")
    print("       ├── train/          # 5088 car images")
    print("       │   ├── 0cdf5b5d0ce1_01.jpg")
    print("       │   └── ...")
    print("       └── train_masks/    # 5088 masks")
    print("           ├── 0cdf5b5d0ce1_01_mask.gif")
    print("           └── ...")
    print()
    
    # Create directories
    data_dir = Path("data")
    train_dir = data_dir / "train"
    masks_dir = data_dir / "train_masks"
    
    train_dir.mkdir(parents=True, exist_ok=True)
    masks_dir.mkdir(parents=True, exist_ok=True)
    
    print("✅ Created directories:")
    print(f"   {train_dir}/")
    print(f"   {masks_dir}/")
    print()
    print("📥 Place your Carvana data in these directories,")
    print("   then run: python train_segmentation.py")


if __name__ == "__main__":
    main()

