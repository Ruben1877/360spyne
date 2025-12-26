"""
BACKGROUND 3D STUDIO - Spyne Exact Quality
==========================================
Génère des environnements 3D de showroom identiques à Spyne.

Éléments reproduits :
- Murs avec panneaux verticaux
- Plafond avec softbox lumineux
- Sol ultra-réfléchissant
- Perspective 3D correcte
- Reflet miroir de la voiture
"""

import cv2
import numpy as np
from typing import Tuple, Dict, Optional
import math


class Studio3DGenerator:
    """
    Génère des environnements de studio 3D comme Spyne.
    """
    
    # Presets de studios 3D
    STUDIO_PRESETS = {
        'spyne_showroom': {
            # Couleurs
            'wall_base': (235, 235, 238),
            'wall_groove': (215, 215, 220),
            'floor_base': (195, 195, 200),
            'floor_reflection': (210, 210, 215),
            'ceiling': (250, 250, 252),
            'softbox': (255, 255, 255),
            # Géométrie
            'horizon': 0.55,
            'vanishing_point': 0.50,  # Centre horizontal
            'panel_count': 12,
            'groove_width': 3,
            # Éclairage
            'softbox_width': 0.4,
            'softbox_height': 0.15,
            'ambient_intensity': 0.95,
        },
        'spyne_white': {
            'wall_base': (248, 248, 250),
            'wall_groove': (235, 235, 240),
            'floor_base': (225, 225, 230),
            'floor_reflection': (240, 240, 245),
            'ceiling': (255, 255, 255),
            'softbox': (255, 255, 255),
            'horizon': 0.52,
            'vanishing_point': 0.50,
            'panel_count': 10,
            'groove_width': 2,
            'softbox_width': 0.35,
            'softbox_height': 0.12,
            'ambient_intensity': 1.0,
        },
        'spyne_dark': {
            'wall_base': (75, 75, 80),
            'wall_groove': (55, 55, 60),
            'floor_base': (45, 45, 50),
            'floor_reflection': (60, 60, 65),
            'ceiling': (90, 90, 95),
            'softbox': (200, 200, 210),
            'horizon': 0.55,
            'vanishing_point': 0.50,
            'panel_count': 12,
            'groove_width': 3,
            'softbox_width': 0.4,
            'softbox_height': 0.15,
            'ambient_intensity': 0.85,
        }
    }
    
    def create_3d_studio(self,
                         width: int,
                         height: int,
                         preset: str = 'spyne_showroom') -> np.ndarray:
        """
        Crée un environnement de studio 3D complet.
        """
        config = self.STUDIO_PRESETS.get(preset, self.STUDIO_PRESETS['spyne_showroom'])
        
        # Canvas
        studio = np.zeros((height, width, 3), dtype=np.uint8)
        
        horizon_y = int(height * config['horizon'])
        vp_x = int(width * config['vanishing_point'])
        
        # 1. Dessiner le plafond avec softbox
        studio = self._draw_ceiling(studio, config, horizon_y, vp_x)
        
        # 2. Dessiner les murs avec panneaux
        studio = self._draw_walls(studio, config, horizon_y, vp_x)
        
        # 3. Dessiner le sol réfléchissant
        studio = self._draw_floor(studio, config, horizon_y, vp_x)
        
        # 4. Ajouter l'éclairage ambiant
        studio = self._add_ambient_lighting(studio, config)
        
        return studio
    
    def _draw_ceiling(self,
                      img: np.ndarray,
                      config: Dict,
                      horizon_y: int,
                      vp_x: int) -> np.ndarray:
        """
        Dessine le plafond avec le softbox lumineux.
        """
        h, w = img.shape[:2]
        ceiling_color = np.array(config['ceiling'], dtype=np.uint8)
        softbox_color = np.array(config['softbox'], dtype=np.uint8)
        
        # Zone du plafond (au-dessus de l'horizon, partie haute)
        ceiling_bottom = int(horizon_y * 0.6)
        
        # Remplir le plafond avec gradient
        for y in range(ceiling_bottom):
            t = y / ceiling_bottom
            # Gradient du plafond (plus clair vers le softbox)
            color = ceiling_color * (0.95 + t * 0.05)
            img[y, :] = np.clip(color, 0, 255).astype(np.uint8)
        
        # Dessiner le softbox (rectangle lumineux)
        softbox_w = int(w * config['softbox_width'])
        softbox_h = int(ceiling_bottom * config['softbox_height'])
        softbox_x = (w - softbox_w) // 2
        softbox_y = int(ceiling_bottom * 0.3)
        
        # Softbox avec bords doux
        for y in range(softbox_y, softbox_y + softbox_h):
            for x in range(softbox_x, softbox_x + softbox_w):
                if 0 <= y < h and 0 <= x < w:
                    # Distance depuis le bord
                    dx = min(x - softbox_x, softbox_x + softbox_w - x) / (softbox_w / 2)
                    dy = min(y - softbox_y, softbox_y + softbox_h - y) / (softbox_h / 2)
                    edge_factor = min(dx, dy) ** 0.3
                    
                    color = ceiling_color + (softbox_color - ceiling_color) * edge_factor
                    img[y, x] = np.clip(color, 0, 255).astype(np.uint8)
        
        # Lignes de perspective sur le plafond
        line_color = (config['wall_groove'][0] - 20,
                      config['wall_groove'][1] - 20,
                      config['wall_groove'][2] - 20)
        
        # Lignes diagonales vers le point de fuite
        for offset in [-0.3, 0.3]:
            x_start = int(w * (0.5 + offset))
            cv2.line(img, (x_start, 0), (vp_x, horizon_y), line_color, 1, cv2.LINE_AA)
        
        return img
    
    def _draw_walls(self,
                    img: np.ndarray,
                    config: Dict,
                    horizon_y: int,
                    vp_x: int) -> np.ndarray:
        """
        Dessine les murs avec panneaux verticaux en perspective.
        """
        h, w = img.shape[:2]
        wall_color = np.array(config['wall_base'], dtype=np.float32)
        groove_color = np.array(config['wall_groove'], dtype=np.float32)
        
        ceiling_bottom = int(horizon_y * 0.6)
        
        # Zone des murs
        wall_top = ceiling_bottom
        wall_bottom = horizon_y
        
        panel_count = config['panel_count']
        groove_width = config['groove_width']
        
        # Dessiner le fond des murs avec gradient de profondeur
        for y in range(wall_top, wall_bottom):
            t = (y - wall_top) / (wall_bottom - wall_top)
            # Plus sombre vers le bas (ombre)
            brightness = 1.0 - t * 0.08
            color = wall_color * brightness
            img[y, :] = np.clip(color, 0, 255).astype(np.uint8)
        
        # Dessiner les rainures verticales des panneaux
        panel_width = w // panel_count
        
        for i in range(panel_count + 1):
            # Position X avec perspective (converge vers le point de fuite)
            x_top = int(i * panel_width)
            
            # Calculer la convergence vers le point de fuite
            convergence = 0.15  # Force de la perspective
            x_at_horizon = int(x_top + (vp_x - x_top) * convergence)
            
            # Dessiner la rainure comme une ligne qui converge
            for y in range(wall_top, wall_bottom):
                t = (y - wall_top) / (wall_bottom - wall_top)
                x = int(x_top + (x_at_horizon - x_top) * t)
                
                # Dessiner la rainure (plusieurs pixels de large)
                for dx in range(-groove_width // 2, groove_width // 2 + 1):
                    if 0 <= x + dx < w:
                        # Effet 3D sur la rainure
                        if dx < 0:
                            color = groove_color * 0.85  # Ombre
                        elif dx > 0:
                            color = groove_color * 1.1   # Highlight
                        else:
                            color = groove_color
                        
                        img[y, x + dx] = np.clip(color, 0, 255).astype(np.uint8)
        
        return img
    
    def _draw_floor(self,
                    img: np.ndarray,
                    config: Dict,
                    horizon_y: int,
                    vp_x: int) -> np.ndarray:
        """
        Dessine le sol ultra-réfléchissant.
        """
        h, w = img.shape[:2]
        floor_color = np.array(config['floor_base'], dtype=np.float32)
        reflection_color = np.array(config['floor_reflection'], dtype=np.float32)
        
        # Zone du sol
        for y in range(horizon_y, h):
            t = (y - horizon_y) / (h - horizon_y)
            
            # Gradient du sol (plus sombre vers l'avant)
            base_brightness = 1.0 - t * 0.15
            
            # Zone de reflet (plus claire au centre/haut)
            reflection_strength = (1 - t) ** 2 * 0.3
            
            for x in range(w):
                # Plus réfléchissant au centre
                x_center = abs(x - w/2) / (w/2)
                center_boost = (1 - x_center ** 2) * reflection_strength
                
                color = floor_color * base_brightness
                color = color + (reflection_color - floor_color) * center_boost
                
                img[y, x] = np.clip(color, 0, 255).astype(np.uint8)
        
        # Ajouter une ligne subtile à l'horizon
        cv2.line(img, (0, horizon_y), (w, horizon_y), 
                 tuple(int(c * 0.95) for c in config['wall_groove']), 1)
        
        return img
    
    def _add_ambient_lighting(self,
                               img: np.ndarray,
                               config: Dict) -> np.ndarray:
        """
        Ajoute l'éclairage ambiant du studio.
        """
        h, w = img.shape[:2]
        intensity = config['ambient_intensity']
        
        # Gradient de lumière du haut
        Y, X = np.ogrid[:h, :w]
        
        # Lumière principale du softbox (centre-haut)
        center_x = w // 2
        center_y = int(h * 0.2)
        
        dist = np.sqrt(((X - center_x) / (w * 0.5)) ** 2 + 
                       ((Y - center_y) / (h * 0.8)) ** 2)
        
        light = 1 + (1 - np.clip(dist, 0, 1)) * 0.08 * intensity
        light = light[:, :, np.newaxis]
        
        result = img.astype(np.float32) * light
        return np.clip(result, 0, 255).astype(np.uint8)
    
    def add_car_reflection(self,
                           studio: np.ndarray,
                           car_image: np.ndarray,
                           car_mask: np.ndarray,
                           car_position: Tuple[int, int],
                           opacity: float = 0.35) -> np.ndarray:
        """
        Ajoute le reflet de la voiture sur le sol.
        """
        h, w = studio.shape[:2]
        car_h, car_w = car_image.shape[:2]
        car_x, car_y = car_position
        
        # Flip vertical pour le reflet
        reflection = cv2.flip(car_image, 0)
        reflection_mask = cv2.flip(car_mask, 0)
        
        # Position du reflet (juste sous la voiture)
        ref_y = car_y + car_h
        
        # Appliquer gradient de fade sur le reflet
        for y in range(reflection.shape[0]):
            fade = 1 - (y / reflection.shape[0]) ** 0.7
            reflection[y] = (reflection[y] * fade * opacity).astype(np.uint8)
            reflection_mask[y] = (reflection_mask[y] * fade * opacity).astype(np.uint8)
        
        # Légère compression verticale (perspective)
        new_h = int(car_h * 0.6)
        reflection = cv2.resize(reflection, (car_w, new_h))
        reflection_mask = cv2.resize(reflection_mask, (car_w, new_h))
        
        # Composer sur le studio
        result = studio.copy()
        
        y1 = max(0, ref_y)
        y2 = min(h, ref_y + new_h)
        x1 = max(0, car_x)
        x2 = min(w, car_x + car_w)
        
        ry1 = max(0, -ref_y)
        ry2 = ry1 + (y2 - y1)
        rx1 = max(0, -car_x)
        rx2 = rx1 + (x2 - x1)
        
        if y2 > y1 and x2 > x1:
            mask_norm = reflection_mask[ry1:ry2, rx1:rx2].astype(np.float32) / 255.0
            mask_3ch = mask_norm[:, :, np.newaxis]
            
            result[y1:y2, x1:x2] = (
                result[y1:y2, x1:x2].astype(np.float32) * (1 - mask_3ch * 0.5) +
                reflection[ry1:ry2, rx1:rx2].astype(np.float32) * mask_3ch * 0.5
            ).astype(np.uint8)
        
        return result


def create_spyne_exact_render(car_image: np.ndarray,
                               car_mask: np.ndarray,
                               preset: str = 'spyne_showroom',
                               output_size: Tuple[int, int] = (1920, 1080)) -> np.ndarray:
    """
    Crée un rendu EXACT comme Spyne avec fond 3D.
    """
    w, h = output_size
    
    # 1. Créer le studio 3D
    studio_gen = Studio3DGenerator()
    studio = studio_gen.create_3d_studio(w, h, preset)
    
    # 2. Redimensionner la voiture
    car_h, car_w = car_image.shape[:2]
    scale = min(w * 0.70 / car_w, h * 0.55 / car_h)
    new_w = int(car_w * scale)
    new_h = int(car_h * scale)
    
    car_resized = cv2.resize(car_image, (new_w, new_h), interpolation=cv2.INTER_LANCZOS4)
    mask_resized = cv2.resize(car_mask, (new_w, new_h), interpolation=cv2.INTER_LANCZOS4)
    
    # 3. Position de la voiture
    car_x = (w - new_w) // 2
    horizon_y = int(h * 0.55)
    car_y = horizon_y - new_h + int(new_h * 0.15)
    
    # 4. Ajouter le reflet de la voiture sur le sol
    result = studio_gen.add_car_reflection(studio, car_resized, mask_resized, 
                                            (car_x, car_y), opacity=0.4)
    
    # 5. Ajouter l'ombre sous la voiture
    result = _add_car_shadow(result, mask_resized, (car_x, car_y), horizon_y)
    
    # 6. Composer la voiture
    y1 = max(0, car_y)
    y2 = min(h, car_y + new_h)
    x1 = max(0, car_x)
    x2 = min(w, car_x + new_w)
    
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
    
    return result


def _add_car_shadow(img: np.ndarray,
                    mask: np.ndarray,
                    car_pos: Tuple[int, int],
                    floor_y: int) -> np.ndarray:
    """
    Ajoute une ombre réaliste sous la voiture.
    """
    h, w = img.shape[:2]
    car_x, car_y = car_pos
    car_h, car_w = mask.shape[:2]
    
    result = img.copy().astype(np.float32)
    
    # Créer l'ombre de contact
    shadow_h = int(car_h * 0.03)
    shadow_w = int(car_w * 0.95)
    
    shadow_x = car_x + (car_w - shadow_w) // 2
    shadow_y = floor_y - 2
    
    # Ombre elliptique floue
    shadow = np.zeros((shadow_h * 3, shadow_w), dtype=np.float32)
    cv2.ellipse(shadow, (shadow_w // 2, shadow_h), (shadow_w // 2, shadow_h),
                0, 0, 360, 1.0, -1)
    shadow = cv2.GaussianBlur(shadow, (21, 21), 0)
    
    # Appliquer l'ombre
    for y in range(shadow.shape[0]):
        for x in range(shadow.shape[1]):
            img_y = shadow_y + y
            img_x = shadow_x + x
            if 0 <= img_y < h and 0 <= img_x < w:
                darkness = shadow[y, x] * 0.4
                result[img_y, img_x] = result[img_y, img_x] * (1 - darkness)
    
    return np.clip(result, 0, 255).astype(np.uint8)


if __name__ == "__main__":
    # Test: générer les studios 3D
    gen = Studio3DGenerator()
    
    for preset in ['spyne_showroom', 'spyne_white', 'spyne_dark']:
        studio = gen.create_3d_studio(1920, 1080, preset)
        cv2.imwrite(f"studio3d_{preset}.png", cv2.cvtColor(studio, cv2.COLOR_RGB2BGR))
        print(f"✅ {preset} saved")
    
    print("\n🎨 Studios 3D générés !")

