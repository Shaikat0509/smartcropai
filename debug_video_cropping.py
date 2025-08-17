#!/usr/bin/env python3
"""
Debug video cropping to see what's actually happening
"""

import cv2
import numpy as np
import os
import sys
sys.path.append('server')
from advanced_video_processor import AdvancedVideoProcessor

def create_debug_video():
    """Create a test video with clear visual markers"""
    print("📹 Creating debug video...")
    
    # Video properties - landscape video
    width, height = 1920, 1080  # Full HD landscape
    fps = 10
    duration = 2  # seconds
    total_frames = fps * duration
    
    # Create video writer
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter('debug_video.mp4', fourcc, fps, (width, height))
    
    for frame_num in range(total_frames):
        # Create frame with grid and markers
        frame = np.zeros((height, width, 3), dtype=np.uint8)
        
        # Add background gradient
        for y in range(height):
            intensity = int(50 + (y / height) * 100)
            frame[y, :] = [intensity, intensity//2, intensity//3]
        
        # Add grid lines every 100 pixels
        for x in range(0, width, 100):
            cv2.line(frame, (x, 0), (x, height), (100, 100, 100), 1)
        for y in range(0, height, 100):
            cv2.line(frame, (0, y), (width, y), (100, 100, 100), 1)
        
        # Add corner markers
        cv2.rectangle(frame, (0, 0), (100, 100), (255, 0, 0), -1)  # Top-left: Red
        cv2.rectangle(frame, (width-100, 0), (width, 100), (0, 255, 0), -1)  # Top-right: Green
        cv2.rectangle(frame, (0, height-100), (100, height), (0, 0, 255), -1)  # Bottom-left: Blue
        cv2.rectangle(frame, (width-100, height-100), (width, height), (255, 255, 0), -1)  # Bottom-right: Yellow
        
        # Add center marker
        center_x, center_y = width // 2, height // 2
        cv2.circle(frame, (center_x, center_y), 50, (255, 255, 255), -1)
        cv2.putText(frame, 'CENTER', (center_x-50, center_y+10), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
        
        # Add moving face
        progress = frame_num / total_frames
        face_x = int(400 + progress * 800)  # Move from left to right
        face_y = int(height * 0.3)  # Upper third
        
        # Draw face
        cv2.circle(frame, (face_x, face_y), 60, (255, 220, 177), -1)  # Face
        cv2.circle(frame, (face_x-20, face_y-15), 8, (0, 0, 0), -1)  # Left eye
        cv2.circle(frame, (face_x+20, face_y-15), 8, (0, 0, 0), -1)  # Right eye
        cv2.ellipse(frame, (face_x, face_y+20), (25, 12), 0, 0, 180, (0, 0, 0), 2)  # Mouth
        
        # Add dimension labels
        cv2.putText(frame, f'{width}x{height}', (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        cv2.putText(frame, f'Frame {frame_num+1}', (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        cv2.putText(frame, f'Face at ({face_x}, {face_y})', (50, 150), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        
        out.write(frame)
    
    out.release()
    print(f"✅ Debug video created: {width}x{height}")

def debug_video_analysis():
    """Debug the video analysis process"""
    print("\n🔍 Debugging video analysis...")
    
    processor = AdvancedVideoProcessor()
    
    # Test different target dimensions
    test_cases = [
        (1080, 1920, "Portrait 9:16 (Instagram Reel)"),
        (1920, 1080, "Landscape 16:9 (YouTube)"),
        (1080, 1080, "Square 1:1 (Instagram Post)"),
    ]
    
    for target_width, target_height, description in test_cases:
        print(f"\n📐 Testing {description} ({target_width}x{target_height})")
        
        # Analyze video
        analysis = processor.analyze_video_content(
            'debug_video.mp4', 
            target_width=target_width, 
            target_height=target_height
        )
        
        if analysis:
            video_info = analysis['video_info']
            optimal_crop = analysis['optimal_crop']
            
            print(f"   📹 Original: {video_info['width']}x{video_info['height']}")
            print(f"   🎯 Target: {target_width}x{target_height}")
            print(f"   ✂️  Crop: {optimal_crop['width']}x{optimal_crop['height']} at ({optimal_crop['x']}, {optimal_crop['y']})")
            print(f"   🤖 Method: {optimal_crop['method']}")
            print(f"   🔍 Detections: {analysis['detections']}")
            
            # Calculate aspect ratios
            original_ratio = video_info['width'] / video_info['height']
            target_ratio = target_width / target_height
            crop_ratio = optimal_crop['width'] / optimal_crop['height']
            
            print(f"   📊 Original ratio: {original_ratio:.3f}")
            print(f"   📊 Target ratio: {target_ratio:.3f}")
            print(f"   📊 Crop ratio: {crop_ratio:.3f}")
            
            # Check if crop ratio matches target ratio
            ratio_match = abs(crop_ratio - target_ratio) < 0.01
            print(f"   ✅ Ratio match: {'Yes' if ratio_match else 'No'}")
            
            if not ratio_match:
                print(f"   ⚠️  Crop ratio ({crop_ratio:.3f}) doesn't match target ratio ({target_ratio:.3f})")
        else:
            print(f"   ❌ Analysis failed")

def test_actual_video_processing():
    """Test actual video processing"""
    print("\n🎬 Testing actual video processing...")
    
    processor = AdvancedVideoProcessor()
    
    # Test Instagram Reel format
    target_width, target_height = 1080, 1920
    output_path = 'debug_output.mp4'
    
    try:
        result = processor.process_video(
            'debug_video.mp4',
            output_path,
            target_width,
            target_height,
            quality='medium',
            compress=False
        )
        
        if result['success']:
            print(f"   ✅ Processing successful!")
            print(f"   🤖 Method: {result['crop_method']}")
            print(f"   🔍 Detections: {result['detections_found']}")
            
            # Check output video dimensions
            if os.path.exists(output_path):
                cap = cv2.VideoCapture(output_path)
                if cap.isOpened():
                    actual_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                    actual_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                    cap.release()
                    
                    print(f"   📐 Output dimensions: {actual_width}x{actual_height}")
                    
                    if actual_width == target_width and actual_height == target_height:
                        print(f"   ✅ Dimensions match target exactly!")
                    else:
                        print(f"   ❌ Dimensions don't match target ({target_width}x{target_height})")
                else:
                    print(f"   ❌ Could not read output video")
            else:
                print(f"   ❌ Output file not created")
        else:
            print(f"   ❌ Processing failed")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")

def main():
    """Run debug tests"""
    print("🐛 Video Cropping Debug Tool")
    print("=" * 50)
    
    # Create debug video
    create_debug_video()
    
    # Debug analysis
    debug_video_analysis()
    
    # Test actual processing
    test_actual_video_processing()
    
    # Cleanup
    try:
        os.remove('debug_video.mp4')
        os.remove('debug_output.mp4')
        print("\n🧹 Cleaned up debug files")
    except:
        pass

if __name__ == "__main__":
    main()
