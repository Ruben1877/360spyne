#!/usr/bin/env python3
"""Test du rendu 3D Spyne exact"""
import cv2
import numpy as np

print("🚗 Test rendu 3D style Spyne...")

from segmentation import Segmentation
from edge_smoothing import EdgeSmoothing
from background_3d import create_spyne_exact_render

# Charger l'image test
image = cv2.imread("test_car.jpg")
image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

# Segmentation
print("  [1/3] Segmentation...")
seg = Segmentation()
mask = seg.segment(image)

smooth = EdgeSmoothing()
mask = smooth.full_edge_refinement(image, mask)

# Extraire la voiture
car_rgba = seg.extract_foreground(image, mask)
car_rgb = car_rgba[:, :, :3]

# Rendre avec fond 3D
for preset in ['spyne_showroom', 'spyne_white']:
    print(f"  [2/3] Rendu 3D {preset}...")
    result = create_spyne_exact_render(car_rgb, mask, preset, (1920, 1080))
    
    output = f"result_3d_{preset}.jpg"
    cv2.imwrite(output, cv2.cvtColor(result, cv2.COLOR_RGB2BGR), [cv2.IMWRITE_JPEG_QUALITY, 95])
    print(f"  ✅ Saved: {output}")

print("\n🎉 Terminé !")
