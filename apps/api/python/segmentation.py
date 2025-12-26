"""
SEGMENTATION MODULE - Clone Spyne (V3 - Pro Quality)
====================================================
Reproduces Spyne's professional-grade car segmentation.

How Spyne achieves perfect segmentation:
1. Car detection (YOLO/similar) - Find the car first
2. Instance segmentation - Segment only the detected car
3. Alpha matting - Ultra-precise edges (glass, mirrors)
4. Multi-pass refinement - Clean up any artifacts

Our approach:
1. YOLO car detection → Get car bounding box
2. rembg (U2Net/ISNet) → Initial segmentation
3. Alpha matting → Refine edges for glass/chrome
4. GrabCut + Morphology → Final cleanup
"""

import cv2
import numpy as np
from typing import Tuple, Optional, List
import os

# ============== IMPORTS ==============

# rembg for background removal
REMBG_AVAILABLE = False
try:
    from rembg import remove, new_session
    REMBG_AVAILABLE = True
except ImportError:
    print("⚠️ rembg not installed: pip install 'rembg[cpu]'")

# YOLO for car detection
YOLO_AVAILABLE = False
try:
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
except ImportError:
    print("⚠️ ultralytics not installed: pip install ultralytics")

# Alpha matting for precise edges
MATTING_AVAILABLE = False
try:
    from pymatting import cutout, estimate_alpha_cf, estimate_foreground_ml
    MATTING_AVAILABLE = True
except ImportError:
    print("⚠️ pymatting not installed: pip install pymatting")

from PIL import Image


class Segmentation:
    """
    Professional-grade car segmentation like Spyne.
    
    Pipeline:
    1. Detect car with YOLO (focus on vehicle only)
    2. Segment with U2Net/ISNet (initial mask)
    3. Alpha matting (precise edges)
    4. Morphological cleanup (remove noise)
    """
    
    def __init__(self, 
                 model_name: str = "isnet-general-use",
                 use_car_detection: bool = True,
                 use_alpha_matting: bool = True):
        """
        Initialize segmentation pipeline.
        
        Args:
            model_name: rembg model - 'u2net', 'isnet-general-use' (best), 'birefnet-general'
            use_car_detection: Use YOLO to detect car first (recommended)
            use_alpha_matting: Use alpha matting for precise edges
        """
        self.model_name = model_name
        self.use_car_detection = use_car_detection and YOLO_AVAILABLE
        self.use_alpha_matting = use_alpha_matting and MATTING_AVAILABLE
        
        # Initialize rembg session
        self.session = None
        if REMBG_AVAILABLE:
            try:
                self.session = new_session(model_name)
                print(f"✅ Segmentation model: {model_name}")
            except Exception as e:
                print(f"⚠️ Could not load {model_name}, using u2net")
                self.session = new_session("u2net")
        
        # Initialize YOLO car detector
        self.yolo = None
        if self.use_car_detection:
            try:
                self.yolo = YOLO('yolov8n.pt')
                print("✅ Car detector: YOLOv8")
            except Exception as e:
                print(f"⚠️ Could not load YOLO: {e}")
                self.use_car_detection = False
    
    def segment(self, 
                image: np.ndarray, 
                threshold: float = 0.5,
                refine: bool = True) -> np.ndarray:
        """
        Segment car from image with Spyne-level quality.
        
        Args:
            image: BGR numpy array
            threshold: Not used with rembg, kept for compatibility
            refine: Apply additional refinement steps
        
        Returns:
            mask: Binary mask (0 or 255) where 255 = car
        """
        h, w = image.shape[:2]
        
        # Step 1: Detect car bounding box (if enabled)
        car_bbox = None
        if self.use_car_detection:
            car_bbox = self._detect_car(image)
            if car_bbox is not None:
                print(f"        → Car detected: {car_bbox}")
        
        # Step 2: Segment with rembg
        if REMBG_AVAILABLE:
            mask = self._segment_rembg(image, car_bbox)
        else:
            mask = self._fallback_segment(image)
        
        # Step 3: Alpha matting for precise edges (glass, chrome)
        if self.use_alpha_matting and refine:
            mask = self._apply_alpha_matting(image, mask)
        
        # Step 4: Refine with GrabCut
        if refine and np.sum(mask > 0) > 1000:
            mask = self._refine_grabcut(image, mask)
        
        # Step 5: Final cleanup
        mask = self._cleanup_mask(mask)
        
        return mask
    
    def _detect_car(self, image: np.ndarray) -> Optional[Tuple[int, int, int, int]]:
        """
        Detect car using YOLO.
        Returns bounding box (x1, y1, x2, y2) or None.
        """
        if self.yolo is None:
            return None
        
        try:
            # COCO classes for vehicles: 2=car, 5=bus, 7=truck
            results = self.yolo(image, classes=[2, 5, 7], verbose=False)
            
            if len(results) == 0 or len(results[0].boxes) == 0:
                return None
            
            # Get largest vehicle
            boxes = results[0].boxes.xyxy.cpu().numpy()
            areas = (boxes[:, 2] - boxes[:, 0]) * (boxes[:, 3] - boxes[:, 1])
            largest_idx = np.argmax(areas)
            
            bbox = boxes[largest_idx].astype(int)
            return tuple(bbox)
            
        except Exception as e:
            print(f"⚠️ Car detection error: {e}")
            return None
    
    def _segment_rembg(self, 
                       image: np.ndarray, 
                       car_bbox: Optional[Tuple[int, int, int, int]] = None) -> np.ndarray:
        """
        Segment using rembg with optional car bounding box focus.
        """
        h, w = image.shape[:2]
        
        # If car detected, crop to car region (with padding)
        if car_bbox is not None:
            x1, y1, x2, y2 = car_bbox
            
            # Add padding around car (20%)
            pad_x = int((x2 - x1) * 0.2)
            pad_y = int((y2 - y1) * 0.2)
            
            x1 = max(0, x1 - pad_x)
            y1 = max(0, y1 - pad_y)
            x2 = min(w, x2 + pad_x)
            y2 = min(h, y2 + pad_y)
            
            # Crop image
            cropped = image[y1:y2, x1:x2]
            
            # Segment cropped region
            cropped_mask = self._segment_region(cropped)
            
            # Place mask back in full image
            mask = np.zeros((h, w), dtype=np.uint8)
            mask[y1:y2, x1:x2] = cropped_mask
            
            return mask
        
        # Segment full image
        return self._segment_region(image)
    
    def _segment_region(self, image: np.ndarray) -> np.ndarray:
        """
        Segment a region using rembg.
        """
        try:
            # Convert BGR to RGB
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            pil_image = Image.fromarray(image_rgb)
            
            # Get mask only
            if self.session:
                result = remove(pil_image, session=self.session, only_mask=True)
            else:
                result = remove(pil_image, only_mask=True)
            
            mask = np.array(result)
            
            # Ensure grayscale
            if len(mask.shape) == 3:
                mask = cv2.cvtColor(mask, cv2.COLOR_RGB2GRAY)
            
            # Binary threshold
            _, mask = cv2.threshold(mask, 127, 255, cv2.THRESH_BINARY)
            
            return mask
            
        except Exception as e:
            print(f"⚠️ rembg error: {e}")
            return self._fallback_segment(image)
    
    def _apply_alpha_matting(self, 
                              image: np.ndarray, 
                              mask: np.ndarray) -> np.ndarray:
        """
        Apply alpha matting for precise edges.
        This is key for glass, chrome, and thin parts.
        """
        if not MATTING_AVAILABLE:
            return mask
        
        try:
            h, w = image.shape[:2]
            
            # Create trimap from mask
            # Trimap: 0 = background, 128 = unknown, 255 = foreground
            trimap = np.zeros((h, w), dtype=np.uint8)
            
            # Erode mask for definite foreground
            kernel = np.ones((10, 10), np.uint8)
            foreground = cv2.erode(mask, kernel, iterations=2)
            
            # Dilate mask for definite background (inverse)
            background = cv2.dilate(mask, kernel, iterations=2)
            
            # Set trimap values
            trimap[foreground == 255] = 255  # Definite foreground
            trimap[background == 0] = 0      # Definite background
            trimap[(background == 255) & (foreground == 0)] = 128  # Unknown
            
            # Convert to float for matting
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB).astype(np.float64) / 255
            trimap_float = trimap.astype(np.float64) / 255
            
            # Estimate alpha
            alpha = estimate_alpha_cf(image_rgb, trimap_float)
            
            # Convert back to mask
            alpha_mask = (alpha * 255).astype(np.uint8)
            
            # Threshold to binary (for compatibility)
            _, alpha_mask = cv2.threshold(alpha_mask, 127, 255, cv2.THRESH_BINARY)
            
            return alpha_mask
            
        except Exception as e:
            print(f"⚠️ Alpha matting error: {e}")
            return mask
    
    def _refine_grabcut(self, 
                        image: np.ndarray, 
                        mask: np.ndarray,
                        iterations: int = 3) -> np.ndarray:
        """
        Refine mask with GrabCut for cleaner edges.
        """
        try:
            h, w = image.shape[:2]
            
            # Create GrabCut mask
            gc_mask = np.zeros((h, w), np.uint8)
            gc_mask[mask == 0] = cv2.GC_BGD
            gc_mask[mask == 255] = cv2.GC_PR_FGD
            
            # Find definite foreground (eroded center)
            kernel = np.ones((15, 15), np.uint8)
            definite_fg = cv2.erode(mask, kernel, iterations=2)
            gc_mask[definite_fg == 255] = cv2.GC_FGD
            
            # Run GrabCut
            bgd_model = np.zeros((1, 65), np.float64)
            fgd_model = np.zeros((1, 65), np.float64)
            
            cv2.grabCut(image, gc_mask, None, bgd_model, fgd_model, 
                       iterations, cv2.GC_INIT_WITH_MASK)
            
            # Create output mask
            refined = np.where(
                (gc_mask == cv2.GC_FGD) | (gc_mask == cv2.GC_PR_FGD),
                255, 0
            ).astype(np.uint8)
            
            return refined
            
        except Exception as e:
            print(f"⚠️ GrabCut error: {e}")
            return mask
    
    def _cleanup_mask(self, mask: np.ndarray) -> np.ndarray:
        """
        Final mask cleanup.
        """
        # Remove small noise
        kernel_small = np.ones((3, 3), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel_small, iterations=1)
        
        # Fill small holes
        kernel_medium = np.ones((5, 5), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel_medium, iterations=2)
        
        # Keep only largest component
        num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(mask, connectivity=8)
        
        if num_labels > 1:
            largest_label = 1 + np.argmax(stats[1:, cv2.CC_STAT_AREA])
            mask = np.where(labels == largest_label, 255, 0).astype(np.uint8)
        
        # Smooth edges slightly
        mask = cv2.GaussianBlur(mask, (3, 3), 0)
        _, mask = cv2.threshold(mask, 127, 255, cv2.THRESH_BINARY)
        
        return mask
    
    def segment_with_grabcut(self, 
                              image: np.ndarray,
                              initial_mask: np.ndarray = None,
                              iterations: int = 5) -> np.ndarray:
        """
        Full segmentation with extra GrabCut iterations.
        """
        if initial_mask is None:
            initial_mask = self.segment(image, refine=False)
        
        return self._refine_grabcut(image, initial_mask, iterations)
    
    def extract_foreground(self, 
                           image: np.ndarray, 
                           mask: np.ndarray) -> np.ndarray:
        """
        Extract foreground with transparency (RGBA).
        """
        rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        rgba = np.dstack((rgb, mask))
        return rgba
    
    def _fallback_segment(self, image: np.ndarray) -> np.ndarray:
        """
        Fallback when rembg is not available.
        """
        h, w = image.shape[:2]
        
        margin_x = int(w * 0.15)
        margin_y = int(h * 0.15)
        rect = (margin_x, margin_y, w - 2*margin_x, h - 2*margin_y)
        
        mask = np.zeros((h, w), np.uint8)
        bgd_model = np.zeros((1, 65), np.float64)
        fgd_model = np.zeros((1, 65), np.float64)
        
        try:
            cv2.grabCut(image, mask, rect, bgd_model, fgd_model, 5, cv2.GC_INIT_WITH_RECT)
            mask = np.where((mask == cv2.GC_FGD) | (mask == cv2.GC_PR_FGD), 255, 0).astype('uint8')
        except:
            hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
            mask = cv2.inRange(hsv[:,:,1], 30, 255)
        
        return mask
    
    def __del__(self):
        self.session = None
        self.yolo = None


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python segmentation.py <image_path> [output_mask_path]")
        sys.exit(1)
    
    image = cv2.imread(sys.argv[1])
    if image is None:
        print(f"Error: Could not load image {sys.argv[1]}")
        sys.exit(1)
    
    print(f"Processing: {sys.argv[1]} ({image.shape[1]}x{image.shape[0]})")
    
    seg = Segmentation(
        model_name="isnet-general-use",
        use_car_detection=True,
        use_alpha_matting=True
    )
    
    mask = seg.segment(image, refine=True)
    
    output_path = sys.argv[2] if len(sys.argv) > 2 else sys.argv[1].rsplit('.', 1)[0] + "_mask.png"
    cv2.imwrite(output_path, mask)
    print(f"✅ Mask saved: {output_path}")
