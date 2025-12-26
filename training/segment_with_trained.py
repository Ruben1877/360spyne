#!/usr/bin/env python3
"""
🚗 Use Trained Model for Segmentation
======================================
Segment car images using your custom-trained model.

Usage:
    python segment_with_trained.py model.pth image.jpg [output_mask.png]
"""

import sys
import numpy as np
import cv2
import torch
import torch.nn as nn
import torchvision.transforms.functional as TF
from PIL import Image
from pathlib import Path

# Import model architecture from training script
from train_segmentation import UNet

DEVICE = torch.device('cuda' if torch.cuda.is_available() else 'mps' if torch.backends.mps.is_available() else 'cpu')


class TrainedSegmentation:
    """
    Use a custom-trained model for car segmentation.
    This gives Spyne-level quality when trained on enough data.
    """
    
    def __init__(self, model_path: str, image_size: int = 512):
        self.image_size = image_size
        self.device = DEVICE
        
        # Load model
        print(f"🔄 Loading model from {model_path}...")
        self.model = UNet().to(self.device)
        
        checkpoint = torch.load(model_path, map_location=self.device)
        self.model.load_state_dict(checkpoint['model_state_dict'])
        self.model.eval()
        
        dice_score = checkpoint.get('dice_score', 'unknown')
        print(f"✅ Model loaded (Dice score: {dice_score})")
    
    def segment(self, image: np.ndarray) -> np.ndarray:
        """
        Segment a car from an image.
        
        Args:
            image: BGR numpy array (OpenCV format)
        
        Returns:
            mask: Binary mask (0 or 255)
        """
        original_h, original_w = image.shape[:2]
        
        # Preprocess
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        pil_image = Image.fromarray(image_rgb)
        pil_image = pil_image.resize((self.image_size, self.image_size), Image.BILINEAR)
        
        # To tensor and normalize
        tensor = TF.to_tensor(pil_image)
        tensor = TF.normalize(tensor, mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        tensor = tensor.unsqueeze(0).to(self.device)
        
        # Predict
        with torch.no_grad():
            prediction = self.model(tensor)
        
        # Post-process
        mask = prediction.squeeze().cpu().numpy()
        mask = (mask > 0.5).astype(np.uint8) * 255
        
        # Resize back to original size
        mask = cv2.resize(mask, (original_w, original_h), interpolation=cv2.INTER_NEAREST)
        
        return mask


def main():
    if len(sys.argv) < 3:
        print("Usage: python segment_with_trained.py model.pth image.jpg [output_mask.png]")
        sys.exit(1)
    
    model_path = sys.argv[1]
    image_path = sys.argv[2]
    output_path = sys.argv[3] if len(sys.argv) > 3 else image_path.rsplit('.', 1)[0] + '_mask.png'
    
    # Load image
    image = cv2.imread(image_path)
    if image is None:
        print(f"❌ Could not load image: {image_path}")
        sys.exit(1)
    
    print(f"📷 Image: {image_path} ({image.shape[1]}x{image.shape[0]})")
    
    # Segment
    segmenter = TrainedSegmentation(model_path)
    mask = segmenter.segment(image)
    
    # Save mask
    cv2.imwrite(output_path, mask)
    print(f"✅ Mask saved: {output_path}")
    
    # Also save cutout
    cutout_path = image_path.rsplit('.', 1)[0] + '_cutout.png'
    rgba = cv2.cvtColor(image, cv2.COLOR_BGR2BGRA)
    rgba[:, :, 3] = mask
    cv2.imwrite(cutout_path, rgba)
    print(f"✅ Cutout saved: {cutout_path}")


if __name__ == "__main__":
    main()

