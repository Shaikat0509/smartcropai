#!/usr/bin/env python3
"""
Test the optimization API directly to verify improvements
"""

import requests
import cv2
import numpy as np
import os

def create_simple_test_image():
    """Create a simple test image"""
    img = np.ones((400, 600, 3), dtype=np.uint8) * 255
    cv2.rectangle(img, (100, 100), (500, 300), (255, 0, 0), -1)
    cv2.circle(img, (300, 200), 80, (0, 255, 0), -1)
    cv2.putText(img, 'TEST GRAPHIC', (150, 250), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
    cv2.imwrite('api_test_graphic.png', img)
    return 'api_test_graphic.png'

def test_api_optimization():
    """Test the API optimization"""
    
    # Create test image
    image_path = create_simple_test_image()
    original_size = os.path.getsize(image_path)
    
    print(f"🧪 Testing API Optimization")
    print(f"📁 Test image: {image_path}")
    print(f"📊 Original size: {original_size:,} bytes")
    
    url = 'http://localhost:3000/api/optimize-convert'
    
    files = {
        'image': (image_path, open(image_path, 'rb'), 'image/png')
    }
    
    data = {
        'format': 'auto',
        'losslessOptimize': 'false',
        'reduceDimensions': 'false'
    }
    
    try:
        response = requests.post(url, files=files, data=data)
        
        if response.status_code == 200:
            result = response.json()
            
            print(f"✅ API Response:")
            print(f"   📈 Compression: {result.get('compressionRatio', 'unknown')}")
            print(f"   💾 Final size: {result.get('processedSize', 0):,} bytes")
            print(f"   🎨 Format: {result.get('format', 'unknown')}")
            print(f"   🔧 Method: {result.get('optimizationMethod', 'unknown')}")
            print(f"   🤖 Professional: {result.get('professionalOptimization', False)}")
            print(f"   🎛️  Quality: {result.get('qualityUsed', 'unknown')}")
            
            # Check if optimization was effective
            processed_size = result.get('processedSize', 0)
            if processed_size > 0 and processed_size < original_size:
                compression = ((original_size - processed_size) / original_size) * 100
                print(f"   🎉 Successful optimization: {compression:.1f}% reduction")
                return True
            else:
                print(f"   ⚠️  Optimization may have failed")
                return False
                
        else:
            print(f"❌ API failed with status {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    finally:
        files['image'][1].close()

if __name__ == "__main__":
    success = test_api_optimization()
    if success:
        print("\n🎉 Professional optimization API is working!")
    else:
        print("\n⚠️  API optimization needs attention")
