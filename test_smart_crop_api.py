#!/usr/bin/env python3
"""
Test script for smart cropping API
"""

import requests
import json

def test_smart_crop():
    """Test the smart cropping functionality through the API"""
    
    # Test with our realistic face image
    url = 'http://localhost:3000/api/resize-image'
    
    # Prepare the file and data
    files = {
        'image': ('test_face_realistic.jpg', open('test_face_realistic.jpg', 'rb'), 'image/jpeg')
    }
    
    data = {
        'platform': 'instagram-post',  # 1080x1080
    }
    
    try:
        print("Testing smart crop API...")
        response = requests.post(url, files=files, data=data)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Smart crop API test successful!")
            print(f"📊 AI Processing Results:")
            
            ai_processing = result.get('aiProcessing', {})
            print(f"   Method: {ai_processing.get('method', 'Unknown')}")
            print(f"   Detections Found: {ai_processing.get('detectionsFound', 0)}")
            print(f"   Confidence: {ai_processing.get('confidence', 0):.2f}")
            print(f"   Crop Method: {ai_processing.get('cropMethod', 'Unknown')}")
            
            print(f"📁 Output file: {result.get('filename', 'Unknown')}")
            print(f"📐 Dimensions: {result.get('dimensions', {}).get('width', 0)}x{result.get('dimensions', {}).get('height', 0)}")
            print(f"💾 Original size: {result.get('originalSize', 0)} bytes")
            print(f"💾 Processed size: {result.get('processedSize', 0)} bytes")
            
        else:
            print(f"❌ API test failed with status {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error testing API: {e}")
    
    finally:
        files['image'][1].close()

if __name__ == "__main__":
    test_smart_crop()
