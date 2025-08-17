#!/usr/bin/env python3
"""
Test script to simulate image upload and check AI detection results
"""

import requests
import json

def test_image_upload():
    """Test image upload with AI detection"""
    url = 'http://localhost:3000/api/resize-image'
    
    # Test with our realistic face image
    with open('test_face_realistic.jpg', 'rb') as f:
        files = {'image': f}
        data = {
            'platforms': 'instagram-post,facebook-post'  # Test with multiple platforms
        }
        
        try:
            response = requests.post(url, files=files, data=data)
            print(f"Status Code: {response.status_code}")
            print(f"Response: {json.dumps(response.json(), indent=2)}")
            
            if response.status_code == 200:
                result = response.json()
                if 'results' in result:
                    for res in result['results']:
                        if 'aiProcessing' in res:
                            print(f"\nAI Processing Results for {res['dimensions']['name']}:")
                            print(f"  Method: {res['aiProcessing']['method']}")
                            print(f"  Detections: {res['aiProcessing']['detectionsFound']}")
                            print(f"  Confidence: {res['aiProcessing']['confidence']}")
                            print(f"  Crop Method: {res['aiProcessing']['cropMethod']}")
                        else:
                            print(f"\nNo AI processing info for {res['dimensions']['name']}")
            
        except requests.exceptions.ConnectionError:
            print("Error: Could not connect to server. Make sure it's running on port 3000.")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    test_image_upload()
