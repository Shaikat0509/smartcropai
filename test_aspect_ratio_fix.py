#!/usr/bin/env python3
"""
Test to verify that images are properly cropped without stretching/squeezing
"""

import requests
import cv2
import numpy as np
from PIL import Image

def create_test_pattern():
    """Create a test image with clear geometric patterns to detect stretching"""
    
    # Create a 600x400 image with clear geometric patterns
    img = np.ones((400, 600, 3), dtype=np.uint8) * 255
    
    # Draw perfect circles that should remain circular
    cv2.circle(img, (150, 200), 80, (255, 0, 0), 3)  # Red circle
    cv2.circle(img, (450, 200), 80, (0, 255, 0), 3)  # Green circle
    
    # Draw perfect squares that should remain square
    cv2.rectangle(img, (50, 100), (130, 180), (0, 0, 255), 3)  # Blue square
    cv2.rectangle(img, (470, 120), (550, 200), (255, 0, 255), 3)  # Magenta square
    
    # Draw grid lines for reference
    for x in range(0, 600, 50):
        cv2.line(img, (x, 0), (x, 400), (128, 128, 128), 1)
    for y in range(0, 400, 50):
        cv2.line(img, (0, y), (600, y), (128, 128, 128), 1)
    
    # Add text to show orientation
    cv2.putText(img, 'ORIGINAL 600x400', (200, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
    cv2.putText(img, 'Aspect Ratio Test', (180, 350), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
    
    cv2.imwrite('test_aspect_pattern.jpg', img)
    print("✅ Created test pattern image (600x400)")

def test_aspect_ratio_preservation():
    """Test that cropping preserves aspect ratios correctly"""
    
    create_test_pattern()
    
    # Test different target aspect ratios
    test_cases = [
        ('instagram-post', 1080, 1080, 'Square (1:1)'),
        ('youtube-thumbnail', 1280, 720, 'Landscape (16:9)'),
        ('instagram-story', 1080, 1920, 'Portrait (9:16)'),
    ]
    
    results = []
    
    for platform, expected_width, expected_height, description in test_cases:
        print(f"\n🧪 Testing {description} - {platform}")
        
        url = 'http://localhost:3000/api/resize-image'
        
        files = {
            'image': ('test_aspect_pattern.jpg', open('test_aspect_pattern.jpg', 'rb'), 'image/jpeg')
        }
        
        data = {
            'platform': platform,
        }
        
        try:
            response = requests.post(url, files=files, data=data)
            
            if response.status_code == 200:
                result = response.json()
                filename = result.get('filename')
                
                # Download and analyze the result
                download_url = f"http://localhost:3000/api/download/images/{filename}"
                img_response = requests.get(download_url)
                
                if img_response.status_code == 200:
                    # Save the result for inspection
                    output_filename = f"test_result_{platform}.jpg"
                    with open(output_filename, 'wb') as f:
                        f.write(img_response.content)
                    
                    # Check dimensions
                    img = Image.open(output_filename)
                    actual_width, actual_height = img.size
                    
                    # Verify dimensions
                    width_correct = actual_width == expected_width
                    height_correct = actual_height == expected_height
                    
                    # Calculate aspect ratios
                    expected_ratio = expected_width / expected_height
                    actual_ratio = actual_width / actual_height
                    ratio_correct = abs(expected_ratio - actual_ratio) < 0.01
                    
                    if width_correct and height_correct and ratio_correct:
                        print(f"   ✅ Dimensions: {actual_width}x{actual_height} (Expected: {expected_width}x{expected_height})")
                        print(f"   ✅ Aspect ratio: {actual_ratio:.3f} (Expected: {expected_ratio:.3f})")
                        print(f"   📁 Saved as: {output_filename}")
                        results.append((description, True))
                    else:
                        print(f"   ❌ Dimensions: {actual_width}x{actual_height} (Expected: {expected_width}x{expected_height})")
                        print(f"   ❌ Aspect ratio: {actual_ratio:.3f} (Expected: {expected_ratio:.3f})")
                        results.append((description, False))
                else:
                    print(f"   ❌ Failed to download result image")
                    results.append((description, False))
            else:
                print(f"   ❌ API request failed: {response.status_code}")
                results.append((description, False))
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
            results.append((description, False))
        
        finally:
            files['image'][1].close()
    
    # Summary
    print(f"\n📊 Aspect Ratio Test Results:")
    print(f"=" * 50)
    
    successful = sum(1 for _, success in results if success)
    total = len(results)
    
    for description, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"   {status} {description}")
    
    print(f"\n🎯 Overall: {successful}/{total} tests passed")
    
    if successful == total:
        print("🎉 All aspect ratio tests passed! Images are properly cropped without stretching.")
        print("📁 Check the test_result_*.jpg files to visually verify the results.")
    else:
        print("⚠️  Some tests failed. Images may still be stretched or squeezed.")

if __name__ == "__main__":
    test_aspect_ratio_preservation()
