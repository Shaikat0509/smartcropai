#!/usr/bin/env python3
"""
Test the video cropping fix to ensure videos are properly cropped to target size
"""

import requests
import cv2
import numpy as np
import os

def create_test_video_with_face():
    """Create a test video with a face that should be detected and cropped"""
    print("📹 Creating test video with moving face...")
    
    # Video properties - landscape video
    width, height = 1280, 720  # 16:9 landscape
    fps = 10
    duration = 3  # seconds
    total_frames = fps * duration
    
    # Create video writer
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter('test_video_crop.mp4', fourcc, fps, (width, height))
    
    for frame_num in range(total_frames):
        # Create frame with gradient background
        frame = np.zeros((height, width, 3), dtype=np.uint8)
        
        # Add gradient background
        for y in range(height):
            intensity = int(100 + (y / height) * 100)
            frame[y, :] = [intensity, intensity//2, intensity//3]
        
        # Moving face-like object (moves from left to center)
        progress = frame_num / total_frames
        face_x = int(200 + progress * 400)  # Move from left side toward center
        face_y = int(height // 2)  # Center vertically
        
        # Draw realistic face
        face_size = 80
        cv2.circle(frame, (face_x, face_y), face_size, (255, 220, 177), -1)  # Face
        cv2.circle(frame, (face_x - 25, face_y - 20), 12, (0, 0, 0), -1)  # Left eye
        cv2.circle(frame, (face_x + 25, face_y - 20), 12, (0, 0, 0), -1)  # Right eye
        cv2.ellipse(frame, (face_x, face_y + 25), (30, 15), 0, 0, 180, (0, 0, 0), 3)  # Mouth
        
        # Add some background objects to make detection more realistic
        cv2.rectangle(frame, (50, 50), (150, 150), (100, 100, 100), -1)  # Background object
        cv2.rectangle(frame, (width-150, height-150), (width-50, height-50), (80, 80, 80), -1)  # Another object
        
        # Add frame info
        cv2.putText(frame, f'Frame {frame_num+1}/{total_frames}', (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.putText(frame, f'Face at X:{face_x}', (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        out.write(frame)
    
    out.release()
    print(f"✅ Test video created: {width}x{height} ({total_frames} frames)")

def test_video_cropping(platform, expected_width, expected_height, description):
    """Test video cropping for a specific platform"""
    
    print(f"\n🧪 Testing {description}")
    print(f"   📐 Target: {expected_width}x{expected_height}")
    
    url = 'http://localhost:3000/api/resize-compress-video'
    
    files = {
        'video': ('test_video_crop.mp4', open('test_video_crop.mp4', 'rb'), 'video/mp4')
    }
    
    data = {
        'platform': platform,
        'quality': 'medium',
        'compress': 'false'
    }
    
    try:
        print("   🔄 Processing video...")
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
            
            print(f"   ✅ Processing successful!")
            print(f"   📐 Output: {actual_width}x{actual_height}")
            print(f"   🤖 Method: {method}")
            print(f"   🔍 Detections: {detections}")
            print(f"   📁 File: {result.get('filename', 'Unknown')}")
            
            # Check if dimensions match exactly
            dimensions_correct = (actual_width == expected_width and actual_height == expected_height)
            
            # Check if AI detection was used
            ai_used = method == 'ai_detected' and detections > 0
            
            if dimensions_correct:
                print(f"   ✅ Dimensions match target exactly!")
            else:
                print(f"   ❌ Dimensions don't match (expected {expected_width}x{expected_height})")
            
            if ai_used:
                print(f"   ✅ AI detection and smart cropping used!")
            else:
                print(f"   ⚠️  AI detection may not have worked (using fallback)")
            
            return dimensions_correct and ai_used
            
        else:
            print(f"   ❌ Processing failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False
    
    finally:
        files['video'][1].close()

def test_optimization_without_smart_option():
    """Test that optimization works without smart option and doesn't increase file size"""
    
    print(f"\n🧪 Testing Image Optimization (No Smart Option)")
    
    # Create test image
    img = np.ones((400, 600, 3), dtype=np.uint8) * 255
    cv2.rectangle(img, (100, 100), (500, 300), (255, 0, 0), -1)
    cv2.circle(img, (300, 200), 80, (0, 255, 0), -1)
    cv2.imwrite('test_optimize_no_smart.png', img)
    
    original_size = os.path.getsize('test_optimize_no_smart.png')
    print(f"   📊 Original size: {original_size:,} bytes")
    
    url = 'http://localhost:3000/api/optimize-convert'
    
    files = {
        'image': ('test_optimize_no_smart.png', open('test_optimize_no_smart.png', 'rb'), 'image/png')
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
            
            print(f"   ✅ Optimization successful!")
            print(f"   💾 Final size: {processed_size:,} bytes")
            print(f"   📈 Compression: {compression_ratio}")
            print(f"   🎨 Format: {result.get('format', 'Unknown')}")
            
            # Check if file size was reduced (not increased)
            size_reduced = processed_size < original_size
            
            if size_reduced:
                actual_compression = ((original_size - processed_size) / original_size) * 100
                print(f"   ✅ File size reduced by {actual_compression:.1f}%!")
                return True
            else:
                print(f"   ❌ File size increased or stayed same")
                return False
                
        else:
            print(f"   ❌ Optimization failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False
    
    finally:
        files['image'][1].close()
        try:
            os.remove('test_optimize_no_smart.png')
        except:
            pass

def main():
    """Test both fixes"""
    
    print("🚀 Testing Video Cropping Fix and Optimization Fix")
    print("=" * 60)
    
    # Create test video
    create_test_video_with_face()
    
    # Test video cropping for different platforms
    video_tests = [
        ('instagram-reel', 1080, 1920, 'Instagram Reel (9:16 Portrait)'),
        ('instagram-story', 1080, 1920, 'Instagram Story (9:16 Portrait)'),
        ('tiktok', 1080, 1920, 'TikTok (9:16 Portrait)'),
        ('youtube-1080p', 1920, 1080, 'YouTube 1080p (16:9 Landscape)'),
    ]
    
    video_results = []
    for platform, width, height, description in video_tests:
        success = test_video_cropping(platform, width, height, description)
        video_results.append((description, success))
    
    # Test optimization without smart option
    optimization_success = test_optimization_without_smart_option()
    
    # Summary
    print(f"\n📊 Test Results Summary")
    print("=" * 60)
    
    print("🎬 Video Cropping Tests:")
    video_passed = sum(1 for _, success in video_results if success)
    video_total = len(video_results)
    
    for description, success in video_results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"   {status} {description}")
    
    print(f"\n🖼️  Image Optimization Test:")
    opt_status = "✅ PASS" if optimization_success else "❌ FAIL"
    print(f"   {opt_status} Optimization without smart option")
    
    total_passed = video_passed + (1 if optimization_success else 0)
    total_tests = video_total + 1
    
    print(f"\n🎯 Overall: {total_passed}/{total_tests} tests passed")
    
    if total_passed == total_tests:
        print("🎉 All fixes are working correctly!")
        print("\n📋 Confirmed fixes:")
        print("   1. ✅ Videos are properly cropped to exact target dimensions")
        print("   2. ✅ Smart cropping focuses on detected faces/objects")
        print("   3. ✅ Image optimization doesn't increase file size")
    else:
        print("⚠️  Some tests failed. Please check the issues above.")
    
    # Cleanup
    try:
        os.remove('test_video_crop.mp4')
        print("\n🧹 Cleaned up test files")
    except:
        pass

if __name__ == "__main__":
    main()
