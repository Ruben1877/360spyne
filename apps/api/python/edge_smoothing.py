"""
EDGE SMOOTHING MODULE - Clone Spyne
===================================
Smooths mask edges to avoid "cut-out" look.

Parameters found in Spyne's code:
- edge (100+ occurrences)
- smooth
- feather
- radius
"""

import cv2
import numpy as np
from typing import Tuple


class EdgeSmoothing:
    """
    Smooth and refine mask edges for professional-looking cutouts.
    Replicates Spyne's edge refinement pipeline.
    """
    
    def __init__(self):
        pass
    
    def smooth_edges(self, 
                     mask: np.ndarray,
                     blur_radius: int = 3,
                     feather_amount: int = 2) -> np.ndarray:
        """
        Smooth mask edges with blur and feathering.
        
        Args:
            mask: Binary mask (0 or 255)
            blur_radius: Gaussian blur radius (0 = no blur)
            feather_amount: Edge feathering amount
        
        Returns:
            mask: Smoothed mask with soft edges
        """
        result = mask.copy()
        
        # Apply Gaussian blur for soft edges
        if blur_radius > 0:
            kernel_size = blur_radius * 2 + 1
            result = cv2.GaussianBlur(
                result, 
                (kernel_size, kernel_size), 
                0
            )
        
        # Feathering: dilate then erode for smoother boundaries
        if feather_amount > 0:
            kernel = np.ones((feather_amount, feather_amount), np.uint8)
            result = cv2.dilate(result, kernel, iterations=1)
            result = cv2.erode(result, kernel, iterations=1)
        
        return result
    
    def refine_edges(self, 
                     image: np.ndarray, 
                     mask: np.ndarray,
                     iterations: int = 5) -> np.ndarray:
        """
        Refine mask edges using GrabCut (like Spyne).
        
        Args:
            image: BGR image
            mask: Initial mask
            iterations: GrabCut iterations
        
        Returns:
            mask: Refined mask with better edge detection
        """
        # Prepare GrabCut mask
        gc_mask = np.where(
            mask > 127, 
            cv2.GC_PR_FGD, 
            cv2.GC_PR_BGD
        ).astype('uint8')
        
        # Models for GrabCut
        bgd_model = np.zeros((1, 65), np.float64)
        fgd_model = np.zeros((1, 65), np.float64)
        
        try:
            cv2.grabCut(
                image, gc_mask, None,
                bgd_model, fgd_model,
                iterations, cv2.GC_INIT_WITH_MASK
            )
        except cv2.error:
            return mask
        
        # Convert to binary mask
        mask_refined = np.where(
            (gc_mask == cv2.GC_FGD) | (gc_mask == cv2.GC_PR_FGD),
            255, 0
        ).astype('uint8')
        
        return mask_refined
    
    def remove_holes(self, 
                     mask: np.ndarray, 
                     min_hole_size: int = 500) -> np.ndarray:
        """
        Fill small holes in the mask.
        
        Args:
            mask: Binary mask
            min_hole_size: Minimum hole size to fill (pixels)
        
        Returns:
            mask: Mask with holes filled
        """
        # Invert mask to find holes
        inverted = cv2.bitwise_not(mask)
        
        # Find contours of holes
        contours, _ = cv2.findContours(
            inverted, 
            cv2.RETR_EXTERNAL, 
            cv2.CHAIN_APPROX_SIMPLE
        )
        
        # Fill small holes
        result = mask.copy()
        for contour in contours:
            area = cv2.contourArea(contour)
            if area < min_hole_size:
                cv2.drawContours(result, [contour], -1, 255, -1)
        
        return result
    
    def remove_small_components(self, 
                                 mask: np.ndarray,
                                 min_size: int = 1000) -> np.ndarray:
        """
        Remove small disconnected components from the mask.
        
        Args:
            mask: Binary mask
            min_size: Minimum component size to keep
        
        Returns:
            mask: Cleaned mask
        """
        # Find connected components
        num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(
            mask, connectivity=8
        )
        
        # Create output mask
        result = np.zeros_like(mask)
        
        # Keep only large components
        for i in range(1, num_labels):
            if stats[i, cv2.CC_STAT_AREA] >= min_size:
                result[labels == i] = 255
        
        return result
    
    def anti_alias_edges(self, 
                         mask: np.ndarray,
                         strength: float = 1.0) -> np.ndarray:
        """
        Apply anti-aliasing to mask edges.
        
        Args:
            mask: Binary mask
            strength: Anti-aliasing strength (0.0-2.0)
        
        Returns:
            mask: Anti-aliased mask
        """
        # Find edges
        edges = cv2.Canny(mask, 50, 150)
        
        # Dilate edges slightly
        kernel = np.ones((3, 3), np.uint8)
        edges_dilated = cv2.dilate(edges, kernel, iterations=1)
        
        # Create gradient at edges
        edge_mask = edges_dilated.astype(np.float32) / 255.0
        
        # Apply Gaussian blur to edge areas only
        blurred = cv2.GaussianBlur(mask.astype(np.float32), (5, 5), 0)
        
        # Blend original and blurred at edges
        result = mask.astype(np.float32)
        result = result * (1 - edge_mask * strength) + blurred * (edge_mask * strength)
        
        return result.astype(np.uint8)
    
    def full_edge_refinement(self, 
                              image: np.ndarray,
                              mask: np.ndarray,
                              blur_radius: int = 2,
                              feather: int = 1,
                              remove_holes: bool = True,
                              remove_small: bool = True,
                              anti_alias: bool = True) -> np.ndarray:
        """
        Apply full edge refinement pipeline.
        
        Args:
            image: Original BGR image
            mask: Initial mask
            blur_radius: Edge blur radius
            feather: Feather amount
            remove_holes: Fill holes in mask
            remove_small: Remove small components
            anti_alias: Apply anti-aliasing
        
        Returns:
            mask: Fully refined mask
        """
        result = mask.copy()
        
        # 1. Remove small components
        if remove_small:
            result = self.remove_small_components(result, min_size=1000)
        
        # 2. Fill holes
        if remove_holes:
            result = self.remove_holes(result, min_hole_size=500)
        
        # 3. Smooth edges
        result = self.smooth_edges(result, blur_radius, feather)
        
        # 4. Anti-alias
        if anti_alias:
            result = self.anti_alias_edges(result, strength=0.5)
        
        return result


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python edge_smoothing.py <image_path> <mask_path>")
        sys.exit(1)
    
    image = cv2.imread(sys.argv[1])
    mask = cv2.imread(sys.argv[2], cv2.IMREAD_GRAYSCALE)
    
    smoother = EdgeSmoothing()
    refined = smoother.full_edge_refinement(image, mask)
    
    output_path = sys.argv[2].rsplit('.', 1)[0] + "_refined.png"
    cv2.imwrite(output_path, refined)
    print(f"✅ Refined mask saved to: {output_path}")

