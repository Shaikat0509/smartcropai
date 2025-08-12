#!/usr/bin/env python3
"""
Advanced Media Processing Module
Uses OpenCV, Pillow, and FFmpeg for intelligent media resizing and optimization
"""

import cv2
import numpy as np
from PIL import Image, ImageEnhance
import json
import sys
import os
import subprocess
from pathlib import Path

def detect_subject_opencv(image_path):
    """
    Use OpenCV for subject detection using Haar cascades and contour detection
    """
    try:
        # Read image
        img = cv2.imread(image_path)
        if img is None:
            return None
            
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        h, w = img.shape[:2]
        
        # Try face detection first
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        faces = face_cascade.detectMultiScale(gray, 1.1, 4)
        
        if len(faces) > 0:
            # Return the largest face as the main subject
            largest_face = max(faces, key=lambda x: x[2] * x[3])
            x, y, fw, fh = largest_face
            
            # Add some padding around face
            padding = 0.3
            px = max(0, int(x - fw * padding))
            py = max(0, int(y - fh * padding))
            pw = min(w - px, int(fw * (1 + 2 * padding)))
            ph = min(h - py, int(fh * (1 + 2 * padding)))
            
            return {
                'main_subject': 'Human face detected',
                'bounding_box': {
                    'x': (px / w) * 100,
                    'y': (py / h) * 100,
                    'width': (pw / w) * 100,
                    'height': (ph / h) * 100
                },
                'focal_points': [{'x': (x + fw/2) / w * 100, 'y': (y + fh/2) / h * 100}],
                'confidence': 0.9
            }
        
        # If no faces, try edge detection for prominent objects
        edges = cv2.Canny(gray, 50, 150)
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if contours:
            # Find the largest contour
            largest_contour = max(contours, key=cv2.contourArea)
            x, y, cw, ch = cv2.boundingRect(largest_contour)
            
            # Only consider if it's a significant portion of the image
            if (cw * ch) > (w * h * 0.1):
                return {
                    'main_subject': 'Main object detected',
                    'bounding_box': {
                        'x': (x / w) * 100,
                        'y': (y / h) * 100,
                        'width': (cw / w) * 100,
                        'height': (ch / h) * 100
                    },
                    'focal_points': [{'x': (x + cw/2) / w * 100, 'y': (y + ch/2) / h * 100}],
                    'confidence': 0.7
                }
        
        # Default to center crop
        return {
            'main_subject': 'Center composition',
            'bounding_box': {
                'x': 25,
                'y': 25,
                'width': 50,
                'height': 50
            },
            'focal_points': [{'x': 50, 'y': 50}],
            'confidence': 0.5
        }
        
    except Exception as e:
        print(f"Error in subject detection: {e}", file=sys.stderr)
        return None

def smart_crop_image(input_path, output_path, target_width, target_height, subject_analysis=None):
    """
    Smart crop using Pillow with subject analysis
    """
    try:
        with Image.open(input_path) as img:
            original_width, original_height = img.size
            target_ratio = target_width / target_height
            original_ratio = original_width / original_height
            
            if subject_analysis and subject_analysis.get('bounding_box'):
                bbox = subject_analysis['bounding_box']
                
                # Calculate subject center
                subject_x = (bbox['x'] + bbox['width'] / 2) / 100 * original_width
                subject_y = (bbox['y'] + bbox['height'] / 2) / 100 * original_height
                
                # Calculate crop dimensions
                if target_ratio > original_ratio:
                    # Target is wider, crop height
                    crop_width = original_width
                    crop_height = int(crop_width / target_ratio)
                    
                    # Center crop vertically around subject
                    crop_y = max(0, min(original_height - crop_height, 
                                      int(subject_y - crop_height / 2)))
                    crop_x = 0
                else:
                    # Target is taller, crop width
                    crop_height = original_height
                    crop_width = int(crop_height * target_ratio)
                    
                    # Center crop horizontally around subject
                    crop_x = max(0, min(original_width - crop_width, 
                                      int(subject_x - crop_width / 2)))
                    crop_y = 0
                
                # Crop the image
                cropped = img.crop((crop_x, crop_y, crop_x + crop_width, crop_y + crop_height))
            else:
                # Fallback to center crop
                if target_ratio > original_ratio:
                    crop_width = original_width
                    crop_height = int(crop_width / target_ratio)
                    crop_x = 0
                    crop_y = (original_height - crop_height) // 2
                else:
                    crop_height = original_height
                    crop_width = int(crop_height * target_ratio)
                    crop_x = (original_width - crop_width) // 2
                    crop_y = 0
                
                cropped = img.crop((crop_x, crop_y, crop_x + crop_width, crop_y + crop_height))
            
            # Resize to target dimensions
            resized = cropped.resize((target_width, target_height), Image.Resampling.LANCZOS)
            
            # Enhance image quality
            enhancer = ImageEnhance.Sharpness(resized)
            enhanced = enhancer.enhance(1.1)
            
            # Save with optimization
            enhanced.save(output_path, 'JPEG', quality=85, optimize=True, progressive=True)
            
            return True
            
    except Exception as e:
        print(f"Error in image processing: {e}", file=sys.stderr)
        return False

def process_video_ffmpeg(input_path, output_path, target_width, target_height, subject_analysis=None):
    """
    Process video using FFmpeg with smart cropping
    """
    try:
        # Get video info
        probe_cmd = [
            'ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_format', '-show_streams', input_path
        ]
        result = subprocess.run(probe_cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            return False
            
        video_info = json.loads(result.stdout)
        video_stream = next((s for s in video_info['streams'] if s['codec_type'] == 'video'), None)
        
        if not video_stream:
            return False
            
        original_width = int(video_stream['width'])
        original_height = int(video_stream['height'])
        
        # Calculate smart crop parameters
        target_ratio = target_width / target_height
        original_ratio = original_width / original_height
        
        if subject_analysis and subject_analysis.get('bounding_box'):
            bbox = subject_analysis['bounding_box']
            subject_x = int((bbox['x'] + bbox['width'] / 2) / 100 * original_width)
            subject_y = int((bbox['y'] + bbox['height'] / 2) / 100 * original_height)
        else:
            subject_x = original_width // 2
            subject_y = original_height // 2
        
        # Build FFmpeg command with smart cropping
        if target_ratio > original_ratio:
            # Crop height, keep width
            crop_width = original_width
            crop_height = int(crop_width / target_ratio)
            crop_x = 0
            crop_y = max(0, min(original_height - crop_height, subject_y - crop_height // 2))
        else:
            # Crop width, keep height
            crop_height = original_height
            crop_width = int(crop_height * target_ratio)
            crop_y = 0
            crop_x = max(0, min(original_width - crop_width, subject_x - crop_width // 2))
        
        ffmpeg_cmd = [
            'ffmpeg', '-i', input_path,
            '-vf', f'crop={crop_width}:{crop_height}:{crop_x}:{crop_y},scale={target_width}:{target_height}',
            '-c:v', 'libx264', '-preset', 'fast', '-crf', '23',
            '-c:a', 'aac', '-b:a', '128k',
            '-movflags', '+faststart',
            '-y', output_path
        ]
        
        result = subprocess.run(ffmpeg_cmd, capture_output=True, text=True)
        return result.returncode == 0
        
    except Exception as e:
        print(f"Error in video processing: {e}", file=sys.stderr)
        return False

def main():
    if len(sys.argv) < 6:
        print("Usage: python media_processor.py <input_path> <output_path> <width> <height> <media_type> [subject_analysis_json]")
        sys.exit(1)
    
    input_path = sys.argv[1]
    output_path = sys.argv[2]
    width = int(sys.argv[3])
    height = int(sys.argv[4])
    media_type = sys.argv[5]
    
    subject_analysis = None
    if len(sys.argv) > 6:
        try:
            subject_analysis = json.loads(sys.argv[6])
        except:
            pass
    
    # Create output directory if it doesn't exist
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    if media_type == 'image':
        # First try to detect subject if not provided
        if not subject_analysis:
            subject_analysis = detect_subject_opencv(input_path)
            
        success = smart_crop_image(input_path, output_path, width, height, subject_analysis)
    elif media_type == 'video':
        success = process_video_ffmpeg(input_path, output_path, width, height, subject_analysis)
    else:
        print(f"Unsupported media type: {media_type}", file=sys.stderr)
        sys.exit(1)
    
    if success:
        print(json.dumps({
            'success': True,
            'output_path': output_path,
            'subject_analysis': subject_analysis
        }))
    else:
        print(json.dumps({
            'success': False,
            'error': 'Processing failed'
        }))
        sys.exit(1)

if __name__ == '__main__':
    main()