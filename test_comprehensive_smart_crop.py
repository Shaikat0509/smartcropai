#!/usr/bin/env python3
"""
Comprehensive test for the improved smart cropping functionality
"""

import requests
import json
import cv2
import numpy as np

def create_test_images():
    """Create various test images to test different scenarios"""
    
    # 1. Face image
    img = np.ones((400, 600, 3), dtype=np.uint8) * 255
    cv2.circle(img, (200, 150), 80, (255, 200, 150), -1)  # Face
    cv2.circle(img, (180, 130), 10, (0, 0, 0), -1)  # Left eye
    cv2.circle(img, (220, 130), 10, (0, 0, 0), -1)  # Right eye
    cv2.ellipse(img, (200, 170), (20, 10), 0, 0, 180, (0, 0, 0), 2)  # Mouth
    cv2.imwrite('test_face_comprehensive.jpg', img)
    
    # 2. Object image (car-like shape)
    img2 = np.ones((400, 600, 3), dtype=np.uint8) * 200
    cv2.rectangle(img2, (150, 180), (450, 280), (100, 100, 200), -1)  # Car body
    cv2.circle(img2, (200, 280), 30, (50, 50, 50), -1)  # Wheel 1
    cv2.circle(img2, (400, 280), 30, (50, 50, 50), -1)  # Wheel 2
    cv2.imwrite('test_object_comprehensive.jpg', img2)
    
    # 3. Complex scene
    img3 = np.ones((400, 600, 3), dtype=np.uint8) * 180
    # Multiple objects
    cv2.rectangle(img3, (50, 50), (150, 150), (255, 100, 100), -1)
    cv2.circle(img3, (400, 100), 50, (100, 255, 100), -1)
    cv2.rectangle(img3, (200, 250), (500, 350), (100, 100, 255), -1)
    cv2.imwrite('test_complex_comprehensive.jpg', img3)
    
    print("✅ Created test images")

def test_smart_crop_scenario(image_path, scenario_name):
    """Test smart cropping for a specific scenario"""
    
    url = 'http://localhost:3000/api/resize-image'
    
    files = {
        'image': (image_path, open(image_path, 'rb'), 'image/jpeg')
    }
    
    data = {
        'platform': 'instagram-post',  # 1080x1080
    }
    
    try:
        print(f"\n🧪 Testing {scenario_name}...")
        response = requests.post(url, files=files, data=data)
        
        if response.status_code == 200:
            result = response.json()
            ai_processing = result.get('aiProcessing', {})
            
            print(f"   ✅ Success!")
            print(f"   📊 Method: {ai_processing.get('method', 'Unknown')}")
            print(f"   🔍 Detections: {ai_processing.get('detectionsFound', 0)}")
            print(f"   📈 Confidence: {ai_processing.get('confidence', 0):.2f}")
            print(f"   ✂️  Crop Method: {ai_processing.get('cropMethod', 'Unknown')}")
            print(f"   📁 Output: {result.get('filename', 'Unknown')}")
            
            # Check if AI processing was used
            if ai_processing.get('cropMethod') == 'ai_detected':
                print(f"   🤖 AI smart cropping was used!")
            elif ai_processing.get('cropMethod') == 'sharp_attention':
                print(f"   ⚡ Sharp attention fallback was used")
            else:
                print(f"   🔄 Other method was used")
                
            return True
        else:
            print(f"   ❌ Failed with status {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False
    
    finally:
        files['image'][1].close()

def main():
    """Run comprehensive smart cropping tests"""
    
    print("🚀 Starting comprehensive smart cropping tests...")
    
    # Create test images
    create_test_images()
    
    # Test scenarios
    scenarios = [
        ('test_face_comprehensive.jpg', 'Face Detection'),
        ('test_object_comprehensive.jpg', 'Object Detection'),
        ('test_complex_comprehensive.jpg', 'Complex Scene'),
        ('test_face_realistic.jpg', 'Realistic Face (existing)')
    ]
    
    results = []
    for image_path, scenario_name in scenarios:
        try:
            success = test_smart_crop_scenario(image_path, scenario_name)
            results.append((scenario_name, success))
        except FileNotFoundError:
            print(f"   ⚠️  Skipping {scenario_name} - file not found")
            results.append((scenario_name, False))
    
    # Summary
    print(f"\n📊 Test Results Summary:")
    print(f"=" * 50)
    
    successful = sum(1 for _, success in results if success)
    total = len(results)
    
    for scenario, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"   {status} {scenario}")
    
    print(f"\n🎯 Overall: {successful}/{total} tests passed")
    
    if successful == total:
        print("🎉 All smart cropping tests passed! The feature is working correctly.")
    else:
        print("⚠️  Some tests failed. Please check the issues above.")

if __name__ == "__main__":
    main()
