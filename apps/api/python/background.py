"""
BACKGROUND GENERATOR MODULE - Clone Spyne
==========================================
Generates professional studio backgrounds (like Spyne showroom backgrounds).

Parameters found in Spyne's code:
- background (300+ occurrences)
- gradient (100+ occurrences)
- floor (20+ occurrences)
- ground (50+ occurrences)
- studio_type
- background_type
- background_color

Spyne Background Structure:
- Top: Light (#F5F5F5 - #FAFAFA)
- Horizon: ~65% from top
- Bottom (floor): Darker (#D0D0D0 - #E0E0E0)
- Smooth gradient between areas
"""

import cv2
import numpy as np
from typing import Tuple, Dict, Optional


class BackgroundGenerator:
    """
    Generate professional studio backgrounds identical to Spyne.
    """
    
    # Background presets (reverse-engineered from Spyne)
    PRESETS = {
        'studio_white': {
            'top_color': (250, 250, 250),      # Almost white
            'horizon_color': (240, 240, 240),  # Light gray
            'floor_color': (215, 215, 215),    # Floor gray
            'horizon_position': 0.65,          # 65% from top
            'floor_gradient': 0.3,             # Floor gradient intensity
        },
        'studio_grey': {
            'top_color': (235, 235, 235),
            'horizon_color': (210, 210, 210),
            'floor_color': (175, 175, 175),
            'horizon_position': 0.65,
            'floor_gradient': 0.35,
        },
        'studio_dark': {
            'top_color': (90, 90, 90),
            'horizon_color': (60, 60, 60),
            'floor_color': (35, 35, 35),
            'horizon_position': 0.65,
            'floor_gradient': 0.4,
        },
        'showroom': {
            'top_color': (248, 248, 250),
            'horizon_color': (230, 230, 235),
            'floor_color': (195, 195, 200),
            'horizon_position': 0.60,
            'floor_gradient': 0.35,
        },
        'outdoor_neutral': {
            'top_color': (200, 210, 220),      # Sky-like
            'horizon_color': (180, 185, 190),
            'floor_color': (160, 165, 170),
            'horizon_position': 0.55,
            'floor_gradient': 0.25,
        },
        'dealership': {
            'top_color': (245, 245, 247),
            'horizon_color': (225, 225, 230),
            'floor_color': (185, 185, 195),
            'horizon_position': 0.62,
            'floor_gradient': 0.4,
        }
    }
    
    def __init__(self):
        pass
    
    def create_studio_background(self,
                                  width: int,
                                  height: int,
                                  preset: str = 'studio_white',
                                  custom_config: Dict = None) -> np.ndarray:
        """
        Create a professional studio background with gradient.
        
        Args:
            width: Image width in pixels
            height: Image height in pixels
            preset: Preset name ('studio_white', 'showroom', etc.)
            custom_config: Optional custom configuration dict
        
        Returns:
            background: RGB numpy array
        """
        # Get configuration
        if custom_config:
            config = custom_config
        else:
            config = self.PRESETS.get(preset, self.PRESETS['studio_white'])
        
        top_color = np.array(config['top_color'], dtype=np.float32)
        horizon_color = np.array(config['horizon_color'], dtype=np.float32)
        floor_color = np.array(config['floor_color'], dtype=np.float32)
        horizon_pos = config['horizon_position']
        floor_grad = config.get('floor_gradient', 0.3)
        
        # Calculate horizon position
        horizon_y = int(height * horizon_pos)
        
        # Create background array
        background = np.zeros((height, width, 3), dtype=np.uint8)
        
        # Generate wall gradient (top to horizon)
        for y in range(horizon_y):
            # Smooth easing for natural gradient
            t = y / horizon_y
            t = self._ease_in_out(t)
            
            color = top_color + (horizon_color - top_color) * t
            background[y, :] = color.astype(np.uint8)
        
        # Generate floor gradient (horizon to bottom)
        for y in range(horizon_y, height):
            t = (y - horizon_y) / (height - horizon_y)
            t = self._ease_in_out(t * floor_grad + (1 - floor_grad))
            
            color = horizon_color + (floor_color - horizon_color) * t
            background[y, :] = color.astype(np.uint8)
        
        return background
    
    def _ease_in_out(self, t: float) -> float:
        """Smooth easing function for natural gradients."""
        return t * t * (3 - 2 * t)
    
    def add_vignette(self,
                     image: np.ndarray,
                     strength: float = 0.3,
                     radius: float = 1.2) -> np.ndarray:
        """
        Add subtle vignette effect (darker edges).
        
        Args:
            image: Input image
            strength: Vignette intensity (0.0-1.0)
            radius: Vignette radius (1.0 = image corners)
        
        Returns:
            image: Image with vignette
        """
        h, w = image.shape[:2]
        
        # Create coordinate grids
        Y, X = np.ogrid[:h, :w]
        center_y, center_x = h / 2, w / 2
        
        # Calculate distance from center
        dist = np.sqrt(
            ((X - center_x) / center_x) ** 2 + 
            ((Y - center_y) / center_y) ** 2
        )
        
        # Normalize and apply vignette
        vignette = 1 - (np.clip(dist / radius, 0, 1) ** 2) * strength
        vignette = np.dstack([vignette] * 3)
        
        result = (image.astype(np.float32) * vignette).astype(np.uint8)
        return result
    
    def add_ambient_lighting(self,
                              image: np.ndarray,
                              light_position: str = 'top',
                              intensity: float = 0.1) -> np.ndarray:
        """
        Add subtle ambient lighting effect.
        
        Args:
            image: Input image
            light_position: 'top', 'top_left', 'top_right'
            intensity: Light intensity (0.0-0.5)
        
        Returns:
            image: Image with ambient lighting
        """
        h, w = image.shape[:2]
        
        # Create light gradient based on position
        Y, X = np.ogrid[:h, :w]
        
        if light_position == 'top':
            light = 1 - (Y / h)
        elif light_position == 'top_left':
            dist = np.sqrt((X / w) ** 2 + (Y / h) ** 2)
            light = 1 - dist
        elif light_position == 'top_right':
            dist = np.sqrt(((w - X) / w) ** 2 + (Y / h) ** 2)
            light = 1 - dist
        else:
            light = np.ones((h, w))
        
        # Apply subtle brightening
        light = 1 + (light * intensity)
        light = np.dstack([light] * 3)
        
        result = np.clip(image.astype(np.float32) * light, 0, 255).astype(np.uint8)
        return result
    
    def add_floor_reflection_area(self,
                                   background: np.ndarray,
                                   reflection_opacity: float = 0.05) -> np.ndarray:
        """
        Add subtle floor reflection zone.
        
        Args:
            background: Background image
            reflection_opacity: Opacity of reflection zone
        
        Returns:
            background: Background with reflection zone
        """
        h, w = background.shape[:2]
        horizon_y = int(h * 0.65)
        
        # Create gradient for reflection zone
        result = background.copy().astype(np.float32)
        
        for y in range(horizon_y, h):
            t = (y - horizon_y) / (h - horizon_y)
            # Slight brightening for reflection effect
            factor = 1 + (1 - t) * reflection_opacity
            result[y, :] = np.clip(result[y, :] * factor, 0, 255)
        
        return result.astype(np.uint8)
    
    def create_custom_background(self,
                                  width: int,
                                  height: int,
                                  top_color: Tuple[int, int, int],
                                  floor_color: Tuple[int, int, int],
                                  horizon_position: float = 0.65) -> np.ndarray:
        """
        Create background with custom colors.
        
        Args:
            width: Image width
            height: Image height
            top_color: RGB tuple for top
            floor_color: RGB tuple for floor
            horizon_position: Position of horizon (0.0-1.0)
        
        Returns:
            background: Custom background
        """
        # Calculate middle color
        top = np.array(top_color, dtype=np.float32)
        floor = np.array(floor_color, dtype=np.float32)
        horizon = (top + floor) / 2
        
        config = {
            'top_color': top_color,
            'horizon_color': tuple(horizon.astype(int)),
            'floor_color': floor_color,
            'horizon_position': horizon_position,
            'floor_gradient': 0.3
        }
        
        return self.create_studio_background(width, height, custom_config=config)
    
    def create_complete_background(self,
                                    width: int,
                                    height: int,
                                    preset: str = 'studio_white',
                                    vignette: bool = True,
                                    vignette_strength: float = 0.15,
                                    ambient_light: bool = True,
                                    reflection_zone: bool = True) -> np.ndarray:
        """
        Create complete professional background with all effects.
        
        Args:
            width: Image width
            height: Image height
            preset: Background preset
            vignette: Add vignette effect
            vignette_strength: Vignette intensity
            ambient_light: Add ambient lighting
            reflection_zone: Add floor reflection zone
        
        Returns:
            background: Complete background
        """
        # Create base background
        bg = self.create_studio_background(width, height, preset)
        
        # Add reflection zone
        if reflection_zone:
            bg = self.add_floor_reflection_area(bg, reflection_opacity=0.03)
        
        # Add ambient lighting
        if ambient_light:
            bg = self.add_ambient_lighting(bg, 'top', intensity=0.05)
        
        # Add vignette
        if vignette:
            bg = self.add_vignette(bg, strength=vignette_strength)
        
        return bg


if __name__ == "__main__":
    import sys
    
    width = int(sys.argv[1]) if len(sys.argv) > 1 else 1920
    height = int(sys.argv[2]) if len(sys.argv) > 2 else 1080
    preset = sys.argv[3] if len(sys.argv) > 3 else 'studio_white'
    
    generator = BackgroundGenerator()
    bg = generator.create_complete_background(width, height, preset)
    
    # Convert RGB to BGR for OpenCV
    bg_bgr = cv2.cvtColor(bg, cv2.COLOR_RGB2BGR)
    
    output_path = f"background_{preset}_{width}x{height}.png"
    cv2.imwrite(output_path, bg_bgr)
    print(f"✅ Background saved to: {output_path}")

