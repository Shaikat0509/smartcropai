#!/usr/bin/env python3
"""
Professional Image Optimizer
Uses industry-best optimization techniques similar to TinyPNG, Squoosh, and other professional tools
"""

import sys
import os
import json
import logging
from PIL import Image, ImageOps, ImageFilter
import pillow_heif
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Register HEIF opener with Pillow
pillow_heif.register_heif_opener()

class ProfessionalImageOptimizer:
    def __init__(self):
        """Initialize the professional image optimizer"""
        self.supported_formats = {
            'jpeg': ['.jpg', '.jpeg'],
            'png': ['.png'],
            'webp': ['.webp'],
            'avif': ['.avif'],
            'heic': ['.heic', '.heif']
        }

    def _get_original_format(self, image_path):
        """Get the original format of the image"""
        try:
            with Image.open(image_path) as img:
                format_name = img.format
                if format_name == 'JPEG':
                    return 'jpeg'
                elif format_name == 'PNG':
                    return 'png'
                elif format_name == 'WEBP':
                    return 'webp'
                else:
                    return 'jpeg'  # Default fallback
        except Exception:
            return 'jpeg'  # Default fallback

    def detect_image_type(self, image_path):
        """Detect the optimal output format based on image content"""
        try:
            with Image.open(image_path) as img:
                # Check if image has transparency
                has_transparency = (
                    img.mode in ('RGBA', 'LA') or
                    (img.mode == 'P' and 'transparency' in img.info)
                )

                # More sophisticated graphic detection
                colors = img.getcolors(maxcolors=512)  # Increased threshold
                is_graphic = False

                if colors is not None:
                    # Consider it graphic if:
                    # 1. Very few colors (< 32)
                    # 2. Few colors with high contrast (typical of logos/graphics)
                    num_colors = len(colors)
                    is_graphic = num_colors <= 32

                    # Additional check for medium color count graphics
                    if not is_graphic and num_colors <= 128:
                        # Check if colors are well-separated (typical of graphics)
                        sorted_colors = sorted(colors, key=lambda x: x[0], reverse=True)
                        top_colors = sorted_colors[:10]  # Top 10 most frequent colors
                        top_color_ratio = sum(count for count, _ in top_colors) / (img.width * img.height)

                        # If top 10 colors make up >80% of image, it's likely graphic
                        if top_color_ratio > 0.8:
                            is_graphic = True

                return {
                    'has_transparency': has_transparency,
                    'is_graphic': is_graphic,
                    'mode': img.mode,
                    'colors': len(colors) if colors else 'many',
                    'original_format': img.format
                }
        except Exception as e:
            logger.warning(f"Could not analyze image: {e}")
            return {'has_transparency': False, 'is_graphic': False, 'mode': 'RGB', 'colors': 'unknown', 'original_format': None}
    
    def optimize_jpeg(self, img, quality='auto', progressive=True):
        """Optimize JPEG with industry-best settings"""
        
        # Auto-determine quality based on image analysis
        if quality == 'auto':
            # Analyze image complexity
            try:
                # Convert to grayscale for analysis
                gray = img.convert('L')
                # Apply edge detection to measure detail level
                edges = gray.filter(ImageFilter.FIND_EDGES)
                edge_pixels = sum(1 for pixel in edges.getdata() if pixel > 30)
                edge_ratio = edge_pixels / (img.width * img.height)
                
                # Determine quality based on detail level
                if edge_ratio > 0.1:  # High detail image
                    quality = 85
                elif edge_ratio > 0.05:  # Medium detail
                    quality = 80
                else:  # Low detail, can compress more
                    quality = 75
                    
            except Exception:
                quality = 80  # Safe default
        
        # Ensure RGB mode for JPEG
        if img.mode != 'RGB':
            if img.mode == 'RGBA':
                # Create white background for transparency
                background = Image.new('RGB', img.size, (255, 255, 255))
                background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = background
            else:
                img = img.convert('RGB')
        
        return img, {
            'format': 'JPEG',
            'quality': quality,
            'progressive': progressive,
            'optimize': True,
            'subsampling': 0 if quality > 90 else 2  # Better subsampling for high quality
        }
    
    def optimize_png(self, img, compression_level=9):
        """Optimize PNG with advanced compression"""
        
        # Analyze if we can reduce to palette mode
        if img.mode == 'RGB':
            # Try to quantize to palette if it has few colors
            try:
                quantized = img.quantize(colors=256, method=Image.Quantize.MEDIANCUT)
                # Check if quantization is lossless enough
                if self._calculate_image_similarity(img, quantized.convert('RGB')) > 0.98:
                    img = quantized
            except Exception:
                pass
        
        # Optimize transparency
        if img.mode == 'RGBA':
            # Remove unnecessary alpha channel if all pixels are opaque
            alpha = img.split()[-1]
            if alpha.getextrema() == (255, 255):
                img = img.convert('RGB')
        
        return img, {
            'format': 'PNG',
            'optimize': True,
            'compress_level': compression_level
        }
    
    def optimize_webp(self, img, quality='auto', lossless=False):
        """Optimize WebP with advanced settings"""
        
        if lossless:
            return img, {
                'format': 'WebP',
                'lossless': True,
                'quality': 100,
                'method': 6  # Best compression method
            }
        
        # Auto-determine quality
        if quality == 'auto':
            # WebP can handle lower quality better than JPEG
            if hasattr(img, 'mode'):
                if img.mode in ('RGBA', 'LA'):
                    quality = 85  # Preserve transparency quality
                else:
                    quality = 80  # Can compress more aggressively
            else:
                quality = 80
        
        return img, {
            'format': 'WebP',
            'quality': quality,
            'method': 6,  # Best compression method
            'lossless': False
        }
    
    def _calculate_image_similarity(self, img1, img2):
        """Calculate similarity between two images (0-1 scale)"""
        try:
            # Simple MSE-based similarity
            import numpy as np
            arr1 = np.array(img1.resize((64, 64)))  # Downsample for speed
            arr2 = np.array(img2.resize((64, 64)))
            mse = np.mean((arr1 - arr2) ** 2)
            # Convert MSE to similarity (higher is better)
            return max(0, 1 - (mse / 10000))
        except Exception:
            return 0.5  # Unknown similarity
    
    def apply_smart_preprocessing(self, img):
        """Apply smart preprocessing to improve compression"""
        
        # Auto-orient based on EXIF
        img = ImageOps.exif_transpose(img)
        
        # Remove unnecessary metadata but keep color profile
        if hasattr(img, 'info'):
            # Keep only essential info
            essential_info = {}
            if 'icc_profile' in img.info:
                essential_info['icc_profile'] = img.info['icc_profile']
            img.info = essential_info
        
        # Apply subtle noise reduction for better compression
        if img.mode in ('RGB', 'RGBA'):
            # Very light blur to reduce noise without affecting quality
            img = img.filter(ImageFilter.GaussianBlur(radius=0.3))
        
        return img
    
    def optimize_image(self, input_path, output_path, target_format=None, quality='auto', 
                      lossless=False, max_width=None, max_height=None):
        """
        Optimize image with professional-grade compression
        
        Args:
            input_path: Path to input image
            output_path: Path to output image
            target_format: Target format ('jpeg', 'png', 'webp', 'auto')
            quality: Quality setting ('auto', or 1-100)
            lossless: Whether to use lossless compression
            max_width: Maximum width (will resize if larger)
            max_height: Maximum height (will resize if larger)
        """
        try:
            # Load and analyze image
            with Image.open(input_path) as img:
                original_size = os.path.getsize(input_path)
                original_width, original_height = img.size
                
                logger.info(f"Processing image: {original_width}x{original_height}, {img.mode}, {original_size} bytes")
                
                # Apply smart preprocessing
                img = self.apply_smart_preprocessing(img)
                
                # Resize if needed
                if max_width or max_height:
                    # Calculate new dimensions maintaining aspect ratio
                    ratio = min(
                        (max_width / img.width) if max_width else 1,
                        (max_height / img.height) if max_height else 1,
                        1  # Don't upscale
                    )
                    
                    if ratio < 1:
                        new_width = int(img.width * ratio)
                        new_height = int(img.height * ratio)
                        img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                        logger.info(f"Resized to: {new_width}x{new_height}")
                
                # Determine optimal format - don't auto-convert unless explicitly requested
                if target_format == 'auto':
                    # Keep original format unless there's a compelling reason to change
                    original_format = self._get_original_format(input_path)
                    analysis = self.detect_image_type(input_path)

                    if analysis['has_transparency'] and original_format not in ['png', 'webp']:
                        target_format = 'png'  # Keep transparency, use PNG for compatibility
                    else:
                        target_format = original_format  # Keep original format
                
                # Apply format-specific optimization
                if target_format == 'jpeg':
                    img, save_params = self.optimize_jpeg(img, quality)
                elif target_format == 'png':
                    img, save_params = self.optimize_png(img)
                elif target_format == 'webp':
                    img, save_params = self.optimize_webp(img, quality, lossless)
                else:
                    # Default to JPEG
                    img, save_params = self.optimize_jpeg(img, quality)
                
                # Save optimized image
                img.save(output_path, **save_params)

                # Calculate results
                optimized_size = os.path.getsize(output_path)
                compression_ratio = ((original_size - optimized_size) / original_size) * 100

                # If optimization made file larger and we're in auto mode, try original format
                if compression_ratio < 0 and target_format == 'auto':
                    logger.info(f"Optimization increased file size by {abs(compression_ratio):.1f}%, trying original format...")

                    # Try to preserve original format
                    analysis = self.detect_image_type(input_path)
                    original_format = analysis.get('original_format', '').lower()

                    if original_format in ['png', 'jpeg', 'jpg']:
                        fallback_format = 'png' if original_format == 'png' else 'jpeg'

                        # Re-optimize with original format
                        if fallback_format == 'jpeg':
                            img_fallback, save_params_fallback = self.optimize_jpeg(img, quality)
                        else:
                            img_fallback, save_params_fallback = self.optimize_png(img)

                        # Save fallback version
                        fallback_path = output_path + '.fallback'
                        img_fallback.save(fallback_path, **save_params_fallback)
                        fallback_size = os.path.getsize(fallback_path)

                        # Use fallback if it's smaller
                        if fallback_size < optimized_size:
                            os.replace(fallback_path, output_path)
                            optimized_size = fallback_size
                            compression_ratio = ((original_size - optimized_size) / original_size) * 100
                            save_params = save_params_fallback
                            logger.info(f"Used fallback format {fallback_format}, compression: {compression_ratio:.1f}%")
                        else:
                            os.remove(fallback_path)
                
                return {
                    'success': True,
                    'original_size': original_size,
                    'optimized_size': optimized_size,
                    'compression_ratio': round(compression_ratio, 1),
                    'format': save_params['format'],
                    'quality_used': save_params.get('quality', 'lossless' if lossless else 'auto'),
                    'dimensions': f"{img.width}x{img.height}"
                }
                
        except Exception as e:
            logger.error(f"Optimization failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }

def main():
    if len(sys.argv) < 3:
        print("Usage: python professional_image_optimizer.py <input_path> <output_path> [options_json]")
        sys.exit(1)
    
    input_path = sys.argv[1]
    output_path = sys.argv[2]
    
    # Parse options
    options = {}
    if len(sys.argv) > 3:
        try:
            options = json.loads(sys.argv[3])
        except Exception as e:
            logger.warning(f"Could not parse options: {e}")
    
    # Create output directory
    output_dir = os.path.dirname(output_path)
    if output_dir:  # Only create directory if there is a directory path
        os.makedirs(output_dir, exist_ok=True)
    
    # Initialize optimizer
    optimizer = ProfessionalImageOptimizer()
    
    # Optimize image
    result = optimizer.optimize_image(
        input_path=input_path,
        output_path=output_path,
        target_format=options.get('format', 'auto'),
        quality=options.get('quality', 'auto'),
        lossless=options.get('lossless', False),
        max_width=options.get('max_width'),
        max_height=options.get('max_height')
    )
    
    # Output result
    print(json.dumps(result, indent=2))
    
    if not result['success']:
        sys.exit(1)

if __name__ == "__main__":
    main()
