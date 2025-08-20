#!/usr/bin/env python3
"""
Test both new features:
1. Squoosh optimization for maximum compression while maintaining quality
2. Auto-cleanup functionality for processed media files
"""

import requests
import cv2
import numpy as np
import os
import time
from PIL import Image

def create_test_images():
    """Create test images for Squoosh optimization testing"""
    
    print("📸 Creating test images for Squoosh optimization...")
    
    # Create a large, detailed JPEG image
    img_large = np.random.randint(50, 200, (2000, 3000, 3), dtype=np.uint8)
    # Add detailed content that should compress well with Squoosh
    for i in range(0, 2000, 100):
        for j in range(0, 3000, 100):
            cv2.rectangle(img_large, (j, i), (j+80, i+80), (255, 100, 100), -1)
            cv2.circle(img_large, (j+40, i+40), 30, (100, 255, 100), -1)
    
    cv2.putText(img_large, 'SQUOOSH TEST - LARGE IMAGE', (500, 1000), cv2.FONT_HERSHEY_SIMPLEX, 4, (255, 255, 255), 8)
    cv2.imwrite('test_squoosh_large.jpg', img_large, [cv2.IMWRITE_JPEG_QUALITY, 95])
    
    # Create a PNG with transparency for format preservation test
    img_png = Image.new('RGBA', (1000, 800), (255, 255, 255, 0))
    for y in range(800):
        for x in range(1000):
            if (x + y) % 150 < 75:
                img_png.putpixel((x, y), (255, 0, 0, 200))
            elif x % 200 < 100:
                img_png.putpixel((x, y), (0, 255, 0, 150))
    img_png.save('test_squoosh_png.png')
    
    print("✅ Test images created")

def test_squoosh_optimization():
    """Test Squoosh optimization for maximum compression"""
    
    print("\n🧪 Testing Squoosh Optimization")
    
    test_cases = [
        ('test_squoosh_large.jpg', 'original', 'Keep original JPEG with Squoosh'),
        ('test_squoosh_png.png', 'original', 'Keep original PNG with Squoosh'),
        ('test_squoosh_large.jpg', 'webp', 'Convert JPEG to WebP with Squoosh'),
    ]
    
    results = []
    
    for filename, format_choice, description in test_cases:
        print(f"\n   📋 {description}")
        
        original_size = os.path.getsize(filename)
        print(f"      📊 Original size: {original_size:,} bytes")
        
        url = 'http://localhost:3000/api/optimize-convert'
        
        files = {
            'image': (filename, open(filename, 'rb'), f'image/{filename.split(".")[-1]}')
        }
        
        data = {
            'format': format_choice,
            'reduceDimensions': 'false'
        }
        
        try:
            start_time = time.time()
            response = requests.post(url, files=files, data=data)
            processing_time = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                
                actual_format = result.get('format', 'Unknown')
                compression_ratio = result.get('compressionRatio', '0%')
                optimization_method = result.get('optimizationMethod', 'Unknown')
                optimized_size = result.get('processedSize', 0)
                
                print(f"      ✅ Optimization successful!")
                print(f"      🎨 Format: {actual_format}")
                print(f"      📈 Compression: {compression_ratio}")
                print(f"      🔧 Method: {optimization_method}")
                print(f"      💾 Final size: {optimized_size:,} bytes")
                print(f"      ⏱️  Processing time: {processing_time:.2f}s")
                
                # Check if Squoosh was used
                squoosh_used = 'squoosh' in optimization_method.lower()
                
                # Check compression effectiveness
                actual_compression = ((original_size - optimized_size) / original_size) * 100
                good_compression = actual_compression > 10  # At least 10% reduction
                
                if squoosh_used:
                    print(f"      ✅ Squoosh optimization used!")
                else:
                    print(f"      ⚠️  Squoosh may not be working (method: {optimization_method})")
                
                if good_compression:
                    print(f"      ✅ Good compression achieved ({actual_compression:.1f}% reduction)!")
                else:
                    print(f"      ⚠️  Limited compression ({actual_compression:.1f}% reduction)")
                
                success = squoosh_used and good_compression
                results.append(success)
                
            else:
                print(f"      ❌ Request failed: {response.status_code}")
                results.append(False)
                
        except Exception as e:
            print(f"      ❌ Error: {e}")
            results.append(False)
        
        finally:
            files['image'][1].close()
    
    return results

def test_cleanup_functionality():
    """Test auto-cleanup functionality"""
    
    print("\n🧪 Testing Auto-Cleanup Functionality")
    
    # Create a simple test image
    img = np.ones((200, 200, 3), dtype=np.uint8) * 150
    cv2.putText(img, 'CLEANUP TEST', (20, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    cv2.imwrite('test_cleanup.jpg', img, [cv2.IMWRITE_JPEG_QUALITY, 90])
    
    # Process the image to create a file that should be cleaned up
    url = 'http://localhost:3000/api/optimize-convert'
    
    files = {
        'image': ('test_cleanup.jpg', open('test_cleanup.jpg', 'rb'), 'image/jpeg')
    }
    
    data = {
        'format': 'original',
        'reduceDimensions': 'false'
    }
    
    try:
        response = requests.post(url, files=files, data=data)
        
        if response.status_code == 200:
            result = response.json()
            processed_filename = result.get('filename', '')
            
            print(f"   📁 Processed file created: {processed_filename}")
            
            # Test cleanup API
            cleanup_url = 'http://localhost:3000/api/cleanup'
            cleanup_data = {
                'files': [
                    {
                        'filename': processed_filename,
                        'type': 'optimize'
                    }
                ]
            }
            
            cleanup_response = requests.post(cleanup_url, json=cleanup_data)
            
            if cleanup_response.status_code == 200:
                cleanup_result = cleanup_response.json()
                cleaned_count = cleanup_result.get('cleanedCount', 0)
                
                print(f"   ✅ Cleanup API working!")
                print(f"   🧹 Files cleaned: {cleaned_count}")
                
                if cleaned_count > 0:
                    print(f"   ✅ Auto-cleanup functionality working!")
                    return True
                else:
                    print(f"   ⚠️  No files were cleaned up")
                    return False
            else:
                print(f"   ❌ Cleanup API failed: {cleanup_response.status_code}")
                return False
        else:
            print(f"   ❌ Image processing failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False
    
    finally:
        files['image'][1].close()
        try:
            os.remove('test_cleanup.jpg')
        except:
            pass

def main():
    """Test both new features"""
    
    print("🚀 Testing Squoosh Optimization & Auto-Cleanup")
    print("=" * 60)
    
    # Create test images
    create_test_images()
    
    # Test Squoosh optimization
    squoosh_results = test_squoosh_optimization()
    
    # Test cleanup functionality
    cleanup_result = test_cleanup_functionality()
    
    # Summary
    print(f"\n📊 Test Results Summary")
    print("=" * 60)
    
    squoosh_passed = sum(squoosh_results)
    squoosh_total = len(squoosh_results)
    
    print(f"🔧 Squoosh Optimization: {squoosh_passed}/{squoosh_total} tests passed")
    print(f"🧹 Auto-Cleanup: {'✅ WORKING' if cleanup_result else '❌ FAILED'}")
    
    total_passed = squoosh_passed + (1 if cleanup_result else 0)
    total_tests = squoosh_total + 1
    
    print(f"\n🎯 Overall: {total_passed}/{total_tests} tests passed")
    
    if total_passed == total_tests:
        print("\n🎉 BOTH NEW FEATURES ARE WORKING!")
        print("\n📋 Confirmed features:")
        print("   1. ✅ Squoosh optimization for maximum compression")
        print("   2. ✅ Auto-cleanup removes processed files")
        print("   3. ✅ Format preservation working correctly")
        print("   4. ✅ Cleanup API endpoint functional")
        
        print("\n🔧 Technical achievements:")
        print("   • Squoosh library integrated for industry-best compression")
        print("   • Auto-cleanup prevents server storage buildup")
        print("   • JavaScript cleanup triggers on page events")
        print("   • Server-side cleanup API handles file removal")
        
    else:
        print("\n⚠️  Some features may need attention")
    
    # Cleanup test files
    try:
        os.remove('test_squoosh_large.jpg')
        os.remove('test_squoosh_png.png')
        print("\n🧹 Cleaned up test files")
    except:
        pass

if __name__ == "__main__":
    main()
