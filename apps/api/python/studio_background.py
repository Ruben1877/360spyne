"""
STUDIO BACKGROUND MODULE - Clone Spyne
======================================
Utilise une vraie image de studio avec plateau tournant.
Positionne la voiture sur le cercle avec ombres et reflets realistes.
"""

import cv2
import numpy as np
from PIL import Image
import os
from typing import Tuple, Optional

class StudioBackground:
    """
    Gere les fonds de studio reels avec plateau tournant.
    """
    
    def __init__(self, background_path: str = None):
        """
        Initialise avec une image de fond studio.
        
        Args:
            background_path: Chemin vers l'image du studio
        """
        self.background_path = background_path
        self.background = None
        self.bg_height = 0
        self.bg_width = 0
        
        # Position du cercle (plateau tournant) - ajuste pour BACKGROUND 1.jpeg
        # Ces valeurs sont en pourcentage de l'image
        self.circle_center_x = 0.50  # Centre horizontal
        self.circle_center_y = 0.85  # Position verticale du cercle (bas de l'image)
        self.circle_radius = 0.28    # Rayon du cercle (ajuste pour le plateau)
        
        if background_path and os.path.exists(background_path):
            self.load_background(background_path)
    
    def load_background(self, path: str):
        """Charge l'image de fond."""
        self.background = cv2.imread(path)
        if self.background is not None:
            self.bg_height, self.bg_width = self.background.shape[:2]
            print(f"Background charge: {self.bg_width}x{self.bg_height}")
        else:
            print(f"Erreur: impossible de charger {path}")
    
    def get_circle_position(self) -> Tuple[int, int, int]:
        """
        Retourne la position du cercle (plateau) dans l'image.
        
        Returns:
            (center_x, center_y, radius) en pixels
        """
        cx = int(self.bg_width * self.circle_center_x)
        cy = int(self.bg_height * self.circle_center_y)
        r = int(min(self.bg_width, self.bg_height) * self.circle_radius)
        return cx, cy, r
    
    def place_car_on_turntable(self,
                                car_image: np.ndarray,
                                car_mask: np.ndarray,
                                scale: float = 0.6,
                                y_offset: float = 0.0) -> Tuple[np.ndarray, int, int]:
        """
        Place la voiture sur le plateau tournant.
        
        Args:
            car_image: Image de la voiture (BGR)
            car_mask: Masque de la voiture
            scale: Echelle de la voiture par rapport au cercle
            y_offset: Decalage vertical (negatif = vers le haut)
        
        Returns:
            (background_with_car, car_x, car_y)
        """
        if self.background is None:
            raise ValueError("Aucun fond charge")
        
        result = self.background.copy()
        car_h, car_w = car_image.shape[:2]
        
        # Obtenir position du cercle
        cx, cy, radius = self.get_circle_position()
        
        # Calculer la taille de la voiture
        target_width = int(radius * 2 * scale)
        aspect_ratio = car_h / car_w
        target_height = int(target_width * aspect_ratio)
        
        # Redimensionner la voiture
        car_resized = cv2.resize(car_image, (target_width, target_height))
        mask_resized = cv2.resize(car_mask, (target_width, target_height))
        
        # Position de la voiture (centree sur le cercle)
        car_x = cx - target_width // 2
        car_y = cy - target_height + int(target_height * 0.15) + int(y_offset * target_height)
        
        # Verifier les limites
        car_x = max(0, min(car_x, self.bg_width - target_width))
        car_y = max(0, min(car_y, self.bg_height - target_height))
        
        return result, car_resized, mask_resized, car_x, car_y
    
    def create_contact_shadow(self,
                               mask: np.ndarray,
                               blur: int = 15,
                               opacity: float = 0.4) -> np.ndarray:
        """
        Cree une ombre de contact sous la voiture.
        """
        h, w = mask.shape[:2]
        
        # Trouver le bas de la voiture
        coords = np.column_stack(np.where(mask > 0))
        if len(coords) == 0:
            return np.zeros((h, w), dtype=np.uint8)
        
        y_max = coords[:, 0].max()
        x_min, x_max = coords[:, 1].min(), coords[:, 1].max()
        
        # Creer une ombre elliptique
        shadow = np.zeros((h, w), dtype=np.uint8)
        
        # Dessiner une ellipse sous la voiture
        center = ((x_min + x_max) // 2, y_max + 5)
        axes = ((x_max - x_min) // 2, 20)
        cv2.ellipse(shadow, center, axes, 0, 0, 360, 255, -1)
        
        # Flouter
        shadow = cv2.GaussianBlur(shadow, (blur * 2 + 1, blur * 2 + 1), 0)
        
        # Appliquer opacite
        shadow = (shadow.astype(np.float32) * opacity).astype(np.uint8)
        
        return shadow
    
    def create_reflection(self,
                          car_image: np.ndarray,
                          car_mask: np.ndarray,
                          opacity: float = 0.15,
                          fade_height: float = 0.3) -> Tuple[np.ndarray, np.ndarray]:
        """
        Cree un reflet de la voiture.
        """
        h, w = car_image.shape[:2]
        
        # Trouver le bas de la voiture
        coords = np.column_stack(np.where(car_mask > 0))
        if len(coords) == 0:
            return np.zeros_like(car_image), np.zeros((h, w), dtype=np.uint8)
        
        y_max = coords[:, 0].max()
        
        # Prendre la partie basse de la voiture pour le reflet
        reflect_height = int(h * fade_height)
        bottom_portion = car_image[max(0, y_max - reflect_height):y_max, :]
        bottom_mask = car_mask[max(0, y_max - reflect_height):y_max, :]
        
        if bottom_portion.size == 0:
            return np.zeros_like(car_image), np.zeros((h, w), dtype=np.uint8)
        
        # Retourner verticalement
        reflection = cv2.flip(bottom_portion, 0)
        reflection_mask = cv2.flip(bottom_mask, 0)
        
        # Dimensions du reflet
        ref_h, ref_w = reflection.shape[:2]
        
        # Creer le gradient de fade avec les bonnes dimensions
        gradient = np.zeros((ref_h, ref_w), dtype=np.float32)
        for y in range(ref_h):
            t = y / max(ref_h, 1)
            gradient[y, :] = 1.0 - (t ** 0.7)
        
        # Appliquer gradient et opacite
        reflection_mask = (reflection_mask.astype(np.float32) / 255.0 * gradient * opacity * 255).astype(np.uint8)
        
        # Desaturer legerement
        if reflection.size > 0:
            hsv = cv2.cvtColor(reflection, cv2.COLOR_BGR2HSV).astype(np.float32)
            hsv[:, :, 1] *= 0.7
            reflection = cv2.cvtColor(np.clip(hsv, 0, 255).astype(np.uint8), cv2.COLOR_HSV2BGR)
            
            # Leger flou
            reflection = cv2.GaussianBlur(reflection, (3, 3), 0)
        
        return reflection, reflection_mask
    
    def composite_car_on_studio(self,
                                 car_image: np.ndarray,
                                 car_mask: np.ndarray,
                                 add_shadow: bool = True,
                                 add_reflection: bool = True,
                                 shadow_opacity: float = 0.4,
                                 reflection_opacity: float = 0.15,
                                 car_scale: float = 0.55) -> np.ndarray:
        """
        Composite complet: voiture + ombre + reflet sur le fond studio.
        
        Args:
            car_image: Image de la voiture (BGR)
            car_mask: Masque de la voiture
            add_shadow: Ajouter l'ombre de contact
            add_reflection: Ajouter le reflet
            shadow_opacity: Opacite de l'ombre
            reflection_opacity: Opacite du reflet
            car_scale: Echelle de la voiture
        
        Returns:
            Image composite finale
        """
        if self.background is None:
            raise ValueError("Aucun fond charge")
        
        # Placer la voiture
        result, car_resized, mask_resized, car_x, car_y = self.place_car_on_turntable(
            car_image, car_mask, scale=car_scale
        )
        
        car_h, car_w = car_resized.shape[:2]
        
        # 1. Ajouter le reflet (sous la voiture)
        if add_reflection:
            reflection, reflection_mask = self.create_reflection(
                car_resized, mask_resized, opacity=reflection_opacity
            )
            
            if reflection.size > 0:
                ref_h, ref_w = reflection.shape[:2]
                ref_y = car_y + car_h  # Juste sous la voiture
                
                # Verifier les limites
                if ref_y < self.bg_height and ref_h > 0:
                    # Calculer les regions
                    y1 = ref_y
                    y2 = min(ref_y + ref_h, self.bg_height)
                    x1 = car_x
                    x2 = min(car_x + ref_w, self.bg_width)
                    
                    # Dimensions effectives
                    eff_h = y2 - y1
                    eff_w = x2 - x1
                    
                    if eff_h > 0 and eff_w > 0:
                        # Extraire les regions avec les bonnes dimensions
                        ref_region = reflection[:eff_h, :eff_w]
                        mask_region = reflection_mask[:eff_h, :eff_w]
                        alpha = mask_region.astype(np.float32) / 255.0
                        
                        # Blend le reflet
                        for c in range(3):
                            bg_region = result[y1:y2, x1:x2, c].astype(np.float32)
                            result[y1:y2, x1:x2, c] = (bg_region * (1 - alpha) + ref_region[:, :, c].astype(np.float32) * alpha).astype(np.uint8)
        
        # 2. Ajouter l'ombre de contact
        if add_shadow:
            shadow = self.create_contact_shadow(mask_resized, opacity=shadow_opacity)
            
            # Position de l'ombre (au niveau des roues)
            coords = np.column_stack(np.where(mask_resized > 0))
            if len(coords) > 0:
                y_max = coords[:, 0].max()
                shadow_y = car_y + y_max - shadow.shape[0] // 2
                
                # Appliquer l'ombre (assombrir le fond)
                for y in range(shadow.shape[0]):
                    for x in range(shadow.shape[1]):
                        bg_y = shadow_y + y
                        bg_x = car_x + x
                        
                        if 0 <= bg_y < self.bg_height and 0 <= bg_x < self.bg_width:
                            darkness = shadow[y, x] / 255.0
                            result[bg_y, bg_x] = (result[bg_y, bg_x].astype(np.float32) * (1 - darkness)).astype(np.uint8)
        
        # 3. Ajouter la voiture
        alpha = mask_resized.astype(np.float32) / 255.0
        alpha = np.dstack([alpha] * 3)
        
        y1, y2 = car_y, min(car_y + car_h, self.bg_height)
        x1, x2 = car_x, min(car_x + car_w, self.bg_width)
        
        car_region = car_resized[:y2-car_y, :x2-car_x].astype(np.float32)
        bg_region = result[y1:y2, x1:x2].astype(np.float32)
        alpha_region = alpha[:y2-car_y, :x2-car_x]
        
        result[y1:y2, x1:x2] = (bg_region * (1 - alpha_region) + car_region * alpha_region).astype(np.uint8)
        
        return result
    
    def resize_to_match(self, target_width: int, target_height: int):
        """
        Redimensionne le fond pour correspondre a une taille cible.
        """
        if self.background is not None:
            self.background = cv2.resize(self.background, (target_width, target_height))
            self.bg_height, self.bg_width = self.background.shape[:2]


if __name__ == "__main__":
    import sys
    
    # Test
    bg_path = "backgrounds/background1.jpeg"
    
    studio = StudioBackground(bg_path)
    print(f"Background: {studio.bg_width}x{studio.bg_height}")
    
    cx, cy, r = studio.get_circle_position()
    print(f"Cercle: centre=({cx}, {cy}), rayon={r}")

