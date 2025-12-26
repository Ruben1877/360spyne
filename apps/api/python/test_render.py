#!/usr/bin/env python3
"""Test du rendu Spyne quality"""
import cv2
import urllib.request
import numpy as np

print("📥 Téléchargement d'une image de test...")
url = "https://images.unsplash.com/photo-1552519507-da3b142c6e3d?w=1200"
urllib.request.urlretrieve(url, "test_car.jpg")
print("✅ Image téléchargée: test_car.jpg")

print("\n🚗 Lancement du traitement Spyne Quality...")
from process_image import SpyneCloneProcessor

processor = SpyneCloneProcessor()

# Test avec chaque preset
for preset in ['spyne_white', 'spyne_grey', 'spyne_showroom']:
    output = f"result_{preset}.jpg"
    print(f"\n🎨 Génération: {preset}...")
    result = processor.process_spyne_quality(
        "test_car.jpg",
        output,
        preset=preset,
        output_size=(1920, 1080)
    )
    if result['success']:
        print(f"   ✅ Saved: {output}")

print("\n🎉 Terminé ! Ouvre le dossier pour voir les résultats.")
