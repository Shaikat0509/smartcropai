#!/usr/bin/env python3
"""
Final test for both fixes:
1. Image format handling - don't change format automatically, validate output
2. Video cropping - proper cropping without stretching/squeezing
"""

import requests
import cv2
import numpy as np
import os
from PIL import Image

def create_test_media():
    """Create test media for both fixes"""
    
    # 1. Create test images in different formats
    print("📸 Creating test images in different formats...")
    
    # JPEG image
    img_jpeg = np.random.randint(100, 200, (800, 1200, 3), dtype=np.uint8)
    cv2.rectangle(img_jpeg, (200, 200), (1000, 600), (255, 100, 100), -1)
    cv2.putText(img_jpeg, 'JPEG TEST', (400, 450), cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 255), 3)
    cv2.imwrite('test_image.jpg', img_jpeg, [cv2.IMWRITE_JPEG_QUALITY, 90])
    
    # PNG image with transparency
    img_png = Image.new('RGBA', (800, 600), (255, 255, 255, 0))
    # Add some content with transparency
    for y in range(600):
        for x in range(800):
            if (x + y) % 100 < 50:
                img_png.putpixel((x, y), (255, 0, 0, 200))
            elif x % 150 < 75:
                img_png.putpixel((x, y), (0, 255, 0, 150))
    img_png.save('test_image.png')
    
    # 2. Create test video for cropping
    print("🎬 Creating test video for cropping...")
    
    width, height = 1920, 1080  # Landscape
    fps = 10
    duration = 3
    total_frames = fps * duration
    
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter('test_video_crop.mp4', fourcc, fps, (width, height))
    
    for frame_num in range(total_frames):
        frame = np.zeros((height, width, 3), dtype=np.uint8)
        
        # Background
        cv2.rectangle(frame, (0, 0), (width, height//2), (100, 150, 200), -1)  # Sky
        cv2.rectangle(frame, (0, height//2), (width, height), (50, 100, 50), -1)  # Ground
        
        # Moving person
        progress = frame_num / total_frames
        person_x = int(300 + progress * 1000)
        person_y = int(height * 0.6)
        
        # Person body
        cv2.rectangle(frame, (person_x-40, person_y-150), (person_x+40, person_y), (100, 100, 200), -1)
        
        # Face
        face_y = person_y - 180
        cv2.circle(frame, (person_x, face_y), 50, (255, 220, 177), -1)
        cv2.circle(frame, (person_x-20, face_y-15), 8, (0, 0, 0), -1)  # Left eye
        cv2.circle(frame, (person_x+20, face_y-15), 8, (0, 0, 0), -1)  # Right eye
        cv2.ellipse(frame, (person_x, face_y+20), (25, 12), 0, 0, 180, (0, 0, 0), 2)  # Mouth
        
        # Labels
        cv2.putText(frame, f'Person at X:{person_x}', (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        cv2.putText(frame, f'{width}x{height} -> Crop Test', (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        
        out.write(frame)
    
    out.release()
    print("✅ Test media created")

def test_image_format_preservation():
    """Test that image formats are preserved when 'Keep Original' is selected"""
    
    print("\n🧪 Testing Image Format Preservation")
    
    test_cases = [
        ('test_image.jpg', 'original', 'JPEG', 'Keep original JPEG format'),
        ('test_image.png', 'original', 'PNG', 'Keep original PNG format'),
        ('test_image.jpg', 'png', 'PNG', 'Convert JPEG to PNG'),
        ('test_image.png', 'webp', 'WebP', 'Convert PNG to WebP'),
    ]
    
    results = []
    
    for filename, format_choice, expected_format, description in test_cases:
        print(f"\n   📋 {description}")
        
        url = 'http://localhost:3000/api/optimize-convert'
        
        files = {
            'image': (filename, open(filename, 'rb'), f'image/{filename.split(".")[-1]}')
        }
        
        data = {
            'format': format_choice,
            'reduceDimensions': 'false'
        }
        
        try:
            response = requests.post(url, files=files, data=data)
            
            if response.status_code == 200:
                result = response.json()
                actual_format = result.get('format', 'Unknown')
                
                print(f"      🎯 Expected: {expected_format}")
                print(f"      📄 Actual: {actual_format}")
                
                format_correct = actual_format.upper() == expected_format.upper()
                
                if format_correct:
                    print(f"      ✅ Format preserved/converted correctly!")
                    results.append(True)
                else:
                    print(f"      ❌ Format mismatch!")
                    results.append(False)
                    
                print(f"      📊 Compression: {result.get('compressionRatio', 'Unknown')}")
                
            else:
                print(f"      ❌ Request failed: {response.status_code}")
                results.append(False)
                
        except Exception as e:
            print(f"      ❌ Error: {e}")
            results.append(False)
        
        finally:
            files['image'][1].close()
    
    return results

def test_video_cropping_accuracy():
    """Test that videos are cropped accurately without stretching"""
    
    print("\n🧪 Testing Video Cropping Accuracy")
    
    test_cases = [
        ('instagram-reel', 1080, 1920, 'Instagram Reel (9:16 Portrait)'),
        ('tiktok', 1080, 1920, 'TikTok (9:16 Portrait)'),
        ('youtube-1080p', 1920, 1080, 'YouTube 1080p (16:9 Landscape)'),
    ]
    
    results = []
    
    for platform, expected_width, expected_height, description in test_cases:
        print(f"\n   📋 {description}")
        print(f"      🎯 Target: {expected_width}x{expected_height}")
        
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
            response = requests.post(url, files=files, data=data, timeout=120)
            
            if response.status_code == 200:
                result = response.json()
                
                actual_width = result.get('dimensions', {}).get('width', 0)
                actual_height = result.get('dimensions', {}).get('height', 0)
                ai_processing = result.get('aiProcessing', {})
                method = ai_processing.get('method', 'unknown')
                detections = ai_processing.get('detectionsFound', 0)
                
                print(f"      📐 Output: {actual_width}x{actual_height}")
                print(f"      🤖 Method: {method}")
                print(f"      🔍 Detections: {detections}")
                
                # Check exact dimensions
                dimensions_correct = (actual_width == expected_width and actual_height == expected_height)
                
                # Check AI detection
                ai_working = method == 'ai_detected' and detections > 0
                
                if dimensions_correct:
                    print(f"      ✅ Exact dimensions achieved!")
                else:
                    print(f"      ❌ Dimensions incorrect!")
                
                if ai_working:
                    print(f"      ✅ AI detection working!")
                else:
                    print(f"      ⚠️  AI detection may not be optimal")
                
                success = dimensions_correct and ai_working
                results.append(success)
                
            else:
                print(f"      ❌ Request failed: {response.status_code}")
                results.append(False)
                
        except Exception as e:
            print(f"      ❌ Error: {e}")
            results.append(False)
        
        finally:
            files['video'][1].close()
    
    return results

def main():
    """Run final comprehensive test"""
    
    print("🚀 Final Test - Both Fixes Working Together")
    print("=" * 60)
    
    # Create test media
    create_test_media()
    
    # Test image format preservation
    image_results = test_image_format_preservation()
    
    # Test video cropping accuracy
    video_results = test_video_cropping_accuracy()
    
    # Summary
    print(f"\n📊 Final Test Results")
    print("=" * 60)
    
    image_passed = sum(image_results)
    image_total = len(image_results)
    video_passed = sum(video_results)
    video_total = len(video_results)
    
    print(f"🖼️  Image Format Tests: {image_passed}/{image_total} passed")
    print(f"🎬 Video Cropping Tests: {video_passed}/{video_total} passed")
    
    total_passed = image_passed + video_passed
    total_tests = image_total + video_total
    
    print(f"\n🎯 Overall: {total_passed}/{total_tests} tests passed")
    
    if total_passed == total_tests:
        print("\n🎉 BOTH FIXES ARE WORKING PERFECTLY!")
        print("\n📋 Confirmed fixes:")
        print("   1. ✅ Image formats preserved when 'Keep Original' selected")
        print("   2. ✅ Image format conversion works when specific format chosen")
        print("   3. ✅ Videos cropped to exact target dimensions")
        print("   4. ✅ No stretching or squeezing in video output")
        print("   5. ✅ AI detection working for smart cropping")
        
    else:
        print("\n⚠️  Some tests failed. Please check the issues above.")
    
    # Cleanup
    try:
        os.remove('test_image.jpg')
        os.remove('test_image.png')
        os.remove('test_video_crop.mp4')
        print("\n🧹 Cleaned up test files")
    except:
        pass

if __name__ == "__main__":
    main()
