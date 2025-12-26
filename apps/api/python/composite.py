"""
COMPOSITE MODULE - Clone Spyne
==============================
Final image composition - assembles all layers.

Parameters found in Spyne's code:
- composite (100+ occurrences)
- blend
- overlay
- alpha

Spyne Layer Order (bottom to top):
1. Background (studio floor/wall)
2. Reflection (mirror effect)
3. Drop shadow (furthest, most blurred)
4. Ambient shadow (medium)
5. Contact shadow (sharpest, closest)
6. Car (the vehicle itself)
"""

import cv2
import numpy as np
from typing import Dict, Tuple, Optional


class Compositor:
    """
    Composite all layers into final professional image.
    Replicates Spyne's layer composition exactly.
    """
    
    def __init__(self):
        pass
    
    def composite_final(self,
                        background: np.ndarray,
                        car_image: np.ndarray,
                        car_mask: np.ndarray,
                        shadows: Dict[str, np.ndarray],
                        reflection: np.ndarray = None,
                        reflection_mask: np.ndarray = None,
                        car_position: Tuple[int, int] = None,
                        output_size: Tuple[int, int] = None) -> np.ndarray:
        """
        Assemble all elements into final composite image.
        
        Layer order (bottom to top):
        1. Background
        2. Reflection
        3. Drop shadow
        4. Ambient shadow
        5. Contact shadow
        6. Car
        
        Args:
            background: Studio background (RGB)
            car_image: Car image (BGR)
            car_mask: Binary mask of car
            shadows: Dict with 'contact', 'ambient', 'drop' shadow layers
            reflection: Reflection image (optional)
            reflection_mask: Reflection alpha mask (optional)
            car_position: (x, y) position, or None for auto-center
            output_size: (width, height) for final output
        
        Returns:
            final_image: Composited result (RGB)
        """
        # Use background dimensions if no output size specified
        if output_size:
            out_w, out_h = output_size
            background = cv2.resize(background, (out_w, out_h))
        else:
            out_h, out_w = background.shape[:2]
        
        # Start with background
        result = background.copy().astype(np.float32)
        
        # Calculate car dimensions
        car_h, car_w = car_image.shape[:2]
        
        # Calculate car position (centered on horizon by default)
        if car_position is None:
            horizon_y = int(out_h * 0.65)
            x = (out_w - car_w) // 2
            y = horizon_y - car_h + int(car_h * 0.1)  # Sit on horizon
        else:
            x, y = car_position
        
        # 1. Add reflection (if provided)
        if reflection is not None and reflection_mask is not None:
            ref_y = y + car_h  # Position just under car
            self._blend_layer(result, reflection, reflection_mask, x, ref_y)
        
        # 2. Add shadows (order: drop → ambient → contact)
        for shadow_type in ['drop', 'ambient', 'contact']:
            if shadow_type not in shadows:
                continue
            
            shadow = shadows[shadow_type]
            if shadow is None or shadow.size == 0:
                continue
            
            # Create black RGB for shadow
            shadow_rgb = np.zeros((*shadow.shape, 3), dtype=np.uint8)
            
            # Position shadow at same location as car
            # (shadows are already positioned relative to mask)
            self._blend_shadow(result, shadow, x=0, y=0)
        
        # 3. Add the car (top layer)
        self._blend_layer(result, car_image, car_mask, x, y)
        
        return np.clip(result, 0, 255).astype(np.uint8)
    
    def _blend_layer(self,
                     base: np.ndarray,
                     layer: np.ndarray,
                     mask: np.ndarray,
                     x: int,
                     y: int):
        """
        Blend a layer onto the base using alpha mask.
        
        Args:
            base: Base image (modified in place)
            layer: Layer to blend
            mask: Alpha mask (0-255)
            x, y: Position of layer
        """
        bh, bw = base.shape[:2]
        lh, lw = layer.shape[:2]
        
        # Calculate overlap regions
        x1, y1 = max(0, x), max(0, y)
        x2, y2 = min(bw, x + lw), min(bh, y + lh)
        
        lx1, ly1 = max(0, -x), max(0, -y)
        lx2, ly2 = lx1 + (x2 - x1), ly1 + (y2 - y1)
        
        if x2 <= x1 or y2 <= y1:
            return
        
        # Get regions
        base_region = base[y1:y2, x1:x2]
        layer_region = layer[ly1:ly2, lx1:lx2].astype(np.float32)
        mask_region = mask[ly1:ly2, lx1:lx2].astype(np.float32) / 255.0
        
        # Expand mask to 3 channels if needed
        if len(mask_region.shape) == 2:
            mask_region = mask_region[:, :, np.newaxis]
        
        # Convert BGR to RGB if needed
        if layer_region.shape[2] == 3:
            layer_region = cv2.cvtColor(layer_region.astype(np.uint8), cv2.COLOR_BGR2RGB).astype(np.float32)
        
        # Alpha blend
        base[y1:y2, x1:x2] = (
            base_region * (1 - mask_region) +
            layer_region * mask_region
        )
    
    def _blend_shadow(self,
                      base: np.ndarray,
                      shadow: np.ndarray,
                      x: int,
                      y: int):
        """
        Blend shadow using multiply mode.
        
        Args:
            base: Base image (modified in place)
            shadow: Shadow intensity map (0-255)
            x, y: Position offset
        """
        bh, bw = base.shape[:2]
        sh, sw = shadow.shape[:2]
        
        # Resize shadow if needed
        if sh != bh or sw != bw:
            shadow = cv2.resize(shadow, (bw, bh))
        
        # Normalize shadow
        shadow_norm = shadow.astype(np.float32) / 255.0
        
        # Apply multiply blend (darkens based on shadow intensity)
        for c in range(3):
            base[:, :, c] = base[:, :, c] * (1 - shadow_norm)
    
    def auto_position_car(self,
                          background_size: Tuple[int, int],
                          car_size: Tuple[int, int],
                          horizon_ratio: float = 0.65) -> Tuple[int, int]:
        """
        Calculate optimal car position in background.
        
        Args:
            background_size: (width, height)
            car_size: (width, height)
            horizon_ratio: Position of horizon (0.0-1.0 from top)
        
        Returns:
            (x, y): Position tuple
        """
        bg_w, bg_h = background_size
        car_w, car_h = car_size
        
        # Center horizontally
        x = (bg_w - car_w) // 2
        
        # Position so car "sits" on horizon
        horizon_y = int(bg_h * horizon_ratio)
        y = horizon_y - car_h + int(car_h * 0.05)
        
        return (x, y)
    
    def scale_car_to_fit(self,
                         car_image: np.ndarray,
                         car_mask: np.ndarray,
                         target_width: int,
                         target_height: int,
                         max_width_ratio: float = 0.75,
                         max_height_ratio: float = 0.50) -> Tuple[np.ndarray, np.ndarray]:
        """
        Scale car to fit within target dimensions.
        
        Args:
            car_image: Car image
            car_mask: Car mask
            target_width: Target canvas width
            target_height: Target canvas height
            max_width_ratio: Max car width as ratio of canvas
            max_height_ratio: Max car height as ratio of canvas
        
        Returns:
            (scaled_image, scaled_mask)
        """
        car_h, car_w = car_image.shape[:2]
        
        max_w = int(target_width * max_width_ratio)
        max_h = int(target_height * max_height_ratio)
        
        # Calculate scale factor
        scale = min(max_w / car_w, max_h / car_h)
        
        if scale < 1.0:
            new_w = int(car_w * scale)
            new_h = int(car_h * scale)
            
            car_image = cv2.resize(car_image, (new_w, new_h), interpolation=cv2.INTER_AREA)
            car_mask = cv2.resize(car_mask, (new_w, new_h), interpolation=cv2.INTER_AREA)
        
        return car_image, car_mask
    
    def create_final_composite(self,
                                background: np.ndarray,
                                car_image: np.ndarray,
                                car_mask: np.ndarray,
                                shadows: Dict[str, np.ndarray],
                                reflection: np.ndarray = None,
                                reflection_mask: np.ndarray = None,
                                auto_position: bool = True,
                                auto_scale: bool = True) -> np.ndarray:
        """
        Complete pipeline for creating final composite.
        
        Args:
            background: Background image
            car_image: Car image
            car_mask: Car mask
            shadows: Shadow layers
            reflection: Optional reflection
            reflection_mask: Optional reflection mask
            auto_position: Auto-calculate car position
            auto_scale: Auto-scale car to fit
        
        Returns:
            final: Complete composited image
        """
        bg_h, bg_w = background.shape[:2]
        
        # Scale car if needed
        if auto_scale:
            car_image, car_mask = self.scale_car_to_fit(
                car_image, car_mask, bg_w, bg_h
            )
        
        # Calculate position
        car_position = None
        if auto_position:
            car_h, car_w = car_image.shape[:2]
            car_position = self.auto_position_car((bg_w, bg_h), (car_w, car_h))
        
        # Create composite
        return self.composite_final(
            background=background,
            car_image=car_image,
            car_mask=car_mask,
            shadows=shadows,
            reflection=reflection,
            reflection_mask=reflection_mask,
            car_position=car_position
        )


if __name__ == "__main__":
    print("Compositor module - use via process_image.py")

