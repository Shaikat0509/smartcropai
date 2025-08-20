#!/usr/bin/env python3
"""
Simple test for Squoosh optimization with smaller images
"""

import requests
import cv2
import numpy as np
import os

def test_simple_optimization():
    """Test with a small image"""
    
    print("🧪 Testing Simple Squoosh Optimization")
    
    # Create a small test image
    img = np.ones((300, 400, 3), dtype=np.uint8) * 200
    cv2.rectangle(img, (50, 50), (350, 250), (255, 100, 100), -1)
    cv2.putText(img, 'SIMPLE TEST', (100, 150), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
    cv2.imwrite('simple_test.jpg', img, [cv2.IMWRITE_JPEG_QUALITY, 90])
    
    original_size = os.path.getsize('simple_test.jpg')
    print(f"   📊 Original size: {original_size:,} bytes")
    
    url = 'http://localhost:3000/api/optimize-convert'
    
    files = {
        'image': ('simple_test.jpg', open('simple_test.jpg', 'rb'), 'image/jpeg')
    }
    
    data = {
        'format': 'original',
        'reduceDimensions': 'false'
    }
    
    try:
        response = requests.post(url, files=files, data=data, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            
            print(f"   ✅ Optimization successful!")
            print(f"   🎨 Format: {result.get('format', 'Unknown')}")
            print(f"   📈 Compression: {result.get('compressionRatio', 'Unknown')}")
            print(f"   🔧 Method: {result.get('optimizationMethod', 'Unknown')}")
            print(f"   💾 Final size: {result.get('processedSize', 0):,} bytes")
            
            return True
        else:
            print(f"   ❌ Request failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False
    
    finally:
        files['image'][1].close()
        try:
            os.remove('simple_test.jpg')
        except:
            pass

def test_cleanup_api():
    """Test cleanup API directly"""
    
    print("\n🧪 Testing Cleanup API")
    
    cleanup_url = 'http://localhost:3000/api/cleanup'
    cleanup_data = {
        'files': [
            {
                'filename': 'test-file.jpg',
                'type': 'optimize'
            }
        ]
    }
    
    try:
        response = requests.post(cleanup_url, json=cleanup_data, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ Cleanup API working!")
            print(f"   📊 Response: {result}")
            return True
        else:
            print(f"   ❌ Cleanup API failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def main():
    """Simple test"""
    
    print("🚀 Simple Test - Squoosh & Cleanup")
    print("=" * 40)
    
    optimization_working = test_simple_optimization()
    cleanup_working = test_cleanup_api()
    
    print(f"\n📊 Results:")
    print(f"   Optimization: {'✅ WORKING' if optimization_working else '❌ FAILED'}")
    print(f"   Cleanup API: {'✅ WORKING' if cleanup_working else '❌ FAILED'}")

if __name__ == "__main__":
    main()
