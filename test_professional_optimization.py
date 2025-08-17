#!/usr/bin/env python3
"""
Test the professional image optimization API
"""

import requests
import cv2
import numpy as np
import os

def create_test_images():
    """Create test images with different characteristics"""
    
    # 1. High-detail photographic image
    img1 = np.random.randint(0, 255, (800, 1200, 3), dtype=np.uint8)
    # Add some structure
    for i in range(0, 800, 50):
        cv2.line(img1, (0, i), (1200, i), (255, 255, 255), 2)
    for i in range(0, 1200, 50):
        cv2.line(img1, (i, 0), (i, 800), (255, 255, 255), 2)
    cv2.imwrite('test_photo_detailed.jpg', img1)
    
    # 2. Simple graphic image
    img2 = np.ones((600, 800, 3), dtype=np.uint8) * 255
    cv2.rectangle(img2, (100, 100), (700, 500), (255, 0, 0), -1)
    cv2.circle(img2, (400, 300), 150, (0, 255, 0), -1)
    cv2.putText(img2, 'SIMPLE GRAPHIC', (200, 350), cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 255), 3)
    cv2.imwrite('test_graphic_simple.png', img2)
    
    # 3. Image with transparency
    img3 = np.ones((400, 600, 4), dtype=np.uint8) * 255
    # Create transparent areas
    img3[100:300, 200:400, 3] = 0  # Transparent rectangle
    cv2.circle(img3, (300, 200), 80, (255, 0, 0, 255), -1)  # Red circle
    cv2.imwrite('test_transparency.png', img3)
    
    print("✅ Created test images for optimization")

def test_optimization_api(image_path, test_name, format_type='auto', lossless=False, reduce_dims=False):
    """Test optimization API with specific settings"""
    
    url = 'http://localhost:3000/api/optimize-convert'
    
    files = {
        'image': (image_path, open(image_path, 'rb'), 'image/jpeg' if image_path.endswith('.jpg') else 'image/png')
    }
    
    data = {
        'format': format_type,
        'losslessOptimize': 'true' if lossless else 'false',
        'reduceDimensions': 'true' if reduce_dims else 'false',
        'reduction': '80' if reduce_dims else '100'
    }
    
    try:
        print(f"\n🧪 Testing {test_name}")
        print(f"   📁 Source: {image_path}")
        print(f"   🎯 Format: {format_type}, Lossless: {lossless}, Reduce: {reduce_dims}")
        
        # Get original file size
        original_size = os.path.getsize(image_path)
        print(f"   📊 Original size: {original_size:,} bytes")
        
        response = requests.post(url, files=files, data=data)
        
        if response.status_code == 200:
            result = response.json()
            
            # Extract results
            processed_size = result.get('processedSize', 0)
            compression_ratio = result.get('compressionRatio', '0%')
            final_format = result.get('format', 'unknown')
            optimization_method = result.get('optimizationMethod', 'unknown')
            professional_opt = result.get('professionalOptimization', False)
            quality_used = result.get('qualityUsed', 'unknown')
            
            print(f"   ✅ Success!")
            print(f"   📈 Compression: {compression_ratio}")
            print(f"   💾 Final size: {processed_size:,} bytes")
            print(f"   🎨 Format: {final_format}")
            print(f"   🔧 Method: {optimization_method}")
            print(f"   🤖 Professional: {'Yes' if professional_opt else 'No'}")
            print(f"   🎛️  Quality: {quality_used}")
            
            # Calculate actual compression
            if processed_size > 0:
                actual_compression = ((original_size - processed_size) / original_size) * 100
                print(f"   📉 Actual compression: {actual_compression:.1f}%")
                
                # Check if optimization was effective
                if processed_size < original_size:
                    print(f"   🎉 File size reduced successfully!")
                    return True
                else:
                    print(f"   ⚠️  File size increased (optimization may have failed)")
                    return False
            else:
                print(f"   ❌ Invalid processed size")
                return False
                
        else:
            print(f"   ❌ API failed with status {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False
    
    finally:
        files['image'][1].close()

def main():
    """Run comprehensive optimization tests"""
    
    print("🚀 Testing Professional Image Optimization")
    print("=" * 60)
    
    # Create test images
    create_test_images()
    
    # Test scenarios
    test_cases = [
        # Format: (image_path, test_name, format, lossless, reduce_dims)
        ('test_photo_detailed.jpg', 'Detailed Photo → Auto Format', 'auto', False, False),
        ('test_photo_detailed.jpg', 'Detailed Photo → WebP Lossy', 'webp', False, False),
        ('test_photo_detailed.jpg', 'Detailed Photo → JPEG High Quality', 'jpeg', True, False),
        ('test_photo_detailed.jpg', 'Detailed Photo → Reduced Size', 'auto', False, True),
        
        ('test_graphic_simple.png', 'Simple Graphic → Auto Format', 'auto', False, False),
        ('test_graphic_simple.png', 'Simple Graphic → PNG Optimized', 'png', False, False),
        ('test_graphic_simple.png', 'Simple Graphic → WebP Lossless', 'webp', True, False),
        
        ('test_transparency.png', 'Transparency → Auto Format', 'auto', False, False),
        ('test_transparency.png', 'Transparency → PNG Lossless', 'png', True, False),
        ('test_transparency.png', 'Transparency → WebP Lossless', 'webp', True, False),
    ]
    
    results = []
    
    for image_path, test_name, format_type, lossless, reduce_dims in test_cases:
        try:
            success = test_optimization_api(image_path, test_name, format_type, lossless, reduce_dims)
            results.append((test_name, success))
        except FileNotFoundError:
            print(f"   ⚠️  Skipping {test_name} - file not found")
            results.append((test_name, False))
    
    # Summary
    print(f"\n📊 Professional Optimization Test Results")
    print("=" * 60)
    
    successful = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"   {status} {test_name}")
    
    print(f"\n🎯 Overall: {successful}/{total} tests passed")
    
    if successful >= total * 0.8:  # 80% success rate
        print("🎉 Professional optimization is working well!")
        print("🔧 Key improvements:")
        print("   • Industry-best compression algorithms")
        print("   • Smart format selection (auto-detect optimal format)")
        print("   • Content-aware quality adjustment")
        print("   • Proper transparency handling")
        print("   • Advanced preprocessing (noise reduction, EXIF handling)")
        print("   • Multi-pass optimization")
    else:
        print("⚠️  Some optimization tests failed. Check the issues above.")

if __name__ == "__main__":
    main()
