#!/usr/bin/env python3
"""
Test script to verify AI models are working correctly
"""

import sys
import os

def test_imports():
    """Test if all required libraries can be imported"""
    print("Testing AI library imports...")
    
    try:
        import cv2
        print("✓ OpenCV imported successfully")
        print(f"  Version: {cv2.__version__}")
    except ImportError as e:
        print(f"✗ OpenCV import failed: {e}")
        return False
    
    try:
        import mediapipe as mp
        print("✓ MediaPipe imported successfully")
        print(f"  Version: {mp.__version__}")
    except ImportError as e:
        print(f"✗ MediaPipe import failed: {e}")
        return False
    
    try:
        from ultralytics import YOLO
        print("✓ YOLOv8 (Ultralytics) imported successfully")
    except ImportError as e:
        print(f"✗ YOLOv8 import failed: {e}")
        return False
    
    try:
        from PIL import Image
        print("✓ Pillow imported successfully")
    except ImportError as e:
        print(f"✗ Pillow import failed: {e}")
        return False
    
    try:
        import numpy as np
        print("✓ NumPy imported successfully")
        print(f"  Version: {np.__version__}")
    except ImportError as e:
        print(f"✗ NumPy import failed: {e}")
        return False
    
    return True

def test_models():
    """Test if AI models can be loaded"""
    print("\nTesting AI model loading...")
    
    try:
        import mediapipe as mp
        
        # Test MediaPipe Face Detection
        mp_face_detection = mp.solutions.face_detection
        face_detection = mp_face_detection.FaceDetection(
            model_selection=1, min_detection_confidence=0.5
        )
        print("✓ MediaPipe Face Detection model loaded")
        
        # Test MediaPipe Pose
        mp_pose = mp.solutions.pose
        pose = mp_pose.Pose(
            static_image_mode=True, min_detection_confidence=0.5
        )
        print("✓ MediaPipe Pose model loaded")
        
        # Test MediaPipe Hands
        mp_hands = mp.solutions.hands
        hands = mp_hands.Hands(
            static_image_mode=True, max_num_hands=2, min_detection_confidence=0.5
        )
        print("✓ MediaPipe Hands model loaded")
        
    except Exception as e:
        print(f"✗ MediaPipe model loading failed: {e}")
        return False
    
    try:
        from ultralytics import YOLO
        
        # Test YOLOv8 model loading (this will download the model if not present)
        print("Loading YOLOv8 model (this may take a moment on first run)...")
        model = YOLO('yolov8n.pt')
        print("✓ YOLOv8 model loaded successfully")
        print(f"  Model classes: {len(model.names)} classes")
        
    except Exception as e:
        print(f"✗ YOLOv8 model loading failed: {e}")
        return False
    
    return True

def test_opencv_features():
    """Test OpenCV features"""
    print("\nTesting OpenCV features...")
    
    try:
        import cv2
        
        # Test Haar cascade loading
        face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )
        if face_cascade.empty():
            print("✗ OpenCV Haar cascade loading failed")
            return False
        else:
            print("✓ OpenCV Haar cascade loaded")
        
        # Test basic image operations
        import numpy as np
        test_image = np.zeros((100, 100, 3), dtype=np.uint8)
        gray = cv2.cvtColor(test_image, cv2.COLOR_BGR2GRAY)
        print("✓ OpenCV image operations working")
        
    except Exception as e:
        print(f"✗ OpenCV features test failed: {e}")
        return False
    
    return True

def test_advanced_processor():
    """Test the advanced media processor"""
    print("\nTesting Advanced Media Processor...")
    
    try:
        from server.advanced_media_processor import AdvancedMediaProcessor
        
        processor = AdvancedMediaProcessor()
        print("✓ AdvancedMediaProcessor initialized successfully")
        
        # Check if models are loaded
        if processor.yolo_model:
            print("✓ YOLOv8 model loaded in processor")
        else:
            print("⚠ YOLOv8 model not loaded in processor")
        
        if processor.face_detection:
            print("✓ MediaPipe face detection loaded in processor")
        else:
            print("⚠ MediaPipe face detection not loaded in processor")
        
    except Exception as e:
        print(f"✗ Advanced Media Processor test failed: {e}")
        return False
    
    return True

def main():
    """Run all tests"""
    print("🤖 AI Models Test Suite")
    print("=" * 50)
    
    success = True
    
    # Test imports
    if not test_imports():
        success = False
    
    # Test model loading
    if not test_models():
        success = False
    
    # Test OpenCV features
    if not test_opencv_features():
        success = False
    
    # Test advanced processor
    if not test_advanced_processor():
        success = False
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 All tests passed! AI models are ready for use.")
        print("\nYour SmartCrop AI application is fully configured with:")
        print("- YOLOv8 object detection")
        print("- MediaPipe face/pose/hand detection")
        print("- OpenCV computer vision")
        print("- Advanced smart cropping algorithms")
    else:
        print("❌ Some tests failed. Please check the installation.")
        print("\nTo fix issues:")
        print("1. Install missing dependencies: pip install opencv-python mediapipe ultralytics pillow numpy")
        print("2. Check Python version (3.8+ required)")
        print("3. Ensure stable internet connection for model downloads")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
