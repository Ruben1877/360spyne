"""
BACKGROUND GENERATOR V2 - Spyne Quality
========================================
Version améliorée avec rendu studio professionnel identique à Spyne.

Améliorations :
- Horizon courbé (cyclorama studio)
- Texture subtile
- Éclairage studio réaliste
- Spots lumineux
- Gradient premium
"""

import cv2
import numpy as np
from typing import Tuple, Dict, Optional


class BackgroundGeneratorV2:
    """
    Générateur de fonds studio qualité Spyne.
    """
    
    # Presets Spyne (analysés frame par frame)
    PRESETS = {
        'spyne_white': {
            'wall_top': (252, 252, 252),
            'wall_bottom': (242, 242, 244),
            'floor_start': (235, 235, 238),
            'floor_end': (218, 218, 222),
            'horizon_position': 0.62,
            'curve_intensity': 0.08,
            'ambient_color': (255, 253, 250),  # Warm white
            'ambient_intensity': 0.03,
        },
        'spyne_grey': {
            'wall_top': (240, 240, 242),
            'wall_bottom': (220, 220, 224),
            'floor_start': (205, 205, 210),
            'floor_end': (175, 175, 182),
            'horizon_position': 0.62,
            'curve_intensity': 0.06,
            'ambient_color': (245, 248, 255),  # Cool white
            'ambient_intensity': 0.04,
        },
        'spyne_dark': {
            'wall_top': (85, 85, 90),
            'wall_bottom': (55, 55, 60),
            'floor_start': (45, 45, 50),
            'floor_end': (28, 28, 32),
            'horizon_position': 0.60,
            'curve_intensity': 0.05,
            'ambient_color': (200, 210, 230),
            'ambient_intensity': 0.02,
        },
        'spyne_showroom': {
            'wall_top': (250, 250, 252),
            'wall_bottom': (235, 235, 240),
            'floor_start': (225, 225, 230),
            'floor_end': (200, 200, 208),
            'horizon_position': 0.58,
            'curve_intensity': 0.10,
            'ambient_color': (255, 252, 248),
            'ambient_intensity': 0.05,
        },
    }
    
    def create_spyne_background(self,
                                 width: int,
                                 height: int,
                                 preset: str = 'spyne_white') -> np.ndarray:
        """
        Crée un fond studio identique à Spyne.
        """
        config = self.PRESETS.get(preset, self.PRESETS['spyne_white'])
        
        # 1. Créer le fond de base avec cyclorama courbé
        bg = self._create_cyclorama(width, height, config)
        
        # 2. Ajouter l'éclairage studio
        bg = self._add_studio_lighting(bg, config)
        
        # 3. Ajouter texture subtile
        bg = self._add_subtle_texture(bg, intensity=0.008)
        
        # 4. Ajouter vignette douce
        bg = self._add_soft_vignette(bg, strength=0.12)
        
        # 5. Ajouter spot lumineux central (comme Spyne)
        bg = self._add_center_spotlight(bg, config)
        
        return bg
    
    def _create_cyclorama(self,
                          width: int,
                          height: int,
                          config: Dict) -> np.ndarray:
        """
        Crée un cyclorama (fond studio courbé) comme dans les vrais studios photo.
        """
        bg = np.zeros((height, width, 3), dtype=np.float32)
        
        wall_top = np.array(config['wall_top'], dtype=np.float32)
        wall_bottom = np.array(config['wall_bottom'], dtype=np.float32)
        floor_start = np.array(config['floor_start'], dtype=np.float32)
        floor_end = np.array(config['floor_end'], dtype=np.float32)
        
        horizon_y = int(height * config['horizon_position'])
        curve_intensity = config['curve_intensity']
        
        # Partie murale (gradient vertical avec légère courbe)
        for y in range(horizon_y):
            t = y / horizon_y
            # Easing cubique pour transition douce
            t_eased = t * t * (3 - 2 * t)
            color = wall_top + (wall_bottom - wall_top) * t_eased
            bg[y, :] = color
        
        # Zone de transition courbée (cyclorama)
        curve_height = int(height * curve_intensity)
        for y in range(horizon_y, min(horizon_y + curve_height, height)):
            t = (y - horizon_y) / curve_height
            # Courbe sinusoïdale pour transition naturelle
            t_curved = np.sin(t * np.pi / 2)
            color = wall_bottom + (floor_start - wall_bottom) * t_curved
            
            # Ajouter légère variation horizontale (effet 3D)
            for x in range(width):
                x_factor = 1 - abs(x - width/2) / (width/2) * 0.02
                bg[y, x] = color * x_factor
        
        # Partie sol (gradient avec perspective)
        floor_start_y = horizon_y + curve_height
        for y in range(floor_start_y, height):
            t = (y - floor_start_y) / (height - floor_start_y)
            # Gradient accéléré vers le bas (perspective)
            t_perspective = t ** 0.8
            color = floor_start + (floor_end - floor_start) * t_perspective
            bg[y, :] = color
        
        return np.clip(bg, 0, 255).astype(np.uint8)
    
    def _add_studio_lighting(self,
                              bg: np.ndarray,
                              config: Dict) -> np.ndarray:
        """
        Ajoute l'éclairage studio (softbox simulation).
        """
        h, w = bg.shape[:2]
        result = bg.astype(np.float32)
        
        ambient_color = np.array(config['ambient_color'], dtype=np.float32) / 255.0
        intensity = config['ambient_intensity']
        
        # Créer un gradient d'éclairage du haut
        Y, X = np.ogrid[:h, :w]
        
        # Lumière principale du haut
        light_top = 1 - (Y / h) ** 0.5
        light_top = light_top[:, :, np.newaxis] * intensity
        
        # Appliquer la teinte ambiante
        result = result + (result * light_top * ambient_color)
        
        return np.clip(result, 0, 255).astype(np.uint8)
    
    def _add_subtle_texture(self,
                            bg: np.ndarray,
                            intensity: float = 0.01) -> np.ndarray:
        """
        Ajoute une texture très subtile pour éviter le banding.
        """
        h, w = bg.shape[:2]
        
        # Générer bruit gaussien
        noise = np.random.normal(0, 1, (h, w, 3)).astype(np.float32)
        
        # Appliquer avec intensité très faible
        result = bg.astype(np.float32) + noise * intensity * 255
        
        return np.clip(result, 0, 255).astype(np.uint8)
    
    def _add_soft_vignette(self,
                           bg: np.ndarray,
                           strength: float = 0.15) -> np.ndarray:
        """
        Ajoute une vignette douce (bords légèrement plus sombres).
        """
        h, w = bg.shape[:2]
        
        Y, X = np.ogrid[:h, :w]
        center_y, center_x = h / 2, w / 2
        
        # Distance elliptique (plus large horizontalement)
        dist = np.sqrt(
            ((X - center_x) / (w * 0.6)) ** 2 +
            ((Y - center_y) / (h * 0.7)) ** 2
        )
        
        # Vignette avec falloff doux
        vignette = 1 - (np.clip(dist, 0, 1) ** 2) * strength
        vignette = vignette[:, :, np.newaxis]
        
        result = bg.astype(np.float32) * vignette
        return np.clip(result, 0, 255).astype(np.uint8)
    
    def _add_center_spotlight(self,
                              bg: np.ndarray,
                              config: Dict) -> np.ndarray:
        """
        Ajoute un spot lumineux central subtil (comme Spyne).
        """
        h, w = bg.shape[:2]
        
        # Centre du spot (légèrement au-dessus du centre)
        center_x = w // 2
        center_y = int(h * 0.45)
        
        Y, X = np.ogrid[:h, :w]
        
        # Spot elliptique très doux
        dist = np.sqrt(
            ((X - center_x) / (w * 0.4)) ** 2 +
            ((Y - center_y) / (h * 0.35)) ** 2
        )
        
        # Intensité du spot (très subtile)
        spot = np.exp(-dist ** 2 * 2) * 0.03
        spot = spot[:, :, np.newaxis]
        
        result = bg.astype(np.float32)
        result = result + result * spot
        
        return np.clip(result, 0, 255).astype(np.uint8)
    
    def create_reflection_floor(self,
                                 width: int,
                                 height: int,
                                 preset: str = 'spyne_white',
                                 reflection_intensity: float = 0.15) -> np.ndarray:
        """
        Crée un fond avec zone de reflet au sol marquée.
        """
        bg = self.create_spyne_background(width, height, preset)
        
        h, w = bg.shape[:2]
        horizon_y = int(h * 0.62)
        
        # Zone de reflet (sol légèrement plus clair/brillant au centre)
        result = bg.astype(np.float32)
        
        for y in range(horizon_y, h):
            t = (y - horizon_y) / (h - horizon_y)
            # Zone de reflet qui s'estompe
            reflection_zone = (1 - t) * reflection_intensity
            
            for x in range(w):
                # Plus intense au centre
                x_factor = 1 - abs(x - w/2) / (w/2)
                x_factor = x_factor ** 0.5
                
                factor = 1 + reflection_zone * x_factor
                result[y, x] = np.clip(result[y, x] * factor, 0, 255)
        
        return result.astype(np.uint8)


class ShadowGeneratorV2:
    """
    Générateur d'ombres qualité Spyne.
    """
    
    SHADOW_PRESETS = {
        'contact': {
            'blur': 3,
            'opacity': 0.55,
            'y_scale': 0.008,
            'x_scale': 0.92,
            'y_offset': -2,
            'color': (5, 5, 10),  # Légère teinte bleue
        },
        'ambient': {
            'blur': 25,
            'opacity': 0.28,
            'y_scale': 0.08,
            'x_scale': 1.05,
            'y_offset': 3,
            'color': (8, 8, 15),
        },
        'soft': {
            'blur': 60,
            'opacity': 0.18,
            'y_scale': 0.15,
            'x_scale': 1.2,
            'y_offset': 8,
            'color': (10, 10, 18),
        }
    }
    
    def create_realistic_shadows(self,
                                  mask: np.ndarray,
                                  floor_y: int = None) -> Dict[str, np.ndarray]:
        """
        Crée des ombres réalistes comme Spyne.
        """
        h, w = mask.shape[:2]
        
        # Trouver le bas de la voiture
        coords = np.column_stack(np.where(mask > 0))
        if len(coords) == 0:
            return {'contact': np.zeros((h, w, 4), dtype=np.uint8),
                    'ambient': np.zeros((h, w, 4), dtype=np.uint8),
                    'soft': np.zeros((h, w, 4), dtype=np.uint8)}
        
        y_max = coords[:, 0].max()
        x_min, x_max = coords[:, 1].min(), coords[:, 1].max()
        car_width = x_max - x_min
        car_height = coords[:, 0].max() - coords[:, 0].min()
        
        if floor_y is None:
            floor_y = y_max
        
        shadows = {}
        
        for shadow_type, config in self.SHADOW_PRESETS.items():
            shadow = self._create_single_shadow(
                mask, floor_y, x_min, car_width, car_height, config
            )
            shadows[shadow_type] = shadow
        
        return shadows
    
    def _create_single_shadow(self,
                               mask: np.ndarray,
                               floor_y: int,
                               x_start: int,
                               car_width: int,
                               car_height: int,
                               config: Dict) -> np.ndarray:
        """
        Crée une seule couche d'ombre.
        """
        h, w = mask.shape[:2]
        
        # Dimensions de l'ombre
        shadow_h = max(1, int(car_height * config['y_scale']))
        shadow_w = int(car_width * config['x_scale'])
        
        # Créer l'ombre de base
        shadow_base = np.zeros((shadow_h, shadow_w), dtype=np.float32)
        
        # Remplir avec gradient elliptique
        Y, X = np.ogrid[:shadow_h, :shadow_w]
        center_x = shadow_w / 2
        
        # Forme elliptique avec falloff
        dist_x = ((X - center_x) / (shadow_w / 2)) ** 2
        dist_y = (Y / shadow_h) ** 0.5
        
        shadow_base = np.clip(1 - dist_x - dist_y * 0.3, 0, 1)
        
        # Appliquer le blur
        blur = config['blur']
        if blur > 0:
            kernel = blur * 2 + 1
            shadow_base = cv2.GaussianBlur(shadow_base, (kernel, kernel), 0)
        
        # Positionner sur le canvas
        shadow_full = np.zeros((h, w, 4), dtype=np.float32)
        
        y_pos = floor_y + config['y_offset']
        x_pos = x_start + (car_width - shadow_w) // 2
        
        # Bounds checking
        y1 = max(0, y_pos)
        y2 = min(h, y_pos + shadow_h)
        x1 = max(0, x_pos)
        x2 = min(w, x_pos + shadow_w)
        
        sy1 = max(0, -y_pos)
        sy2 = sy1 + (y2 - y1)
        sx1 = max(0, -x_pos)
        sx2 = sx1 + (x2 - x1)
        
        if y2 > y1 and x2 > x1:
            # RGB (couleur de l'ombre)
            shadow_full[y1:y2, x1:x2, 0] = config['color'][0]
            shadow_full[y1:y2, x1:x2, 1] = config['color'][1]
            shadow_full[y1:y2, x1:x2, 2] = config['color'][2]
            # Alpha (opacité)
            shadow_full[y1:y2, x1:x2, 3] = shadow_base[sy1:sy2, sx1:sx2] * config['opacity'] * 255
        
        return shadow_full.astype(np.uint8)
    
    def composite_shadows_on_background(self,
                                         background: np.ndarray,
                                         shadows: Dict[str, np.ndarray]) -> np.ndarray:
        """
        Compose les ombres sur le fond avec blending réaliste.
        """
        result = background.copy().astype(np.float32)
        
        # Ordre: soft -> ambient -> contact (du plus loin au plus proche)
        for shadow_type in ['soft', 'ambient', 'contact']:
            if shadow_type not in shadows:
                continue
            
            shadow = shadows[shadow_type].astype(np.float32)
            
            # Extraire RGB et alpha
            shadow_rgb = shadow[:, :, :3]
            alpha = shadow[:, :, 3:4] / 255.0
            
            # Blend multiplicatif avec la couleur de l'ombre
            # result = result * (1 - alpha) + shadow_rgb * alpha
            result = result * (1 - alpha * 0.8) + shadow_rgb * alpha * 0.2
        
        return np.clip(result, 0, 255).astype(np.uint8)


def create_spyne_render(car_image: np.ndarray,
                        car_mask: np.ndarray,
                        preset: str = 'spyne_white',
                        output_size: Tuple[int, int] = (1920, 1080)) -> np.ndarray:
    """
    Fonction principale pour créer un rendu qualité Spyne.
    """
    w, h = output_size
    
    # 1. Créer le fond
    bg_gen = BackgroundGeneratorV2()
    background = bg_gen.create_reflection_floor(w, h, preset)
    
    # 2. Redimensionner la voiture
    car_h, car_w = car_image.shape[:2]
    scale = min(w * 0.75 / car_w, h * 0.65 / car_h)
    new_w = int(car_w * scale)
    new_h = int(car_h * scale)
    
    car_resized = cv2.resize(car_image, (new_w, new_h), interpolation=cv2.INTER_LANCZOS4)
    mask_resized = cv2.resize(car_mask, (new_w, new_h), interpolation=cv2.INTER_LANCZOS4)
    
    # 3. Position de la voiture
    car_x = (w - new_w) // 2
    car_y = int(h * 0.62) - new_h + int(new_h * 0.1)
    
    # 4. Générer les ombres
    shadow_gen = ShadowGeneratorV2()
    
    # Créer un masque pleine taille pour les ombres
    full_mask = np.zeros((h, w), dtype=np.uint8)
    y1 = max(0, car_y)
    y2 = min(h, car_y + new_h)
    x1 = max(0, car_x)
    x2 = min(w, car_x + new_w)
    
    my1 = max(0, -car_y)
    my2 = my1 + (y2 - y1)
    mx1 = max(0, -car_x)
    mx2 = mx1 + (x2 - x1)
    
    if y2 > y1 and x2 > x1:
        full_mask[y1:y2, x1:x2] = mask_resized[my1:my2, mx1:mx2]
    
    floor_y = int(h * 0.62)
    shadows = shadow_gen.create_realistic_shadows(full_mask, floor_y)
    
    # 5. Composer les ombres sur le fond
    result = shadow_gen.composite_shadows_on_background(background, shadows)
    
    # 6. Ajouter la voiture
    if y2 > y1 and x2 > x1:
        mask_norm = mask_resized[my1:my2, mx1:mx2].astype(np.float32) / 255.0
        mask_3ch = mask_norm[:, :, np.newaxis]
        
        result[y1:y2, x1:x2] = (
            result[y1:y2, x1:x2].astype(np.float32) * (1 - mask_3ch) +
            car_resized[my1:my2, mx1:mx2].astype(np.float32) * mask_3ch
        ).astype(np.uint8)
    
    return result


if __name__ == "__main__":
    # Test: générer les fonds
    bg_gen = BackgroundGeneratorV2()
    
    for preset in ['spyne_white', 'spyne_grey', 'spyne_dark', 'spyne_showroom']:
        bg = bg_gen.create_spyne_background(1920, 1080, preset)
        cv2.imwrite(f"bg_{preset}.png", cv2.cvtColor(bg, cv2.COLOR_RGB2BGR))
        print(f"✅ {preset} saved")
    
    print("\n🎨 Backgrounds générés !")

