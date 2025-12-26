"""
REFLECTION GENERATOR MODULE - Clone Spyne
==========================================
Generates floor reflection effect identical to Spyne.

Parameters found in Spyne's code:
- reflection
- flip
- alpha
- gradient (for fade out)

Spyne Reflection Technique:
1. Vertical flip of the car
2. Apply opacity (~0.15-0.25)
3. Gradient mask (fade towards bottom)
4. Position directly under the car
"""

import cv2
import numpy as np
from typing import Tuple, Optional


class ReflectionGenerator:
    """
    Generate realistic floor reflections like Spyne.
    """
    
    def __init__(self):
        pass
    
    def create_reflection(self,
                          car_image: np.ndarray,
                          car_mask: np.ndarray,
                          opacity: float = 0.20,
                          fade_height: float = 0.5,
                          blur: int = 2,
                          gap: int = 0) -> Tuple[np.ndarray, np.ndarray]:
        """
        Create mirror reflection of the car for floor effect.
        
        Args:
            car_image: BGR image of the car
            car_mask: Binary mask of the car
            opacity: Reflection opacity (0.0-1.0)
            fade_height: Portion visible before complete fade (0.0-1.0)
            blur: Slight blur for realism
            gap: Pixel gap between car and reflection
        
        Returns:
            (reflection_image, reflection_mask): BGR image and alpha mask
        """
        h, w = car_image.shape[:2]
        
        # Flip vertically
        reflection = cv2.flip(car_image, 0)
        reflection_mask = cv2.flip(car_mask, 0)
        
        # Create fade gradient (strong at top, fades to transparent at bottom)
        gradient = np.zeros((h, w), dtype=np.float32)
        fade_end = int(h * fade_height)
        
        for y in range(fade_end):
            # Smooth fade curve
            t = y / fade_end
            # Use ease-out curve for natural fade
            gradient[y, :] = 1.0 - self._ease_out(t)
        
        # Apply gradient and opacity to mask
        reflection_mask_float = reflection_mask.astype(np.float32) / 255.0
        reflection_mask_float = reflection_mask_float * gradient * opacity
        reflection_mask = (reflection_mask_float * 255).astype(np.uint8)
        
        # Apply slight blur for realism
        if blur > 0:
            reflection = cv2.GaussianBlur(reflection, (blur * 2 + 1, blur * 2 + 1), 0)
            reflection_mask = cv2.GaussianBlur(reflection_mask, (blur * 2 + 1, blur * 2 + 1), 0)
        
        # Slightly desaturate reflection for realism
        reflection = self._desaturate(reflection, amount=0.2)
        
        # Shift down by gap if specified
        if gap > 0:
            M = np.float32([[1, 0, 0], [0, 1, gap]])
            reflection = cv2.warpAffine(reflection, M, (w, h))
            reflection_mask = cv2.warpAffine(reflection_mask, M, (w, h))
        
        return reflection, reflection_mask
    
    def _ease_out(self, t: float) -> float:
        """Ease-out curve for natural fade."""
        return t * t
    
    def _desaturate(self, image: np.ndarray, amount: float = 0.3) -> np.ndarray:
        """Reduce saturation of image."""
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV).astype(np.float32)
        hsv[:, :, 1] = hsv[:, :, 1] * (1 - amount)
        hsv = np.clip(hsv, 0, 255).astype(np.uint8)
        return cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)
    
    def create_reflection_extended(self,
                                    car_image: np.ndarray,
                                    car_mask: np.ndarray,
                                    background_height: int,
                                    car_y_position: int,
                                    opacity: float = 0.18,
                                    max_reflection_height: float = 0.4) -> Tuple[np.ndarray, np.ndarray, int]:
        """
        Create reflection sized for the full background.
        
        Args:
            car_image: Car image
            car_mask: Car mask
            background_height: Full background height
            car_y_position: Y position of car in background
            opacity: Reflection opacity
            max_reflection_height: Maximum reflection height as ratio of car height
        
        Returns:
            (reflection, mask, y_position): Reflection image, mask, and Y position
        """
        car_h, car_w = car_image.shape[:2]
        
        # Find actual car bounds in mask
        coords = np.column_stack(np.where(car_mask > 0))
        if len(coords) == 0:
            return np.zeros_like(car_image), np.zeros((car_h, car_w), dtype=np.uint8), 0
        
        y_min, y_max = coords[:, 0].min(), coords[:, 0].max()
        actual_height = y_max - y_min
        
        # Calculate reflection height
        reflection_height = int(actual_height * max_reflection_height)
        
        # Create reflection from bottom portion of car
        bottom_portion = car_image[y_max - reflection_height:y_max, :]
        bottom_mask = car_mask[y_max - reflection_height:y_max, :]
        
        if bottom_portion.size == 0:
            return np.zeros_like(car_image), np.zeros((car_h, car_w), dtype=np.uint8), 0
        
        # Flip
        reflection = cv2.flip(bottom_portion, 0)
        reflection_mask = cv2.flip(bottom_mask, 0)
        
        # Create fade gradient
        ref_h = reflection.shape[0]
        gradient = np.zeros((ref_h, car_w), dtype=np.float32)
        for y in range(ref_h):
            t = y / ref_h
            gradient[y, :] = 1.0 - (t ** 0.8)  # Power curve for fade
        
        # Apply gradient and opacity
        reflection_mask = (reflection_mask.astype(np.float32) / 255.0 * gradient * opacity * 255).astype(np.uint8)
        
        # Slight blur
        reflection = cv2.GaussianBlur(reflection, (3, 3), 0)
        
        # Desaturate
        reflection = self._desaturate(reflection, 0.25)
        
        # Calculate Y position (just under the car)
        reflection_y = car_y_position + car_h
        
        return reflection, reflection_mask, reflection_y
    
    def add_reflection_to_composite(self,
                                     background: np.ndarray,
                                     reflection: np.ndarray,
                                     reflection_mask: np.ndarray,
                                     x: int,
                                     y: int) -> np.ndarray:
        """
        Add reflection to background at specified position.
        
        Args:
            background: Background image
            reflection: Reflection image
            reflection_mask: Reflection alpha mask
            x: X position
            y: Y position
        
        Returns:
            result: Background with reflection added
        """
        result = background.copy().astype(np.float32)
        
        bg_h, bg_w = background.shape[:2]
        ref_h, ref_w = reflection.shape[:2]
        
        # Calculate bounds
        y1, y2 = max(0, y), min(bg_h, y + ref_h)
        x1, x2 = max(0, x), min(bg_w, x + ref_w)
        
        ry1, ry2 = max(0, -y), min(ref_h, bg_h - y)
        rx1, rx2 = max(0, -x), min(ref_w, bg_w - x)
        
        if y2 <= y1 or x2 <= x1:
            return background
        
        # Get regions
        bg_region = result[y1:y2, x1:x2]
        ref_region = reflection[ry1:ry2, rx1:rx2].astype(np.float32)
        mask_region = reflection_mask[ry1:ry2, rx1:rx2].astype(np.float32) / 255.0
        
        if len(mask_region.shape) == 2:
            mask_region = mask_region[:, :, np.newaxis]
        
        # Blend
        result[y1:y2, x1:x2] = bg_region * (1 - mask_region) + ref_region * mask_region
        
        return np.clip(result, 0, 255).astype(np.uint8)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python reflection.py <image_path> <mask_path>")
        sys.exit(1)
    
    image = cv2.imread(sys.argv[1])
    mask = cv2.imread(sys.argv[2], cv2.IMREAD_GRAYSCALE)
    
    generator = ReflectionGenerator()
    reflection, reflection_mask = generator.create_reflection(image, mask)
    
    cv2.imwrite("reflection_image.png", reflection)
    cv2.imwrite("reflection_mask.png", reflection_mask)
    print("✅ Reflection saved")

