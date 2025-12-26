#!/usr/bin/env python3
"""Rendu avec fond de studio personnalisé"""
import cv2
import numpy as np

print("🎨 Rendu avec ton fond de studio...")

# Charger le fond
bg_path = "backgrounds/background1.jpeg"
background = cv2.imread(bg_path)
if background is None:
    print(f"❌ Erreur: impossible de charger {bg_path}")
    exit(1)

background = cv2.cvtColor(background, cv2.COLOR_BGR2RGB)
bg_h, bg_w = background.shape[:2]
print(f"✅ Fond chargé: {bg_w}x{bg_h}")

# Charger la voiture test
car_path = "test_car.jpg"
car_image = cv2.imread(car_path)
car_image = cv2.cvtColor(car_image, cv2.COLOR_BGR2RGB)

# Segmentation
print("🔍 Segmentation de la voiture...")
from segmentation import Segmentation
from edge_smoothing import EdgeSmoothing

seg = Segmentation()
mask = seg.segment(cv2.cvtColor(car_image, cv2.COLOR_RGB2BGR))

smooth = EdgeSmoothing()
mask = smooth.full_edge_refinement(cv2.cvtColor(car_image, cv2.COLOR_RGB2BGR), mask)

# Redimensionner la voiture pour le fond
car_h, car_w = car_image.shape[:2]
scale = min(bg_w * 0.65 / car_w, bg_h * 0.50 / car_h)
new_w = int(car_w * scale)
new_h = int(car_h * scale)

car_resized = cv2.resize(car_image, (new_w, new_h), interpolation=cv2.INTER_LANCZOS4)
mask_resized = cv2.resize(mask, (new_w, new_h), interpolation=cv2.INTER_LANCZOS4)

# Position de la voiture (centrée, sur le sol)
car_x = (bg_w - new_w) // 2
# Trouver la ligne d'horizon (environ 55% depuis le haut pour ce type de fond)
horizon_y = int(bg_h * 0.72)
car_y = horizon_y - new_h + int(new_h * 0.12)

print(f"🚗 Position: ({car_x}, {car_y})")

# Créer le résultat
result = background.copy()

# 1. Ajouter le reflet de la voiture
print("🪞 Génération du reflet...")
reflection = cv2.flip(car_resized, 0)
reflection_mask = cv2.flip(mask_resized, 0)

# Fade et compression du reflet
ref_h = int(new_h * 0.5)
reflection = cv2.resize(reflection, (new_w, ref_h))
reflection_mask = cv2.resize(reflection_mask, (new_w, ref_h))

for y in range(ref_h):
    fade = (1 - y / ref_h) ** 1.5 * 0.35
    reflection[y] = (reflection[y] * fade).astype(np.uint8)
    reflection_mask[y] = (reflection_mask[y] * fade).astype(np.uint8)

# Positionner le reflet
ref_y = horizon_y + 5
ry1 = max(0, ref_y)
ry2 = min(bg_h, ref_y + ref_h)
rx1 = max(0, car_x)
rx2 = min(bg_w, car_x + new_w)

if ry2 > ry1 and rx2 > rx1:
    rmy1 = max(0, -ref_y)
    rmy2 = rmy1 + (ry2 - ry1)
    rmx1 = max(0, -car_x)
    rmx2 = rmx1 + (rx2 - rx1)
    
    ref_mask_norm = reflection_mask[rmy1:rmy2, rmx1:rmx2].astype(np.float32) / 255.0
    ref_mask_3ch = ref_mask_norm[:, :, np.newaxis]
    
    result[ry1:ry2, rx1:rx2] = (
        result[ry1:ry2, rx1:rx2].astype(np.float32) * (1 - ref_mask_3ch * 0.6) +
        reflection[rmy1:rmy2, rmx1:rmx2].astype(np.float32) * ref_mask_3ch * 0.6
    ).astype(np.uint8)

# 2. Ajouter l'ombre
print("🌑 Génération de l'ombre...")
shadow_h = max(5, int(new_h * 0.025))
shadow_w = int(new_w * 0.90)
shadow_x = car_x + (new_w - shadow_w) // 2
shadow_y = horizon_y - 3

# Créer une ombre elliptique floue
shadow = np.zeros((shadow_h * 4, shadow_w), dtype=np.float32)
cv2.ellipse(shadow, (shadow_w // 2, shadow_h * 2), (shadow_w // 2, shadow_h), 0, 0, 360, 1.0, -1)
shadow = cv2.GaussianBlur(shadow, (31, 31), 0)

for y in range(shadow.shape[0]):
    for x in range(shadow.shape[1]):
        img_y = shadow_y + y - shadow_h
        img_x = shadow_x + x
        if 0 <= img_y < bg_h and 0 <= img_x < bg_w:
            darkness = shadow[y, x] * 0.5
            result[img_y, img_x] = (result[img_y, img_x].astype(np.float32) * (1 - darkness)).astype(np.uint8)

# 3. Ajouter la voiture
print("🚗 Composition de la voiture...")
y1 = max(0, car_y)
y2 = min(bg_h, car_y + new_h)
x1 = max(0, car_x)
x2 = min(bg_w, car_x + new_w)

my1 = max(0, -car_y)
my2 = my1 + (y2 - y1)
mx1 = max(0, -car_x)
mx2 = mx1 + (x2 - x1)

if y2 > y1 and x2 > x1:
    mask_norm = mask_resized[my1:my2, mx1:mx2].astype(np.float32) / 255.0
    mask_3ch = mask_norm[:, :, np.newaxis]
    
    result[y1:y2, x1:x2] = (
        result[y1:y2, x1:x2].astype(np.float32) * (1 - mask_3ch) +
        car_resized[my1:my2, mx1:mx2].astype(np.float32) * mask_3ch
    ).astype(np.uint8)

# Sauvegarder
output = "result_custom_studio.jpg"
cv2.imwrite(output, cv2.cvtColor(result, cv2.COLOR_RGB2BGR), [cv2.IMWRITE_JPEG_QUALITY, 95])
print(f"\n✅ Résultat sauvegardé: {output}")
print("🎉 Ouvre le dossier pour voir !")
