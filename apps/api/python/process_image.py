#!/usr/bin/env python3
"""
MAIN PROCESSING SCRIPT - Clone Spyne
====================================
Complete image processing pipeline that replicates Spyne's workflow.

This script orchestrates:
1. Segmentation (AI background removal)
2. Edge smoothing (clean cutout edges)
3. Background generation (studio floor/wall)
4. Shadow generation (3-layer realistic shadows)
5. Reflection generation (floor mirror effect)
6. Composite (layer assembly)
7. Post-processing (enhancements)

Usage:
    python process_image.py input.jpg output.jpg [preset]
    
Presets: studio_white, studio_grey, studio_dark, showroom, dealership
"""

import sys
import os
import time
import argparse
import cv2
import numpy as np
from pathlib import Path

# Import all modules
from segmentation import Segmentation
from edge_smoothing import EdgeSmoothing
from background import BackgroundGenerator
from shadows import ShadowGenerator
from reflection import ReflectionGenerator
from composite import Compositor
from postprocess import PostProcessor, OutputFormatter

# Import V2 modules (Spyne quality)
try:
    from background_v2 import BackgroundGeneratorV2, ShadowGeneratorV2, create_spyne_render
    V2_AVAILABLE = True
    print("✅ Background V2 (Spyne quality) available")
except ImportError:
    V2_AVAILABLE = False
    print("⚠️ Background V2 not available, using standard quality")


class SpyneCloneProcessor:
    """
    Complete Spyne clone processing pipeline.
    Processes car images to create professional studio-quality photos.
    """
    
    def __init__(self, verbose: bool = True):
        """
        Initialize all processing modules.
        
        Args:
            verbose: Print progress messages
        """
        self.verbose = verbose
        
        self._log("🚗 Initializing Spyne Clone Processor...")
        
        self.segmenter = Segmentation()
        self.edge_smoother = EdgeSmoothing()
        self.bg_generator = BackgroundGenerator()
        self.shadow_generator = ShadowGenerator()
        self.reflection_generator = ReflectionGenerator()
        self.compositor = Compositor()
        self.post_processor = PostProcessor()
        self.output_formatter = OutputFormatter()
        
        self._log("✅ All modules initialized")
        
        # Initialize V2 modules if available
        if V2_AVAILABLE:
            self.bg_generator_v2 = BackgroundGeneratorV2()
            self.shadow_generator_v2 = ShadowGeneratorV2()
            self._log("✅ V2 modules (Spyne quality) initialized")
    
    def _log(self, message: str):
        """Print message if verbose mode is on."""
        if self.verbose:
            print(message)
    
    def process_spyne_quality(self,
                               input_path: str,
                               output_path: str,
                               preset: str = 'spyne_white',
                               output_size: tuple = (1920, 1080),
                               quality: int = 95) -> dict:
        """
        Process with Spyne-quality rendering (V2 pipeline).
        
        Args:
            input_path: Path to input image
            output_path: Path for output image  
            preset: 'spyne_white', 'spyne_grey', 'spyne_dark', 'spyne_showroom'
            output_size: Output dimensions (width, height)
            quality: JPEG quality (0-100)
        
        Returns:
            dict: Processing results
        """
        if not V2_AVAILABLE:
            self._log("⚠️ V2 not available, falling back to standard")
            return self.process(input_path, output_path, 'studio_white', True, True, output_size, quality)
        
        start_time = time.time()
        results = {'success': False, 'input': input_path, 'output': output_path}
        
        try:
            self._log(f"\n🚗 Processing (Spyne Quality): {input_path}")
            
            # 1. Load image
            self._log("  [1/6] Loading...")
            image = cv2.imread(input_path)
            if image is None:
                raise ValueError(f"Could not load: {input_path}")
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            # 2. Segmentation
            self._log("  [2/6] AI Segmentation...")
            mask = self.segmenter.segment(image)
            mask = self.edge_smoother.full_edge_refinement(image, mask)
            
            # 3. Extract car
            self._log("  [3/6] Extracting car...")
            car_rgba = self.segmenter.extract_foreground(image, mask)
            car_rgb = car_rgba[:, :, :3]
            
            # 4. Create Spyne render
            self._log("  [4/6] Spyne-quality rendering...")
            result = create_spyne_render(
                car_rgb, mask, preset, output_size
            )
            
            # 5. Post-processing
            self._log("  [5/6] Post-processing...")
            result = self.post_processor.enhance_image(
                result,
                brightness=1.0,
                contrast=1.03,
                saturation=1.05,
                sharpness=1.08
            )
            
            # 6. Save
            self._log("  [6/6] Saving...")
            result_bgr = cv2.cvtColor(result, cv2.COLOR_RGB2BGR)
            cv2.imwrite(output_path, result_bgr, [cv2.IMWRITE_JPEG_QUALITY, quality])
            
            elapsed = time.time() - start_time
            results['success'] = True
            results['processing_time'] = elapsed
            self._log(f"\n✅ Done in {elapsed:.2f}s: {output_path}")
            
        except Exception as e:
            results['error'] = str(e)
            self._log(f"\n❌ Error: {e}")
        
        return results
    
    def process(self,
                input_path: str,
                output_path: str,
                background_preset: str = 'studio_white',
                add_reflection: bool = True,
                add_shadows: bool = True,
                output_size: tuple = (1920, 1080),
                quality: int = 95) -> dict:
        """
        Process a car image through the complete pipeline.
        
        Args:
            input_path: Path to input image
            output_path: Path for output image
            background_preset: Background style preset
            add_reflection: Add floor reflection effect
            add_shadows: Add shadow layers
            output_size: Output dimensions (width, height)
            quality: JPEG quality (0-100)
        
        Returns:
            dict: Processing results and metadata
        """
        start_time = time.time()
        results = {
            'success': False,
            'input': input_path,
            'output': output_path,
            'stages': {}
        }
        
        try:
            # 1. LOAD IMAGE
            self._log(f"\n🖼️  Processing: {input_path}")
            self._log("  [1/8] Loading image...")
            
            image = cv2.imread(input_path)
            if image is None:
                raise ValueError(f"Could not load image: {input_path}")
            
            original_h, original_w = image.shape[:2]
            results['stages']['load'] = {'width': original_w, 'height': original_h}
            self._log(f"        Loaded: {original_w}x{original_h}")
            
            # 2. SEGMENTATION (AI Background Removal)
            self._log("  [2/8] AI Segmentation (removing background)...")
            
            # Convert to RGB for segmentation
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            mask = self.segmenter.segment(image_rgb, threshold=0.5)
            
            # Optionally refine with GrabCut for better edges
            mask = self.segmenter.segment_with_grabcut(image, mask, iterations=3)
            
            results['stages']['segmentation'] = {'mask_coverage': np.mean(mask > 0)}
            self._log(f"        Mask coverage: {np.mean(mask > 0) * 100:.1f}%")
            
            # 3. EDGE SMOOTHING
            self._log("  [3/8] Smoothing edges...")
            
            mask = self.edge_smoother.full_edge_refinement(
                image, mask,
                blur_radius=2,
                feather=1,
                remove_holes=True,
                remove_small=True,
                anti_alias=True
            )
            
            results['stages']['edge_smoothing'] = {'completed': True}
            
            # 4. PREPARE CAR IMAGE
            self._log("  [4/8] Extracting car...")
            
            car_image = image.copy()
            car_mask = mask.copy()
            
            # Scale car to fit output
            out_w, out_h = output_size
            car_image, car_mask = self.compositor.scale_car_to_fit(
                car_image, car_mask,
                out_w, out_h,
                max_width_ratio=0.75,
                max_height_ratio=0.50
            )
            
            car_h, car_w = car_image.shape[:2]
            results['stages']['car_extraction'] = {'width': car_w, 'height': car_h}
            self._log(f"        Car size: {car_w}x{car_h}")
            
            # 5. GENERATE BACKGROUND
            self._log(f"  [5/8] Generating studio background ({background_preset})...")
            
            background = self.bg_generator.create_complete_background(
                out_w, out_h,
                preset=background_preset,
                vignette=True,
                vignette_strength=0.15,
                ambient_light=True,
                reflection_zone=True
            )
            
            results['stages']['background'] = {'preset': background_preset}
            
            # 6. GENERATE SHADOWS
            shadows = {}
            if add_shadows:
                self._log("  [6/8] Generating shadows (3 layers)...")
                
                # Need full-size mask for shadows
                full_mask = np.zeros((out_h, out_w), dtype=np.uint8)
                
                # Calculate car position
                car_position = self.compositor.auto_position_car(
                    (out_w, out_h), (car_w, car_h)
                )
                x, y = car_position
                
                # Place car mask in full canvas
                y1, y2 = max(0, y), min(out_h, y + car_h)
                x1, x2 = max(0, x), min(out_w, x + car_w)
                cy1, cy2 = max(0, -y), car_h - max(0, y + car_h - out_h)
                cx1, cx2 = max(0, -x), car_w - max(0, x + car_w - out_w)
                
                if y2 > y1 and x2 > x1:
                    full_mask[y1:y2, x1:x2] = car_mask[cy1:cy2, cx1:cx2]
                
                shadows = self.shadow_generator.create_all_shadows(full_mask)
                
                results['stages']['shadows'] = {
                    'contact': shadows['contact'].max() if 'contact' in shadows else 0,
                    'ambient': shadows['ambient'].max() if 'ambient' in shadows else 0,
                    'drop': shadows['drop'].max() if 'drop' in shadows else 0
                }
                self._log("        ✓ Contact, Ambient, Drop shadows created")
            else:
                self._log("  [6/8] Skipping shadows...")
            
            # 7. GENERATE REFLECTION
            reflection, reflection_mask = None, None
            if add_reflection:
                self._log("  [7/8] Generating floor reflection...")
                
                reflection, reflection_mask = self.reflection_generator.create_reflection(
                    car_image, car_mask,
                    opacity=0.18,
                    fade_height=0.5,
                    blur=2
                )
                
                results['stages']['reflection'] = {'opacity': 0.18}
                self._log("        ✓ Reflection created")
            else:
                self._log("  [7/8] Skipping reflection...")
            
            # 8. COMPOSITE FINAL
            self._log("  [8/8] Compositing final image...")
            
            # Calculate car position
            car_position = self.compositor.auto_position_car(
                (out_w, out_h), (car_w, car_h)
            )
            
            # Composite all layers
            final = self.compositor.composite_final(
                background=background,
                car_image=car_image,
                car_mask=car_mask,
                shadows=shadows,
                reflection=reflection,
                reflection_mask=reflection_mask,
                car_position=car_position
            )
            
            # Apply post-processing
            final = self.post_processor.enhance_image(
                cv2.cvtColor(final, cv2.COLOR_RGB2BGR),
                brightness=1.0,
                contrast=1.05,
                saturation=1.10,
                sharpness=1.10
            )
            
            # Save output
            cv2.imwrite(output_path, final, [cv2.IMWRITE_JPEG_QUALITY, quality])
            
            elapsed = time.time() - start_time
            results['success'] = True
            results['elapsed_time'] = elapsed
            results['output_size'] = output_size
            
            self._log(f"\n✅ Complete! Saved to: {output_path}")
            self._log(f"   Processing time: {elapsed:.2f}s")
            
        except Exception as e:
            results['success'] = False
            results['error'] = str(e)
            self._log(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()
        
        return results
    
    def process_batch(self,
                      input_paths: list,
                      output_dir: str,
                      **kwargs) -> list:
        """
        Process multiple images.
        
        Args:
            input_paths: List of input image paths
            output_dir: Output directory
            **kwargs: Processing options
        
        Returns:
            list: Results for each image
        """
        results = []
        
        os.makedirs(output_dir, exist_ok=True)
        
        for i, input_path in enumerate(input_paths, 1):
            self._log(f"\n{'='*50}")
            self._log(f"Processing {i}/{len(input_paths)}")
            
            # Generate output filename
            basename = Path(input_path).stem
            output_path = os.path.join(output_dir, f"{basename}_processed.jpg")
            
            result = self.process(input_path, output_path, **kwargs)
            results.append(result)
        
        # Summary
        success_count = sum(1 for r in results if r['success'])
        self._log(f"\n{'='*50}")
        self._log(f"Batch complete: {success_count}/{len(results)} successful")
        
        return results


def main():
    """Main entry point with CLI argument parsing."""
    parser = argparse.ArgumentParser(
        description='Clone Spyne - Car Image Processor',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python process_image.py car.jpg output.jpg
  python process_image.py car.jpg output.jpg --preset showroom
  python process_image.py car.jpg output.jpg --size 3840 2160 --no-reflection
  python process_image.py *.jpg --batch --output-dir processed/
        """
    )
    
    parser.add_argument('input', help='Input image path')
    parser.add_argument('output', nargs='?', help='Output image path')
    
    parser.add_argument('--preset', '-p', 
                        default='studio_white',
                        choices=['studio_white', 'studio_grey', 'studio_dark', 
                                'showroom', 'dealership', 'outdoor_neutral'],
                        help='Background preset (default: studio_white)')
    
    parser.add_argument('--size', '-s', 
                        nargs=2, type=int, 
                        default=[1920, 1080],
                        metavar=('WIDTH', 'HEIGHT'),
                        help='Output size (default: 1920 1080)')
    
    parser.add_argument('--no-reflection', 
                        action='store_true',
                        help='Disable floor reflection')
    
    parser.add_argument('--no-shadows', 
                        action='store_true',
                        help='Disable shadows')
    
    parser.add_argument('--quality', '-q', 
                        type=int, default=95,
                        help='JPEG quality 0-100 (default: 95)')
    
    parser.add_argument('--quiet', 
                        action='store_true',
                        help='Minimal output')
    
    args = parser.parse_args()
    
    # Determine output path
    if args.output:
        output_path = args.output
    else:
        input_path = Path(args.input)
        output_path = str(input_path.parent / f"{input_path.stem}_processed.jpg")
    
    # Initialize processor
    processor = SpyneCloneProcessor(verbose=not args.quiet)
    
    # Process
    result = processor.process(
        input_path=args.input,
        output_path=output_path,
        background_preset=args.preset,
        add_reflection=not args.no_reflection,
        add_shadows=not args.no_shadows,
        output_size=tuple(args.size),
        quality=args.quality
    )
    
    # Exit code
    sys.exit(0 if result['success'] else 1)


if __name__ == "__main__":
    main()

