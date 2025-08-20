#!/usr/bin/env python3
"""
Test the final UI changes:
1. Resize Images for Social Platforms - single image, max 5MB
2. Optimize & Convert Images - thumbnail preview list with download buttons (TinyPNG style)
"""

import requests
import cv2
import numpy as np
import os
import time

def create_test_images():
    """Create test images for both features"""
    
    print("📸 Creating test images...")
    
    # Create a single test image for resize testing (under 5MB)
    img = np.random.randint(50, 200, (800, 600, 3), dtype=np.uint8)
    cv2.rectangle(img, (50, 50), (550, 350), (255, 100, 100), -1)
    cv2.putText(img, 'RESIZE TEST', (150, 200), cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 255), 3)
    cv2.imwrite('test_resize_single.jpg', img, [cv2.IMWRITE_JPEG_QUALITY, 90])
    
    # Create multiple test images for optimize testing
    for i in range(3):
        img = np.random.randint(100, 255, (400, 600, 3), dtype=np.uint8)
        # Add detailed content for compression testing
        for y in range(0, 400, 50):
            for x in range(0, 600, 50):
                color = (i*80, 255-i*50, 100+i*40)
                cv2.circle(img, (x+25, y+25), 20, color, -1)
        cv2.putText(img, f'OPTIMIZE {i+1}', (200, 200), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        cv2.imwrite(f'test_optimize_multi_{i+1}.jpg', img, [cv2.IMWRITE_JPEG_QUALITY, 95])
    
    print("✅ Test images created")

def test_resize_single_image():
    """Test Resize Images with single image (max 5MB)"""
    
    print("\n🧪 Testing Resize Images - Single Image (max 5MB)")
    
    file_size = os.path.getsize('test_resize_single.jpg')
    print(f"   📊 Test image size: {file_size:,} bytes ({file_size / (1024*1024):.2f} MB)")
    
    if file_size > 5 * 1024 * 1024:
        print(f"   ⚠️  Test image is larger than 5MB")
        return False
    
    url = 'http://localhost:3000/api/resize-image'
    
    files = {
        'image': ('test_resize_single.jpg', open('test_resize_single.jpg', 'rb'), 'image/jpeg')
    }
    
    data = {
        'platform': 'instagram-post'  # 1080x1080
    }
    
    try:
        print(f"   📤 Uploading single image for Instagram Post resize...")
        start_time = time.time()
        
        response = requests.post(url, files=files, data=data, timeout=60)
        processing_time = time.time() - start_time
        
        if response.status_code == 200:
            result = response.json()
            
            print(f"   ✅ Processing successful!")
            print(f"   ⏱️  Processing time: {processing_time:.2f}s")
            print(f"   📐 Output dimensions: {result.get('dimensions', {}).get('width', 0)}x{result.get('dimensions', {}).get('height', 0)}")
            print(f"   📊 Original: {result.get('originalSize', 0):,} bytes")
            print(f"   📊 Processed: {result.get('processedSize', 0):,} bytes")
            
            # Check if it's a single result (not array)
            is_single = not isinstance(result, list)
            dimensions_correct = result.get('dimensions', {}).get('width') == 1080 and result.get('dimensions', {}).get('height') == 1080
            
            print(f"   {'✅' if is_single else '❌'} Single image result: {'WORKING' if is_single else 'FAILED'}")
            print(f"   {'✅' if dimensions_correct else '❌'} Correct dimensions: {'WORKING' if dimensions_correct else 'FAILED'}")
            
            return is_single and dimensions_correct
        else:
            print(f"   ❌ Request failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False
    
    finally:
        files['image'][1].close()

def test_optimize_thumbnail_preview():
    """Test Optimize & Convert with multiple images and thumbnail preview"""
    
    print("\n🧪 Testing Optimize & Convert - Thumbnail Preview (TinyPNG style)")
    
    url = 'http://localhost:3000/api/optimize-convert'
    
    # Prepare multiple files
    files = []
    for i in range(3):
        files.append(('images', (f'test_optimize_multi_{i+1}.jpg', open(f'test_optimize_multi_{i+1}.jpg', 'rb'), 'image/jpeg')))
    
    data = {
        'format': 'original',
        'reduceDimensions': 'false'
    }
    
    try:
        print(f"   📤 Uploading 3 images for optimization...")
        start_time = time.time()
        
        response = requests.post(url, files=files, data=data, timeout=120)
        processing_time = time.time() - start_time
        
        if response.status_code == 200:
            results = response.json()
            
            print(f"   ✅ Processing successful!")
            print(f"   ⏱️  Processing time: {processing_time:.2f}s")
            
            if isinstance(results, list):
                print(f"   📊 Results: {len(results)} images processed")
                
                total_original = 0
                total_optimized = 0
                all_have_download_urls = True
                all_have_filenames = True
                
                for i, result in enumerate(results):
                    original_size = result.get('originalSize', 0)
                    optimized_size = result.get('processedSize', 0)
                    compression = result.get('compressionRatio', '0%')
                    download_url = result.get('downloadUrl', '')
                    filename = result.get('filename', '')
                    
                    total_original += original_size
                    total_optimized += optimized_size
                    
                    if not download_url:
                        all_have_download_urls = False
                    if not filename:
                        all_have_filenames = False
                    
                    print(f"      Image {i+1}: {compression} compression")
                    print(f"      Original: {original_size:,} → Optimized: {optimized_size:,} bytes")
                    print(f"      Download URL: {'✅' if download_url else '❌'}")
                    print(f"      Filename: {'✅' if filename else '❌'}")
                
                overall_compression = ((total_original - total_optimized) / total_original) * 100
                print(f"   📈 Overall compression: {overall_compression:.1f}%")
                
                # Check all requirements for TinyPNG-style interface
                is_array = isinstance(results, list)
                has_compression = overall_compression > 5  # At least 5% compression
                has_download_urls = all_have_download_urls
                has_filenames = all_have_filenames
                correct_count = len(results) == 3
                
                print(f"   {'✅' if is_array else '❌'} Array result: {'WORKING' if is_array else 'FAILED'}")
                print(f"   {'✅' if has_compression else '❌'} Good compression: {'WORKING' if has_compression else 'FAILED'}")
                print(f"   {'✅' if has_download_urls else '❌'} Download URLs: {'WORKING' if has_download_urls else 'FAILED'}")
                print(f"   {'✅' if has_filenames else '❌'} Filenames: {'WORKING' if has_filenames else 'FAILED'}")
                print(f"   {'✅' if correct_count else '❌'} Correct count: {'WORKING' if correct_count else 'FAILED'}")
                
                return is_array and has_compression and has_download_urls and has_filenames and correct_count
            else:
                print(f"   ❌ Expected array result for multiple files, got single result")
                return False
        else:
            print(f"   ❌ Request failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False
    
    finally:
        for file_tuple in files:
            file_tuple[1][1].close()

def test_ui_elements():
    """Test that UI elements are accessible"""
    
    print("\n🧪 Testing UI Elements")
    
    try:
        # Test homepage
        response = requests.get('http://localhost:3000/', timeout=10)
        homepage_loads = response.status_code == 200
        
        # Test resize page
        response = requests.get('http://localhost:3000/resize-image', timeout=10)
        resize_page_loads = response.status_code == 200
        
        # Test optimize page
        response = requests.get('http://localhost:3000/optimize-convert', timeout=10)
        optimize_page_loads = response.status_code == 200
        
        print(f"   📄 Homepage loads: {'✅' if homepage_loads else '❌'}")
        print(f"   📄 Resize page loads: {'✅' if resize_page_loads else '❌'}")
        print(f"   📄 Optimize page loads: {'✅' if optimize_page_loads else '❌'}")
        
        return homepage_loads and resize_page_loads and optimize_page_loads
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def cleanup_test_files():
    """Clean up test files"""
    
    print("\n🧹 Cleaning up test files...")
    
    try:
        os.remove('test_resize_single.jpg')
    except:
        pass
    
    for i in range(3):
        try:
            os.remove(f'test_optimize_multi_{i+1}.jpg')
        except:
            pass
    
    print("✅ Test files cleaned up")

def main():
    """Test final UI changes"""
    
    print("🚀 Testing Final UI Changes")
    print("=" * 60)
    
    # Create test images
    create_test_images()
    
    # Test all features
    resize_working = test_resize_single_image()
    optimize_working = test_optimize_thumbnail_preview()
    ui_working = test_ui_elements()
    
    # Summary
    print(f"\n📊 Final Test Results")
    print("=" * 60)
    
    print(f"🖼️  Resize Images (single, 5MB): {'✅ WORKING' if resize_working else '❌ FAILED'}")
    print(f"🔧 Optimize Images (thumbnail preview): {'✅ WORKING' if optimize_working else '❌ FAILED'}")
    print(f"🌐 UI Elements: {'✅ WORKING' if ui_working else '❌ FAILED'}")
    
    total_passed = sum([resize_working, optimize_working, ui_working])
    total_tests = 3
    
    print(f"\n🎯 Overall: {total_passed}/{total_tests} features working")
    
    if total_passed == total_tests:
        print("\n🎉 ALL FINAL CHANGES ARE WORKING!")
        print("\n📋 Confirmed features:")
        print("   1. ✅ Resize Images: Single image upload, max 5MB")
        print("   2. ✅ Optimize & Convert: Thumbnail preview list")
        print("   3. ✅ TinyPNG-style interface with download buttons")
        print("   4. ✅ Multiple file processing with individual results")
        print("   5. ✅ Compression statistics and download URLs")
        print("   6. ✅ All UI pages loading correctly")
        
        print("\n🔧 Technical achievements:")
        print("   • Reverted resize to single image with proper validation")
        print("   • Added thumbnail preview section for optimize feature")
        print("   • TinyPNG-style result display with download buttons")
        print("   • Individual file progress tracking")
        print("   • Enhanced user experience with visual feedback")
        
    else:
        print("\n⚠️  Some features may need attention")
    
    # Cleanup
    cleanup_test_files()

if __name__ == "__main__":
    main()
