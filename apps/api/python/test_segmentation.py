"""
Test de segmentation sur une image
Usage: python test_segmentation.py chemin/image.jpg
"""

import sys
import cv2
import numpy as np
from PIL import Image
import os

# Installer rembg si pas disponible
try:
    from rembg import remove, new_session
    print("rembg OK")
except ImportError:
    print("Installation de rembg...")
    os.system("pip install rembg[cpu]")
    from rembg import remove, new_session

def segment_car(image_path, output_dir="output"):
    """Segmente une voiture et sauvegarde les resultats"""
    
    # Creer dossier output
    os.makedirs(output_dir, exist_ok=True)
    
    # Charger image
    print(f"\nChargement: {image_path}")
    image = cv2.imread(image_path)
    if image is None:
        print(f"Erreur: impossible de charger {image_path}")
        return
    
    h, w = image.shape[:2]
    print(f"Taille: {w}x{h}")
    
    # Convertir BGR -> RGB
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    pil_image = Image.fromarray(image_rgb)
    
    # Charger modele ISNet (meilleur pour les objets)
    print("\nChargement du modele ISNet...")
    session = new_session("isnet-general-use")
    
    # Segmentation
    print("Segmentation en cours...")
    
    # 1. Obtenir le masque
    mask = remove(pil_image, session=session, only_mask=True)
    mask_np = np.array(mask)
    
    # 2. Obtenir l'image sans fond (RGBA)
    result_rgba = remove(pil_image, session=session)
    
    # Sauvegarder les resultats
    base_name = os.path.splitext(os.path.basename(image_path))[0]
    
    # Masque
    mask_path = os.path.join(output_dir, f"{base_name}_mask.png")
    cv2.imwrite(mask_path, mask_np)
    print(f"Masque: {mask_path}")
    
    # Image sans fond (PNG transparent)
    nobg_path = os.path.join(output_dir, f"{base_name}_nobg.png")
    result_rgba.save(nobg_path)
    print(f"Sans fond: {nobg_path}")
    
    # Image avec fond blanc
    white_bg = Image.new("RGBA", result_rgba.size, (255, 255, 255, 255))
    white_bg.paste(result_rgba, mask=result_rgba.split()[3])
    white_path = os.path.join(output_dir, f"{base_name}_white_bg.png")
    white_bg.convert("RGB").save(white_path)
    print(f"Fond blanc: {white_path}")
    
    # Image avec fond gris studio
    gray_bg = Image.new("RGBA", result_rgba.size, (240, 240, 240, 255))
    gray_bg.paste(result_rgba, mask=result_rgba.split()[3])
    gray_path = os.path.join(output_dir, f"{base_name}_studio_bg.png")
    gray_bg.convert("RGB").save(gray_path)
    print(f"Fond studio: {gray_path}")
    
    # Overlay (image originale + masque en rouge)
    overlay = image_rgb.copy()
    mask_colored = np.zeros_like(image_rgb)
    mask_colored[:,:,0] = mask_np  # Rouge
    overlay = cv2.addWeighted(overlay, 0.7, mask_colored, 0.3, 0)
    overlay_path = os.path.join(output_dir, f"{base_name}_overlay.png")
    cv2.imwrite(overlay_path, cv2.cvtColor(overlay, cv2.COLOR_RGB2BGR))
    print(f"Overlay: {overlay_path}")
    
    print(f"\nTermine! Resultats dans: {output_dir}/")
    return mask_np

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_segmentation.py chemin/image.jpg")
        print("\nExemple:")
        print("  python test_segmentation.py ma_voiture.jpg")
        sys.exit(1)
    
    image_path = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "output"
    
    segment_car(image_path, output_dir)

