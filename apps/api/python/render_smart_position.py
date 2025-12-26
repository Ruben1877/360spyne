#!/usr/bin/env python3
"""
Positionnement intelligent - Détecte les points de contact des roues
Fonctionne même avec des voitures en angle (3/4 view)
"""
import cv2
import numpy as np

print("🎨 Rendu avec positionnement intelligent...")

def find_wheel_contact_points(mask):
    """
    Trouve les points de contact des roues (bas gauche et bas droit).
    Fonctionne même si la voiture est en angle.
    """
    h, w = mask.shape[:2]
    
    # Diviser le masque en deux moitiés (gauche/droite)
    left_half = mask[:, :w//2]
    right_half = mask[:, w//2:]
    
    # Trouver le point le plus bas dans chaque moitié
    left_coords = np.column_stack(np.where(left_half > 128))
    right_coords = np.column_stack(np.where(right_half > 128))
    
    left_bottom = 0
    right_bottom = 0
    left_x = w // 4
    right_x = w * 3 // 4
    
    if len(left_coords) > 0:
        # Trouver le point le plus bas à gauche
        max_y_idx = left_coords[:, 0].argmax()
        left_bottom = left_coords[max_y_idx, 0]
        left_x = left_coords[max_y_idx, 1]
    
    if len(right_coords) > 0:
        # Trouver le point le plus bas à droite
        max_y_idx = right_coords[:, 0].argmax()
        right_bottom = right_coords[max_y_idx, 0]
        right_x = right_coords[max_y_idx, 1] + w // 2
    
    # Le point de contact effectif est le plus bas des deux
    contact_y = max(left_bottom, right_bottom)
    
    # Calculer l'angle de la voiture (différence entre gauche et droite)
    angle_diff = right_bottom - left_bottom
    
    return {
        'contact_y': contact_y,
        'left_bottom': left_bottom,
        'right_bottom': right_bottom,
        'left_x': left_x,
        'right_x': right_x,
        'angle_diff': angle_diff,
        'is_angled': abs(angle_diff) > 10
    }

def find_floor_line(background):
    """
    Détecte automatiquement la ligne du sol dans le fond.
    Cherche le changement de luminosité mur/sol.
    """
    h, w = background.shape[:2]
    gray = cv2.cvtColor(background, cv2.COLOR_RGB2GRAY) if len(background.shape) == 3 else background
    
    # Analyser la colonne centrale
    center_col = gray[:, w//2]
    
    # Chercher le gradient maximum (changement mur -> sol)
    gradient = np.abs(np.diff(center_col.astype(float)))
    
    # Chercher dans la zone probable (40% - 80% de la hauteur)
    search_start = int(h * 0.4)
    search_end = int(h * 0.8)
    
    gradient_zone = gradient[search_start:search_end]
    if len(gradient_zone) > 0:
        max_gradient_idx = np.argmax(gradient_zone)
        floor_y = search_start + max_gradient_idx
    else:
        floor_y = int(h * 0.72)  # Fallback
    
    return floor_y

# Charger le fond
bg_path = "backgrounds/background1.jpeg"
background = cv2.imread(bg_path)
background = cv2.cvtColor(background, cv2.COLOR_BGR2RGB)
bg_h, bg_w = background.shape[:2]
print(f"✅ Fond: {bg_w}x{bg_h}")

# Détecter la ligne du sol automatiquement
floor_y = find_floor_line(background)
print(f"📍 Sol détecté à: {floor_y}px ({floor_y/bg_h*100:.1f}%)")

# Charger et segmenter la voiture
car_image = cv2.imread("test_car.jpg")
car_image_bgr = car_image.copy()
car_image = cv2.cvtColor(car_image, cv2.COLOR_BGR2RGB)

print("🔍 Segmentation...")
from segmentation import Segmentation
from edge_smoothing import EdgeSmoothing

seg = Segmentation()
mask = seg.segment(car_image_bgr)
smooth = EdgeSmoothing()
mask = smooth.full_edge_refinement(car_image_bgr, mask)

# Analyser les points de contact
contact_info = find_wheel_contact_points(mask)
print(f"🔍 Points de contact:")
print(f"   Gauche: y={contact_info['left_bottom']}")
print(f"   Droite: y={contact_info['right_bottom']}")
print(f"   Angle: {'Oui' if contact_info['is_angled'] else 'Non'} (diff={contact_info['angle_diff']}px)")

# Redimensionner
car_h, car_w = car_image.shape[:2]
scale = min(bg_w * 0.55 / car_w, bg_h * 0.45 / car_h)
new_w = int(car_w * scale)
new_h = int(car_h * scale)

car_resized = cv2.resize(car_image, (new_w, new_h), interpolation=cv2.INTER_LANCZOS4)
mask_resized = cv2.resize(mask, (new_w, new_h), interpolation=cv2.INTER_LANCZOS4)

# Recalculer les points de contact après redimensionnement
contact_y_scaled = int(contact_info['contact_y'] * scale)

# === POSITIONNEMENT INTELLIGENT ===
# Positionner pour que le point de contact le plus bas touche le sol
car_y = floor_y - contact_y_scaled
car_x = (bg_w - new_w) // 2

print(f"🚗 Position finale: ({car_x}, {car_y})")
print(f"   Point de contact au sol: {car_y + contact_y_scaled} = {floor_y} ✓")

# Créer le résultat
result = background.copy()

# 1. Reflet
print("🪞 Reflet...")
reflection = cv2.flip(car_resized, 0)
reflection_mask = cv2.flip(mask_resized, 0)

ref_h = int(new_h * 0.4)
reflection = cv2.resize(reflection, (new_w, ref_h))
reflection_mask = cv2.resize(reflection_mask, (new_w, ref_h))

for y in range(ref_h):
    fade = (1 - y / ref_h) ** 2 * 0.25
    reflection[y] = (reflection[y] * fade).astype(np.uint8)
    reflection_mask[y] = (reflection_mask[y] * fade).astype(np.uint8)

ref_y = floor_y + 3
ry1, ry2 = max(0, ref_y), min(bg_h, ref_y + ref_h)
rx1, rx2 = max(0, car_x), min(bg_w, car_x + new_w)

if ry2 > ry1 and rx2 > rx1:
    rmy1 = max(0, -ref_y)
    rmy2 = rmy1 + (ry2 - ry1)
    rmx1 = max(0, -car_x)
    rmx2 = rmx1 + (rx2 - rx1)
    
    if rmy2 <= ref_h and rmx2 <= new_w:
        ref_mask_norm = reflection_mask[rmy1:rmy2, rmx1:rmx2].astype(np.float32) / 255.0
        ref_mask_3ch = ref_mask_norm[:, :, np.newaxis]
        
        result[ry1:ry2, rx1:rx2] = (
            result[ry1:ry2, rx1:rx2].astype(np.float32) * (1 - ref_mask_3ch * 0.4) +
            reflection[rmy1:rmy2, rmx1:rmx2].astype(np.float32) * ref_mask_3ch * 0.4
        ).astype(np.uint8)

# 2. Ombre de contact
print("🌑 Ombre...")
shadow_h = max(10, int(new_h * 0.018))
shadow_w = int(new_w * 0.82)
shadow_x = car_x + (new_w - shadow_w) // 2
shadow_y = floor_y - shadow_h // 2

shadow = np.zeros((shadow_h * 3, shadow_w), dtype=np.float32)
cv2.ellipse(shadow, (shadow_w // 2, shadow_h), (shadow_w // 2, shadow_h), 0, 0, 360, 1.0, -1)
shadow = cv2.GaussianBlur(shadow, (21, 21), 0)

for y in range(shadow.shape[0]):
    for x in range(shadow.shape[1]):
        img_y = shadow_y + y - shadow_h
        img_x = shadow_x + x
        if 0 <= img_y < bg_h and 0 <= img_x < bg_w:
            darkness = shadow[y, x] * 0.4
            result[img_y, img_x] = (result[img_y, img_x].astype(np.float32) * (1 - darkness)).astype(np.uint8)

# 3. Voiture
print("🚗 Composition...")
y1, y2 = max(0, car_y), min(bg_h, car_y + new_h)
x1, x2 = max(0, car_x), min(bg_w, car_x + new_w)
my1 = max(0, -car_y)
my2 = my1 + (y2 - y1)
mx1 = max(0, -car_x)
mx2 = mx1 + (x2 - x1)

if y2 > y1 and x2 > x1 and my2 <= new_h and mx2 <= new_w:
    mask_norm = mask_resized[my1:my2, mx1:mx2].astype(np.float32) / 255.0
    mask_3ch = mask_norm[:, :, np.newaxis]
    
    result[y1:y2, x1:x2] = (
        result[y1:y2, x1:x2].astype(np.float32) * (1 - mask_3ch) +
        car_resized[my1:my2, mx1:mx2].astype(np.float32) * mask_3ch
    ).astype(np.uint8)

# Sauvegarder
output = "result_smart_position.jpg"
cv2.imwrite(output, cv2.cvtColor(result, cv2.COLOR_RGB2BGR), [cv2.IMWRITE_JPEG_QUALITY, 95])
print(f"\n✅ Résultat: {output}")
