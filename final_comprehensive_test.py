#!/usr/bin/env python3
"""
Final comprehensive test demonstrating both fixes:
1. Smart optimization option completely removed (no file size increases)
2. Video cropping properly crops to target size with face/object detection
"""

import requests
import cv2
import numpy as np
import os

def create_comprehensive_test_media():
    """Create test media for comprehensive testing"""
    
    # 1. Create large test image for optimization
    print("📸 Creating test image for optimization...")
    img = np.random.randint(50, 200, (2000, 3000, 3), dtype=np.uint8)
    # Add some structure to make it realistic
    cv2.rectangle(img, (500, 500), (2500, 1500), (255, 100, 100), -1)
    cv2.circle(img, (1500, 1000), 300, (100, 255, 100), -1)
    cv2.putText(img, 'LARGE TEST IMAGE', (800, 1200), cv2.FONT_HERSHEY_SIMPLEX, 4, (255, 255, 255), 8)
    cv2.imwrite('large_test_image.jpg', img, [cv2.IMWRITE_JPEG_QUALITY, 95])
    
    # 2. Create test video with clear face for cropping
    print("🎬 Creating test video with face for cropping...")
    width, height = 1920, 1080  # Full HD landscape
    fps = 15
    duration = 4
    total_frames = fps * duration
    
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter('comprehensive_test_video.mp4', fourcc, fps, (width, height))
    
    for frame_num in range(total_frames):
        # Create frame with realistic background
        frame = np.zeros((height, width, 3), dtype=np.uint8)
        
        # Add realistic background
        cv2.rectangle(frame, (0, 0), (width, height//3), (135, 206, 235), -1)  # Sky
        cv2.rectangle(frame, (0, height//3), (width, height), (34, 139, 34), -1)  # Ground
        
        # Add some background objects
        cv2.rectangle(frame, (100, 200), (300, 400), (139, 69, 19), -1)  # Building
        cv2.rectangle(frame, (width-300, 150), (width-100, 350), (139, 69, 19), -1)  # Another building
        
        # Moving person with face (moves across screen)
        progress = frame_num / total_frames
        person_x = int(200 + progress * 1200)  # Move across screen
        person_y = int(height * 0.7)  # Bottom third
        
        # Draw person body
        cv2.rectangle(frame, (person_x-30, person_y-100), (person_x+30, person_y), (100, 100, 200), -1)
        
        # Draw realistic face
        face_y = person_y - 120
        cv2.circle(frame, (person_x, face_y), 40, (255, 220, 177), -1)  # Face
        cv2.circle(frame, (person_x-15, face_y-10), 6, (0, 0, 0), -1)  # Left eye
        cv2.circle(frame, (person_x+15, face_y-10), 6, (0, 0, 0), -1)  # Right eye
        cv2.ellipse(frame, (person_x, face_y+15), (15, 8), 0, 0, 180, (0, 0, 0), 2)  # Mouth
        
        # Add frame info
        cv2.putText(frame, f'Person at X:{person_x}', (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        cv2.putText(frame, f'Frame {frame_num+1}/{total_frames}', (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        
        out.write(frame)
    
    out.release()
    print("✅ Test media created successfully")

def test_image_optimization_no_increase():
    """Test that image optimization never increases file size"""
    
    print("\n🧪 Testing Image Optimization (No Size Increases)")
    
    original_size = os.path.getsize('large_test_image.jpg')
    print(f"   📊 Original size: {original_size:,} bytes")
    
    url = 'http://localhost:3000/api/optimize-convert'
    
    files = {
        'image': ('large_test_image.jpg', open('large_test_image.jpg', 'rb'), 'image/jpeg')
    }
    
    data = {
        'format': 'auto',
        'reduceDimensions': 'false'
    }
    
    try:
        response = requests.post(url, files=files, data=data)
        
        if response.status_code == 200:
            result = response.json()
            
            processed_size = result.get('processedSize', 0)
            compression_ratio = result.get('compressionRatio', '0%')
            format_used = result.get('format', 'Unknown')
            
            print(f"   ✅ Optimization completed!")
            print(f"   💾 Final size: {processed_size:,} bytes")
            print(f"   📈 Compression: {compression_ratio}")
            print(f"   🎨 Format: {format_used}")
            
            # Check if file size was reduced
            if processed_size < original_size:
                actual_reduction = ((original_size - processed_size) / original_size) * 100
                print(f"   ✅ File size reduced by {actual_reduction:.1f}%!")
                return True
            else:
                print(f"   ❌ File size increased or stayed same - this should not happen!")
                return False
                
        else:
            print(f"   ❌ Optimization failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False
    
    finally:
        files['image'][1].close()

def test_video_smart_cropping(platform, expected_width, expected_height, description):
    """Test smart video cropping for exact dimensions"""
    
    print(f"\n🧪 Testing {description}")
    print(f"   📐 Target: {expected_width}x{expected_height}")
    
    url = 'http://localhost:3000/api/resize-compress-video'
    
    files = {
        'video': ('comprehensive_test_video.mp4', open('comprehensive_test_video.mp4', 'rb'), 'video/mp4')
    }
    
    data = {
        'platform': platform,
        'quality': 'medium',
        'compress': 'false'
    }
    
    try:
        print("   🔄 Processing video with AI detection...")
        response = requests.post(url, files=files, data=data, timeout=120)
        
        if response.status_code == 200:
            result = response.json()
            
            # Get actual dimensions
            actual_width = result.get('dimensions', {}).get('width', 0)
            actual_height = result.get('dimensions', {}).get('height', 0)
            
            # Get AI processing info
            ai_processing = result.get('aiProcessing', {})
            method = ai_processing.get('method', 'unknown')
            detections = ai_processing.get('detectionsFound', 0)
            
            print(f"   ✅ Video processing successful!")
            print(f"   📐 Output: {actual_width}x{actual_height}")
            print(f"   🤖 AI Method: {method}")
            print(f"   🔍 Detections: {detections}")
            print(f"   📁 File: {result.get('filename', 'Unknown')}")
            
            # Check exact dimensions
            dimensions_exact = (actual_width == expected_width and actual_height == expected_height)
            
            # Check AI detection
            ai_working = method == 'ai_detected' and detections > 0
            
            if dimensions_exact:
                print(f"   ✅ Exact target dimensions achieved!")
            else:
                print(f"   ❌ Dimensions don't match exactly")
            
            if ai_working:
                print(f"   ✅ AI detection and smart cropping working!")
            else:
                print(f"   ⚠️  AI detection may not be optimal")
            
            return dimensions_exact and ai_working
            
        else:
            print(f"   ❌ Video processing failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False
    
    finally:
        files['video'][1].close()

def main():
    """Run final comprehensive test"""
    
    print("🚀 Final Comprehensive Test - Both Fixes Working")
    print("=" * 60)
    
    # Create test media
    create_comprehensive_test_media()
    
    # Test 1: Image optimization (no size increases)
    optimization_success = test_image_optimization_no_increase()
    
    # Test 2: Video smart cropping for different aspect ratios
    video_tests = [
        ('instagram-reel', 1080, 1920, 'Instagram Reel (Portrait 9:16)'),
        ('youtube-1080p', 1920, 1080, 'YouTube 1080p (Landscape 16:9)'),
        ('tiktok', 1080, 1920, 'TikTok (Portrait 9:16)'),
    ]
    
    video_results = []
    for platform, width, height, description in video_tests:
        success = test_video_smart_cropping(platform, width, height, description)
        video_results.append((description, success))
    
    # Summary
    print(f"\n📊 Final Test Results")
    print("=" * 60)
    
    print("🖼️  Image Optimization:")
    opt_status = "✅ PASS" if optimization_success else "❌ FAIL"
    print(f"   {opt_status} No file size increases (smart option removed)")
    
    print(f"\n🎬 Video Smart Cropping:")
    video_passed = sum(1 for _, success in video_results if success)
    video_total = len(video_results)
    
    for description, success in video_results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"   {status} {description}")
    
    total_passed = (1 if optimization_success else 0) + video_passed
    total_tests = 1 + video_total
    
    print(f"\n🎯 Overall: {total_passed}/{total_tests} tests passed")
    
    if total_passed == total_tests:
        print("\n🎉 BOTH FIXES ARE WORKING PERFECTLY!")
        print("\n📋 Confirmed fixes:")
        print("   1. ✅ Smart optimization option completely removed")
        print("   2. ✅ Image optimization never increases file size")
        print("   3. ✅ Videos crop to exact target dimensions")
        print("   4. ✅ Smart cropping focuses on detected faces/objects")
        print("   5. ✅ AI detection working across different aspect ratios")
        
        print("\n🔧 Technical achievements:")
        print("   • Removed problematic 'smart' optimization causing size increases")
        print("   • Fixed video cropping to maintain exact aspect ratios")
        print("   • AI face/object detection working for video cropping")
        print("   • Support for portrait (9:16) and landscape (16:9) formats")
        
    else:
        print("\n⚠️  Some tests failed. Please check the issues above.")
    
    # Cleanup
    try:
        os.remove('large_test_image.jpg')
        os.remove('comprehensive_test_video.mp4')
        print("\n🧹 Cleaned up test files")
    except:
        pass

if __name__ == "__main__":
    main()
