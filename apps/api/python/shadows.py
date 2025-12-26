"""
SHADOW GENERATOR MODULE - Clone Spyne
======================================
Generates realistic 3-layer shadows identical to Spyne.

Parameters found in Spyne's code:
- shadow (50+ occurrences)
- radius (blur)
- opacity
- alpha
- ambient
- composite
- blend

Spyne Shadow Structure (3 layers):
1. Contact Shadow: Very sharp, small, directly under wheels (opacity ~0.4-0.5)
2. Ambient Shadow: Blurred, large, under entire car (opacity ~0.2-0.3)
3. Drop Shadow: Very blurred, very large, soft falloff (opacity ~0.1-0.2)
"""

import cv2
import numpy as np
from typing import Dict, Tuple, Optional


class ShadowGenerator:
    """
    Generate realistic multi-layer shadows like Spyne.
    """
    
    # Shadow configurations (reverse-engineered from Spyne)
    SHADOW_CONFIG = {
        'contact': {
            'blur_radius': 5,
            'opacity': 0.45,
            'offset_y': 0,
            'scale_y': 0.015,      # Very thin (contact line)
            'scale_x': 0.95,       # Slightly narrower than car
            'color': (0, 0, 0),
            'gradient': False
        },
        'ambient': {
            'blur_radius': 35,
            'opacity': 0.25,
            'offset_y': 5,
            'scale_y': 0.12,       # Medium height
            'scale_x': 1.1,        # Slightly wider
            'color': (0, 0, 0),
            'gradient': True
        },
        'drop': {
            'blur_radius': 80,
            'opacity': 0.15,
            'offset_y': 15,
            'scale_y': 0.20,       # Tall shadow
            'scale_x': 1.3,        # Much wider
            'color': (0, 0, 0),
            'gradient': True
        }
    }
    
    def __init__(self):
        pass
    
    def create_shadow_layer(self,
                            mask: np.ndarray,
                            shadow_type: str = 'ambient',
                            custom_config: Dict = None) -> np.ndarray:
        """
        Create a single shadow layer from the car mask.
        
        Args:
            mask: Binary mask of the car
            shadow_type: 'contact', 'ambient', or 'drop'
            custom_config: Optional custom shadow configuration
        
        Returns:
            shadow: Grayscale shadow layer (0-255)
        """
        config = custom_config or self.SHADOW_CONFIG.get(
            shadow_type, 
            self.SHADOW_CONFIG['ambient']
        )
        
        h, w = mask.shape[:2]
        
        # Find bounding box of the car
        coords = np.column_stack(np.where(mask > 0))
        if len(coords) == 0:
            return np.zeros((h, w), dtype=np.uint8)
        
        y_min, x_min = coords.min(axis=0)
        y_max, x_max = coords.max(axis=0)
        car_height = y_max - y_min
        car_width = x_max - x_min
        
        # Calculate shadow dimensions
        shadow_height = int(car_height * config['scale_y'])
        shadow_width = int(car_width * config['scale_x'])
        
        # Extract bottom portion of mask for shadow base
        bottom_strip = mask[y_max - shadow_height:y_max, x_min:x_max]
        if bottom_strip.size == 0:
            bottom_strip = mask[max(0, y_max - 20):y_max, x_min:x_max]
        
        # Resize to shadow dimensions
        if shadow_height > 0 and shadow_width > 0:
            shadow = cv2.resize(bottom_strip, (shadow_width, shadow_height))
        else:
            shadow = np.zeros((max(1, shadow_height), max(1, shadow_width)), dtype=np.uint8)
        
        # Apply vertical compression (flatten for ground shadow)
        if config['scale_y'] < 1.0:
            shadow = cv2.resize(shadow, (shadow_width, max(1, shadow_height)))
        
        # Apply gradient (fade out at edges) for soft shadows
        if config.get('gradient', False):
            shadow = self._apply_shadow_gradient(shadow)
        
        # Apply blur
        blur = config['blur_radius']
        if blur > 0:
            kernel_size = blur * 2 + 1
            shadow = cv2.GaussianBlur(shadow, (kernel_size, kernel_size), 0)
        
        # Create full-size shadow canvas
        shadow_full = np.zeros((h, w), dtype=np.float32)
        
        # Position shadow under the car
        offset_y = config['offset_y']
        shadow_y = y_max + offset_y
        shadow_x = x_min + (car_width - shadow_width) // 2
        
        # Ensure bounds
        sy1 = max(0, shadow_y)
        sy2 = min(h, shadow_y + shadow.shape[0])
        sx1 = max(0, shadow_x)
        sx2 = min(w, shadow_x + shadow.shape[1])
        
        # Source bounds
        oy1 = max(0, -shadow_y)
        oy2 = oy1 + (sy2 - sy1)
        ox1 = max(0, -shadow_x)
        ox2 = ox1 + (sx2 - sx1)
        
        if sy2 > sy1 and sx2 > sx1 and oy2 <= shadow.shape[0] and ox2 <= shadow.shape[1]:
            shadow_full[sy1:sy2, sx1:sx2] = shadow[oy1:oy2, ox1:ox2]
        
        # Apply opacity
        opacity = config['opacity']
        shadow_full = shadow_full * opacity
        
        return shadow_full.astype(np.uint8)
    
    def _apply_shadow_gradient(self, shadow: np.ndarray) -> np.ndarray:
        """Apply fade-out gradient to shadow edges."""
        h, w = shadow.shape[:2]
        
        # Create horizontal gradient (fade at sides)
        x_grad = np.zeros((h, w), dtype=np.float32)
        center_x = w / 2
        for x in range(w):
            dist = abs(x - center_x) / center_x
            x_grad[:, x] = 1 - (dist ** 1.5) * 0.5
        
        # Create vertical gradient (fade towards bottom)
        y_grad = np.zeros((h, w), dtype=np.float32)
        for y in range(h):
            y_grad[y, :] = 1 - (y / h) * 0.7
        
        # Combine gradients
        gradient = x_grad * y_grad
        
        result = shadow.astype(np.float32) * gradient
        return result.astype(np.uint8)
    
    def create_all_shadows(self, mask: np.ndarray) -> Dict[str, np.ndarray]:
        """
        Create all 3 shadow layers (like Spyne).
        
        Args:
            mask: Binary mask of the car
        
        Returns:
            dict: {'contact': ..., 'ambient': ..., 'drop': ...}
        """
        return {
            'contact': self.create_shadow_layer(mask, 'contact'),
            'ambient': self.create_shadow_layer(mask, 'ambient'),
            'drop': self.create_shadow_layer(mask, 'drop')
        }
    
    def composite_shadows(self,
                          background: np.ndarray,
                          shadows: Dict[str, np.ndarray],
                          blend_mode: str = 'multiply') -> np.ndarray:
        """
        Composite shadows onto background.
        
        Order (bottom to top):
        1. Background
        2. Drop shadow
        3. Ambient shadow
        4. Contact shadow
        
        Args:
            background: Background image (RGB)
            shadows: Dict of shadow layers
            blend_mode: 'multiply' or 'overlay'
        
        Returns:
            result: Background with shadows
        """
        result = background.copy().astype(np.float32)
        
        # Apply shadows in order (furthest to closest)
        for shadow_type in ['drop', 'ambient', 'contact']:
            if shadow_type not in shadows:
                continue
            
            shadow = shadows[shadow_type].astype(np.float32) / 255.0
            
            if blend_mode == 'multiply':
                # Multiply blend: darken where shadow is dark
                for c in range(3):
                    result[:, :, c] = result[:, :, c] * (1 - shadow)
            else:
                # Overlay blend
                for c in range(3):
                    result[:, :, c] = result[:, :, c] - (shadow * 100)
        
        return np.clip(result, 0, 255).astype(np.uint8)
    
    def create_directional_shadow(self,
                                   mask: np.ndarray,
                                   angle: float = 45,
                                   length: float = 0.3,
                                   blur: int = 40,
                                   opacity: float = 0.2) -> np.ndarray:
        """
        Create directional shadow (simulating sun position).
        
        Args:
            mask: Car mask
            angle: Shadow direction in degrees (0 = right)
            length: Shadow length relative to car height
            blur: Blur radius
            opacity: Shadow opacity
        
        Returns:
            shadow: Directional shadow layer
        """
        h, w = mask.shape[:2]
        
        # Calculate offset from angle
        import math
        rad = math.radians(angle)
        coords = np.column_stack(np.where(mask > 0))
        if len(coords) == 0:
            return np.zeros((h, w), dtype=np.uint8)
        
        car_height = coords[:, 0].max() - coords[:, 0].min()
        offset_x = int(math.cos(rad) * car_height * length)
        offset_y = int(math.sin(rad) * car_height * length)
        
        # Create translation matrix
        M = np.float32([[1, 0, offset_x], [0, 1, offset_y]])
        
        # Translate mask
        shadow = cv2.warpAffine(mask, M, (w, h))
        
        # Blur
        if blur > 0:
            shadow = cv2.GaussianBlur(shadow, (blur * 2 + 1, blur * 2 + 1), 0)
        
        # Apply opacity
        shadow = (shadow.astype(np.float32) * opacity).astype(np.uint8)
        
        return shadow


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python shadows.py <mask_path>")
        sys.exit(1)
    
    mask = cv2.imread(sys.argv[1], cv2.IMREAD_GRAYSCALE)
    if mask is None:
        print(f"Error: Could not load mask {sys.argv[1]}")
        sys.exit(1)
    
    generator = ShadowGenerator()
    shadows = generator.create_all_shadows(mask)
    
    # Save each shadow layer
    for name, shadow in shadows.items():
        output_path = f"shadow_{name}.png"
        cv2.imwrite(output_path, shadow)
        print(f"✅ {name} shadow saved to: {output_path}")

