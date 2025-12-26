"""
POST-PROCESSING MODULE - Clone Spyne
====================================
Final image enhancements like Spyne applies.

Parameters found in Spyne's code:
- brightness
- contrast
- saturation
- enhance
- quality
"""

import cv2
import numpy as np
from typing import Tuple, Optional

try:
    from PIL import Image, ImageEnhance
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


class PostProcessor:
    """
    Apply final image enhancements to match Spyne quality.
    """
    
    # Default enhancement values (tuned to match Spyne output)
    DEFAULT_BRIGHTNESS = 1.0
    DEFAULT_CONTRAST = 1.05
    DEFAULT_SATURATION = 1.10
    DEFAULT_SHARPNESS = 1.10
    
    def __init__(self):
        pass
    
    def enhance_image(self,
                      image: np.ndarray,
                      brightness: float = None,
                      contrast: float = None,
                      saturation: float = None,
                      sharpness: float = None) -> np.ndarray:
        """
        Apply image enhancements (like Spyne's post-processing).
        
        Args:
            image: BGR numpy array
            brightness: Brightness factor (1.0 = no change)
            contrast: Contrast factor (1.0 = no change)
            saturation: Saturation factor (1.0 = no change)
            sharpness: Sharpness factor (1.0 = no change)
        
        Returns:
            enhanced: Enhanced image
        """
        # Use defaults if not specified
        brightness = brightness or self.DEFAULT_BRIGHTNESS
        contrast = contrast or self.DEFAULT_CONTRAST
        saturation = saturation or self.DEFAULT_SATURATION
        sharpness = sharpness or self.DEFAULT_SHARPNESS
        
        if PIL_AVAILABLE:
            return self._enhance_pil(image, brightness, contrast, saturation, sharpness)
        else:
            return self._enhance_cv2(image, brightness, contrast, saturation, sharpness)
    
    def _enhance_pil(self,
                     image: np.ndarray,
                     brightness: float,
                     contrast: float,
                     saturation: float,
                     sharpness: float) -> np.ndarray:
        """Enhance using PIL (better quality)."""
        # Convert BGR to RGB for PIL
        rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        pil_image = Image.fromarray(rgb)
        
        # Brightness
        if brightness != 1.0:
            enhancer = ImageEnhance.Brightness(pil_image)
            pil_image = enhancer.enhance(brightness)
        
        # Contrast
        if contrast != 1.0:
            enhancer = ImageEnhance.Contrast(pil_image)
            pil_image = enhancer.enhance(contrast)
        
        # Saturation (Color)
        if saturation != 1.0:
            enhancer = ImageEnhance.Color(pil_image)
            pil_image = enhancer.enhance(saturation)
        
        # Sharpness
        if sharpness != 1.0:
            enhancer = ImageEnhance.Sharpness(pil_image)
            pil_image = enhancer.enhance(sharpness)
        
        # Convert back to BGR
        result = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
        return result
    
    def _enhance_cv2(self,
                     image: np.ndarray,
                     brightness: float,
                     contrast: float,
                     saturation: float,
                     sharpness: float) -> np.ndarray:
        """Enhance using OpenCV (fallback)."""
        result = image.astype(np.float32)
        
        # Brightness (additive)
        if brightness != 1.0:
            result = result + (brightness - 1.0) * 50
        
        # Contrast (multiplicative from mean)
        if contrast != 1.0:
            mean = np.mean(result)
            result = mean + (result - mean) * contrast
        
        # Saturation
        if saturation != 1.0:
            hsv = cv2.cvtColor(np.clip(result, 0, 255).astype(np.uint8), cv2.COLOR_BGR2HSV)
            hsv = hsv.astype(np.float32)
            hsv[:, :, 1] = hsv[:, :, 1] * saturation
            hsv = np.clip(hsv, 0, 255).astype(np.uint8)
            result = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR).astype(np.float32)
        
        # Sharpness (unsharp mask)
        if sharpness != 1.0:
            blurred = cv2.GaussianBlur(result, (0, 0), 3)
            result = cv2.addWeighted(result, 1 + sharpness - 1.0, blurred, -(sharpness - 1.0), 0)
        
        return np.clip(result, 0, 255).astype(np.uint8)
    
    def auto_levels(self, image: np.ndarray) -> np.ndarray:
        """
        Auto-adjust levels (histogram stretching).
        
        Args:
            image: Input image
        
        Returns:
            image: Levels-adjusted image
        """
        result = image.copy()
        
        for c in range(3):
            channel = result[:, :, c]
            min_val = np.percentile(channel, 1)
            max_val = np.percentile(channel, 99)
            
            if max_val > min_val:
                result[:, :, c] = np.clip(
                    (channel - min_val) * 255.0 / (max_val - min_val),
                    0, 255
                ).astype(np.uint8)
        
        return result
    
    def white_balance(self, image: np.ndarray) -> np.ndarray:
        """
        Apply automatic white balance.
        
        Args:
            image: Input BGR image
        
        Returns:
            image: White-balanced image
        """
        result = image.astype(np.float32)
        
        # Calculate average color
        avg_b = np.mean(result[:, :, 0])
        avg_g = np.mean(result[:, :, 1])
        avg_r = np.mean(result[:, :, 2])
        
        # Calculate gray point
        gray = (avg_b + avg_g + avg_r) / 3
        
        # Scale each channel
        result[:, :, 0] = result[:, :, 0] * (gray / avg_b)
        result[:, :, 1] = result[:, :, 1] * (gray / avg_g)
        result[:, :, 2] = result[:, :, 2] * (gray / avg_r)
        
        return np.clip(result, 0, 255).astype(np.uint8)
    
    def reduce_noise(self,
                     image: np.ndarray,
                     strength: int = 5) -> np.ndarray:
        """
        Apply noise reduction.
        
        Args:
            image: Input image
            strength: Denoising strength (1-10)
        
        Returns:
            image: Denoised image
        """
        return cv2.fastNlMeansDenoisingColored(
            image, None, strength, strength, 7, 21
        )
    
    def adjust_gamma(self,
                     image: np.ndarray,
                     gamma: float = 1.0) -> np.ndarray:
        """
        Adjust gamma (mid-tones).
        
        Args:
            image: Input image
            gamma: Gamma value (< 1 = brighter, > 1 = darker)
        
        Returns:
            image: Gamma-adjusted image
        """
        inv_gamma = 1.0 / gamma
        table = np.array([
            ((i / 255.0) ** inv_gamma) * 255
            for i in np.arange(0, 256)
        ]).astype("uint8")
        
        return cv2.LUT(image, table)
    
    def full_enhancement(self,
                         image: np.ndarray,
                         auto_levels: bool = False,
                         white_balance: bool = False,
                         denoise: bool = False,
                         gamma: float = 1.0) -> np.ndarray:
        """
        Apply full enhancement pipeline.
        
        Args:
            image: Input image
            auto_levels: Apply auto levels
            white_balance: Apply white balance
            denoise: Apply noise reduction
            gamma: Gamma adjustment
        
        Returns:
            image: Fully enhanced image
        """
        result = image.copy()
        
        # Optional: Auto levels
        if auto_levels:
            result = self.auto_levels(result)
        
        # Optional: White balance
        if white_balance:
            result = self.white_balance(result)
        
        # Optional: Denoise
        if denoise:
            result = self.reduce_noise(result, strength=3)
        
        # Gamma adjustment
        if gamma != 1.0:
            result = self.adjust_gamma(result, gamma)
        
        # Standard enhancements
        result = self.enhance_image(result)
        
        return result


class OutputFormatter:
    """
    Format and export final images.
    """
    
    def __init__(self):
        pass
    
    def save_jpeg(self,
                  image: np.ndarray,
                  path: str,
                  quality: int = 95) -> str:
        """
        Save as high-quality JPEG.
        
        Args:
            image: Image to save
            path: Output path
            quality: JPEG quality (0-100)
        
        Returns:
            path: Saved file path
        """
        cv2.imwrite(path, image, [cv2.IMWRITE_JPEG_QUALITY, quality])
        return path
    
    def save_png(self,
                 image: np.ndarray,
                 path: str,
                 compression: int = 6) -> str:
        """
        Save as PNG (lossless).
        
        Args:
            image: Image to save
            path: Output path
            compression: Compression level (0-9)
        
        Returns:
            path: Saved file path
        """
        cv2.imwrite(path, image, [cv2.IMWRITE_PNG_COMPRESSION, compression])
        return path
    
    def save_webp(self,
                  image: np.ndarray,
                  path: str,
                  quality: int = 90) -> str:
        """
        Save as WebP (modern format).
        
        Args:
            image: Image to save
            path: Output path
            quality: WebP quality (0-100)
        
        Returns:
            path: Saved file path
        """
        cv2.imwrite(path, image, [cv2.IMWRITE_WEBP_QUALITY, quality])
        return path
    
    def resize_for_web(self,
                       image: np.ndarray,
                       max_width: int = 1920,
                       max_height: int = 1080) -> np.ndarray:
        """
        Resize image for web display.
        
        Args:
            image: Input image
            max_width: Maximum width
            max_height: Maximum height
        
        Returns:
            image: Resized image
        """
        h, w = image.shape[:2]
        
        scale = min(max_width / w, max_height / h)
        
        if scale < 1.0:
            new_w = int(w * scale)
            new_h = int(h * scale)
            return cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_AREA)
        
        return image
    
    def create_thumbnail(self,
                         image: np.ndarray,
                         size: int = 200) -> np.ndarray:
        """
        Create square thumbnail.
        
        Args:
            image: Input image
            size: Thumbnail size (square)
        
        Returns:
            thumbnail: Square thumbnail
        """
        h, w = image.shape[:2]
        
        # Crop to square from center
        if w > h:
            x = (w - h) // 2
            square = image[:, x:x + h]
        else:
            y = (h - w) // 2
            square = image[y:y + w, :]
        
        # Resize to target size
        return cv2.resize(square, (size, size), interpolation=cv2.INTER_AREA)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python postprocess.py <image_path>")
        sys.exit(1)
    
    image = cv2.imread(sys.argv[1])
    
    processor = PostProcessor()
    enhanced = processor.full_enhancement(image)
    
    output_path = sys.argv[1].rsplit('.', 1)[0] + "_enhanced.jpg"
    cv2.imwrite(output_path, enhanced, [cv2.IMWRITE_JPEG_QUALITY, 95])
    print(f"✅ Enhanced image saved to: {output_path}")

