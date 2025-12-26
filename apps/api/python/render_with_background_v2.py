#!/usr/bin/env python3
"""Rendu avec positionnement automatique sur le sol"""
import cv2
import numpy as np

print("🎨 Rendu avec positionnement automatique...")

# Charger le fond
bg_path = "backgrounds/background1.jpeg"
background = cv2.imread(bg_path)
background = cv2.cvtColor(background, cv2.COLOR_BGR2RGB)
bg_h, bg_w = background.shape[:2]
print(f"✅ Fond: {bg_w}x{bg_h}")

# Charger la voiture
car_image = cv2.imread("test_car.jpg")
car_image_bgr = car_image.copy()
car_image = cv2.cvtColor(car_image, cv2.COLOR_BGR2RGB)

# Segmentation
print("🔍 Segmentation...")
from segmentation import Segmentation
from edge_smoothing import EdgeSmoothing

seg = Segmentation()
mask = seg.segment(car_image_bgr)
smooth = EdgeSmoothing()
mask = smooth.full_edge_refinement(car_image_bgr, mask)

# Trouver le bas RÉEL de la voiture (les roues)
def find_car_bottom(mask):
    """Trouve la ligne du bas de la voiture (roues)"""
    coords = np.column_stack(np.where(mask > 128))
    if len(coords) == 0:
        return mask.shape[0]
    return coords[:, 0].max()

def find_car_bounds(mask):
    """Trouve les limites de la voiture"""
    coords = np.column_stack(np.where(mask > 128))
    if len(coords) == 0:
        return 0, 0, mask.shape[0], mask.shape[1]
    y_min, x_min = coords.min(axis=0)
    y_max, x_max = coords.max(axis=0)
    return y_min, x_min, y_max, x_max

# Obtenir les bounds de la voiture
car_top, car_left, car_bottom, car_right = find_car_bounds(mask)
car_h_actual = car_bottom - car_top
car_w_actual = car_right - car_left

print(f"   Voiture: top={car_top}, bottom={car_bottom}, h={car_h_actual}")

# Redimensionner
car_h, car_w = car_image.shape[:2]
scale = min(bg_w * 0.55 / car_w, bg_h * 0.45 / car_h)
new_w = int(car_w * scale)
new_h = int(car_h * scale)

car_resized = cv2.resize(car_image, (new_w, new_h), interpolation=cv2.INTER_LANCZOS4)
mask_resized = cv2.resize(mask, (new_w, new_h), interpolation=cv2.INTER_LANCZOS4)

# Recalculer les bounds après redimensionnement
new_car_bottom = int(car_bottom * scale)
new_car_top = int(car_top * scale)

# === POSITIONNEMENT CORRECT ===
# La ligne du sol dans ce fond est à environ 72% de la hauteur
floor_y = int(bg_h * 0.72)

# Positionner la voiture pour que ses ROUES touchent le sol
# car_y + new_car_bottom = floor_y
# donc: car_y = floor_y - new_car_bottom
car_y = floor_y - new_car_bottom
car_x = (bg_w - new_w) // 2

print(f"🚗 Position corrigée: ({car_x}, {car_y})")
print(f"   Sol à: {floor_y}, Roues à: {car_y + new_car_bottom}")

# Créer le résultat
result = background.copy()

# 1. Reflet (positionné juste sous le sol)
print("🪞 Reflet...")
reflection = cv2.flip(car_resized, 0)
reflection_mask = cv2.flip(mask_resized, 0)

ref_h = int(new_h * 0.45)
reflection = cv2.resize(reflection, (new_w, ref_h))
reflection_mask = cv2.resize(reflection_mask, (new_w, ref_h))

for y in range(ref_h):
    fade = (1 - y / ref_h) ** 1.8 * 0.30
    reflection[y] = (reflection[y] * fade).astype(np.uint8)
    reflection_mask[y] = (reflection_mask[y] * fade).astype(np.uint8)

ref_y = floor_y + 2  # Juste sous la ligne du sol
ry1, ry2 = max(0, ref_y), min(bg_h, ref_y + ref_h)
rx1, rx2 = max(0, car_x), min(bg_w, car_x + new_w)

if ry2 > ry1 and rx2 > rx1:
    rmy1, rmy2 = max(0, -ref_y), max(0, -ref_y) + (ry2 - ry1)
    rmx1, rmx2 = max(0, -car_x), max(0, -car_x) + (rx2 - rx1)
    
    ref_mask_norm = reflection_mask[rmy1:rmy2, rmx1:rmx2].astype(np.float32) / 255.0
    ref_mask_3ch = ref_mask_norm[:, :, np.newaxis]
    
    result[ry1:ry2, rx1:rx2] = (
        result[ry1:ry2, rx1:rx2].astype(np.float32) * (1 - ref_mask_3ch * 0.5) +
        reflection[rmy1:rmy2, rmx1:rmx2].astype(np.float32) * ref_mask_3ch * 0.5
    ).astype(np.uint8)

# 2. Ombre de contact (exactement au niveau du sol)
print("🌑 Ombre...")
shadow_h = max(8, int(new_h * 0.02))
shadow_w = int(new_w * 0.85)
shadow_x = car_x + (new_w - shadow_w) // 2
shadow_y = floor_y - shadow_h // 2  # Centrée sur la ligne du sol

shadow = np.zeros((shadow_h * 3, shadow_w), dtype=np.float32)
cv2.ellipse(shadow, (shadow_w // 2, shadow_h), (shadow_w // 2, shadow_h), 0, 0, 360, 1.0, -1)
shadow = cv2.GaussianBlur(shadow, (25, 25), 0)

for y in range(shadow.shape[0]):
    for x in range(shadow.shape[1]):
        img_y = shadow_y + y - shadow_h
        img_x = shadow_x + x
        if 0 <= img_y < bg_h and 0 <= img_x < bg_w:
            darkness = shadow[y, x] * 0.45
            result[img_y, img_x] = (result[img_y, img_x].astype(np.float32) * (1 - darkness)).astype(np.uint8)

# 3. Voiture
print("🚗 Composition...")
y1, y2 = max(0, car_y), min(bg_h, car_y + new_h)
x1, x2 = max(0, car_x), min(bg_w, car_x + new_w)
my1, my2 = max(0, -car_y), max(0, -car_y) + (y2 - y1)
mx1, mx2 = max(0, -car_x), max(0, -car_x) + (x2 - x1)

if y2 > y1 and x2 > x1:
    mask_norm = mask_resized[my1:my2, mx1:mx2].astype(np.float32) / 255.0
    mask_3ch = mask_norm[:, :, np.newaxis]
    
    result[y1:y2, x1:x2] = (
        result[y1:y2, x1:x2].astype(np.float32) * (1 - mask_3ch) +
        car_resized[my1:my2, mx1:mx2].astype(np.float32) * mask_3ch
    ).astype(np.uint8)

# Sauvegarder
output = "result_custom_studio_v2.jpg"
cv2.imwrite(output, cv2.cvtColor(result, cv2.COLOR_RGB2BGR), [cv2.IMWRITE_JPEG_QUALITY, 95])
print(f"\n✅ Résultat: {output}")
