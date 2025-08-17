#!/usr/bin/env python3
"""
Advanced Video Processor with AI Detection and Smart Cropping
Uses YOLOv8, MediaPipe, OpenCV, and FFmpeg for professional video processing
"""

import cv2
import numpy as np
import subprocess
import sys
import os
import json
import logging
import tempfile
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    from ultralytics import YOLO
    import mediapipe as mp
    YOLO_AVAILABLE = True
    MEDIAPIPE_AVAILABLE = True
except ImportError as e:
    YOLO_AVAILABLE = False
    MEDIAPIPE_AVAILABLE = False
    logger.warning(f"AI libraries not available: {e}")

class AdvancedVideoProcessor:
    def __init__(self):
        """Initialize the advanced video processor with AI models"""
        self.yolo_model = None
        self.face_detection = None
        self.pose = None
        
        # Initialize YOLOv8 if available
        if YOLO_AVAILABLE:
            try:
                self.yolo_model = YOLO('yolov8n.pt')
                logger.info("YOLOv8 model loaded successfully")
            except Exception as e:
                logger.warning(f"Failed to load YOLOv8: {e}")
        
        # Initialize MediaPipe if available
        if MEDIAPIPE_AVAILABLE:
            try:
                mp_face_detection = mp.solutions.face_detection
                mp_pose = mp.solutions.pose
                self.face_detection = mp_face_detection.FaceDetection(
                    model_selection=1, min_detection_confidence=0.5
                )
                self.pose = mp_pose.Pose(
                    static_image_mode=True, min_detection_confidence=0.5
                )
                logger.info("MediaPipe models loaded successfully")
            except Exception as e:
                logger.warning(f"Failed to load MediaPipe: {e}")

    def check_ffmpeg(self):
        """Check if FFmpeg is available"""
        try:
            subprocess.run(['ffmpeg', '-version'], 
                         capture_output=True, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False

    def analyze_video_content(self, video_path, sample_frames=10, target_width=None, target_height=None):
        """
        Analyze video content to determine optimal crop area
        Samples frames throughout the video for consistent detection
        """
        try:
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                raise ValueError(f"Could not open video: {video_path}")
            
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
            # Sample frames evenly throughout the video
            frame_indices = np.linspace(0, total_frames - 1, sample_frames, dtype=int)
            
            all_detections = []
            
            for frame_idx in frame_indices:
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
                ret, frame = cap.read()
                
                if not ret:
                    continue
                
                # Analyze this frame
                detections = self._analyze_frame(frame)
                if detections:
                    all_detections.extend(detections)
            
            cap.release()
            
            # Determine optimal crop area from all detections
            optimal_crop = self._calculate_optimal_crop(all_detections, width, height, target_width, target_height)
            
            return {
                'video_info': {
                    'width': width,
                    'height': height,
                    'fps': fps,
                    'total_frames': total_frames,
                    'duration': total_frames / fps if fps > 0 else 0
                },
                'detections': len(all_detections),
                'optimal_crop': optimal_crop
            }
            
        except Exception as e:
            logger.error(f"Video analysis failed: {e}")
            return None

    def _analyze_frame(self, frame):
        """Analyze a single frame for subjects"""
        detections = []
        h, w = frame.shape[:2]
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Face detection with MediaPipe
        if self.face_detection:
            try:
                results = self.face_detection.process(rgb_frame)
                if results.detections:
                    for detection in results.detections:
                        bbox = detection.location_data.relative_bounding_box
                        detections.append({
                            'type': 'face',
                            'confidence': detection.score[0],
                            'x': bbox.xmin * w,
                            'y': bbox.ymin * h,
                            'width': bbox.width * w,
                            'height': bbox.height * h,
                            'center_x': (bbox.xmin + bbox.width/2) * w,
                            'center_y': (bbox.ymin + bbox.height/2) * h
                        })
            except Exception as e:
                logger.warning(f"Face detection failed: {e}")
        
        # Object detection with YOLOv8
        if self.yolo_model:
            try:
                results = self.yolo_model(frame, verbose=False)
                for result in results:
                    boxes = result.boxes
                    if boxes is not None:
                        for box in boxes:
                            x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                            conf = box.conf[0].cpu().numpy()
                            cls = int(box.cls[0].cpu().numpy())
                            
                            # Focus on people and important objects
                            class_name = self.yolo_model.names[cls]
                            if class_name in ['person', 'car', 'dog', 'cat', 'bird'] and conf > 0.5:
                                detections.append({
                                    'type': f'object_{class_name}',
                                    'confidence': float(conf),
                                    'x': float(x1),
                                    'y': float(y1),
                                    'width': float(x2 - x1),
                                    'height': float(y2 - y1),
                                    'center_x': float((x1 + x2) / 2),
                                    'center_y': float((y1 + y2) / 2)
                                })
            except Exception as e:
                logger.warning(f"Object detection failed: {e}")
        
        # Fallback: OpenCV face detection
        if not detections:
            try:
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                face_cascade = cv2.CascadeClassifier(
                    cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
                )
                faces = face_cascade.detectMultiScale(gray, 1.1, 4)
                
                for (x, y, fw, fh) in faces:
                    detections.append({
                        'type': 'face_opencv',
                        'confidence': 0.7,
                        'x': float(x),
                        'y': float(y),
                        'width': float(fw),
                        'height': float(fh),
                        'center_x': float(x + fw/2),
                        'center_y': float(y + fh/2)
                    })
            except Exception as e:
                logger.warning(f"OpenCV face detection failed: {e}")
        
        return detections

    def _calculate_optimal_crop(self, detections, video_width, video_height, target_width=None, target_height=None):
        """Calculate optimal crop area from all detections with proper aspect ratio handling"""
        # Calculate target aspect ratio if provided
        target_ratio = None
        if target_width and target_height:
            target_ratio = target_width / target_height

        if not detections:
            # Default to center crop with target aspect ratio
            if target_ratio:
                original_ratio = video_width / video_height
                if target_ratio > original_ratio:
                    # Target is wider - use full width, crop height
                    crop_width = video_width
                    crop_height = int(crop_width / target_ratio)
                    crop_x = 0
                    crop_y = max(0, (video_height - crop_height) // 2)
                else:
                    # Target is taller - use full height, crop width
                    crop_height = video_height
                    crop_width = int(crop_height * target_ratio)
                    crop_y = 0
                    crop_x = max(0, (video_width - crop_width) // 2)
            else:
                # Default center crop
                crop_width = int(video_width * 0.8)
                crop_height = int(video_height * 0.8)
                crop_x = (video_width - crop_width) // 2
                crop_y = (video_height - crop_height) // 2

            return {
                'x': crop_x,
                'y': crop_y,
                'width': crop_width,
                'height': crop_height,
                'method': 'center_fallback'
            }
        
        # Weight detections by confidence and type
        weighted_centers = []
        for det in detections:
            weight = det['confidence']
            if det['type'].startswith('face'):
                weight *= 2.0  # Prioritize faces
            elif det['type'].startswith('object_person'):
                weight *= 1.5  # Prioritize people
            
            weighted_centers.append({
                'x': det['center_x'],
                'y': det['center_y'],
                'weight': weight
            })
        
        # Calculate weighted center
        total_weight = sum(c['weight'] for c in weighted_centers)
        if total_weight == 0:
            center_x = video_width / 2
            center_y = video_height / 2
        else:
            center_x = sum(c['x'] * c['weight'] for c in weighted_centers) / total_weight
            center_y = sum(c['y'] * c['weight'] for c in weighted_centers) / total_weight
        
        # Calculate bounding box that includes all important detections
        min_x = min(det['x'] for det in detections)
        max_x = max(det['x'] + det['width'] for det in detections)
        min_y = min(det['y'] for det in detections)
        max_y = max(det['y'] + det['height'] for det in detections)

        # Add padding around detections
        detection_width = max_x - min_x
        detection_height = max_y - min_y
        padding_x = max(detection_width * 0.5, video_width * 0.1)
        padding_y = max(detection_height * 0.5, video_height * 0.1)

        # Calculate crop area with target aspect ratio
        if target_ratio:
            # We need to crop to exactly match the target aspect ratio
            # Start by determining the maximum possible crop area that fits the target ratio

            # Option 1: Use full width, calculate height
            option1_width = video_width
            option1_height = option1_width / target_ratio

            # Option 2: Use full height, calculate width
            option2_height = video_height
            option2_width = option2_height * target_ratio

            # Choose the option that fits within the video bounds
            if option1_height <= video_height:
                # Use full width
                crop_width = option1_width
                crop_height = option1_height
                crop_x = 0
                # Center around weighted center vertically
                crop_y = center_y - crop_height / 2
                crop_y = max(0, min(crop_y, video_height - crop_height))
            else:
                # Use full height
                crop_width = option2_width
                crop_height = option2_height
                crop_y = 0
                # Center around weighted center horizontally
                crop_x = center_x - crop_width / 2
                crop_x = max(0, min(crop_x, video_width - crop_width))

        else:
            # No target ratio, use detection area plus padding
            crop_x = min_x - padding_x
            crop_y = min_y - padding_y
            crop_width = detection_width + 2 * padding_x
            crop_height = detection_height + 2 * padding_y

        # Ensure crop area is within video bounds
        crop_x = max(0, min(crop_x, video_width - crop_width))
        crop_y = max(0, min(crop_y, video_height - crop_height))
        crop_width = min(crop_width, video_width - crop_x)
        crop_height = min(crop_height, video_height - crop_y)

        # Ensure crop area is within video bounds (final validation)
        crop_x = max(0, min(crop_x, video_width - crop_width))
        crop_y = max(0, min(crop_y, video_height - crop_height))
        crop_width = min(crop_width, video_width - crop_x)
        crop_height = min(crop_height, video_height - crop_y)

        # Final aspect ratio validation - ensure it exactly matches target
        if target_ratio:
            actual_ratio = crop_width / crop_height
            if abs(actual_ratio - target_ratio) > 0.01:  # Allow small tolerance
                # Recalculate to ensure exact ratio match
                if target_ratio > actual_ratio:
                    # Need to be wider - reduce height
                    new_height = crop_width / target_ratio
                    height_diff = crop_height - new_height
                    crop_height = new_height
                    crop_y += height_diff / 2  # Center the adjustment
                else:
                    # Need to be taller - reduce width
                    new_width = crop_height * target_ratio
                    width_diff = crop_width - new_width
                    crop_width = new_width
                    crop_x += width_diff / 2  # Center the adjustment

                # Ensure still within bounds
                crop_x = max(0, min(crop_x, video_width - crop_width))
                crop_y = max(0, min(crop_y, video_height - crop_height))
        
        return {
            'x': int(crop_x),
            'y': int(crop_y),
            'width': int(crop_width),
            'height': int(crop_height),
            'method': 'ai_detected'
        }

    def process_video(self, input_path, output_path, target_width, target_height, 
                     quality='medium', compress=False):
        """
        Process video with smart cropping and optimization
        """
        if not self.check_ffmpeg():
            raise RuntimeError("FFmpeg is not installed. Please install FFmpeg to process videos.")
        
        try:
            # Analyze video content
            analysis = self.analyze_video_content(input_path, target_width=target_width, target_height=target_height)
            if not analysis:
                raise ValueError("Failed to analyze video content")
            
            video_info = analysis['video_info']
            optimal_crop = analysis['optimal_crop']
            
            # Build FFmpeg command
            cmd = ['ffmpeg', '-i', input_path]
            
            # Video filters
            filters = []

            # Smart crop filter - crop to area that matches target aspect ratio
            crop_filter = f"crop={optimal_crop['width']}:{optimal_crop['height']}:{optimal_crop['x']}:{optimal_crop['y']}"
            filters.append(crop_filter)
            logger.info(f"Smart crop applied: {crop_filter} (method: {optimal_crop['method']})")

            # Scale to exact target dimensions (no aspect ratio preservation needed since crop matches ratio)
            scale_filter = f"scale={target_width}:{target_height}"
            filters.append(scale_filter)
            
            # Apply filters
            if filters:
                cmd.extend(['-vf', ','.join(filters)])
            
            # Video codec and quality settings
            if compress:
                cmd.extend(['-c:v', 'libx264', '-crf', '28', '-preset', 'medium'])
            else:
                quality_map = {
                    'high': '18',
                    'medium': '23',
                    'low': '28'
                }
                crf = quality_map.get(quality, '23')
                cmd.extend(['-c:v', 'libx264', '-crf', crf, '-preset', 'medium'])
            
            # Audio codec
            cmd.extend(['-c:a', 'aac', '-b:a', '128k'])
            
            # Output settings
            cmd.extend(['-movflags', '+faststart', '-y', output_path])
            
            # Execute FFmpeg command
            logger.info(f"Executing: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                raise RuntimeError(f"FFmpeg failed: {result.stderr}")
            
            return {
                'success': True,
                'analysis': analysis,
                'crop_method': optimal_crop['method'],
                'detections_found': analysis['detections']
            }
            
        except Exception as e:
            logger.error(f"Video processing failed: {e}")
            raise

def main():
    """Main function for command line usage"""
    if len(sys.argv) < 5:
        print("Usage: python advanced_video_processor.py <input> <output> <width> <height> [quality] [compress]")
        sys.exit(1)
    
    input_path = sys.argv[1]
    output_path = sys.argv[2]
    target_width = int(sys.argv[3])
    target_height = int(sys.argv[4])
    quality = sys.argv[5] if len(sys.argv) > 5 else 'medium'
    compress = sys.argv[6].lower() == 'true' if len(sys.argv) > 6 else False
    
    processor = AdvancedVideoProcessor()
    
    try:
        result = processor.process_video(
            input_path, output_path, target_width, target_height, quality, compress
        )
        print(json.dumps(result, indent=2))
    except Exception as e:
        logger.error(f"Processing failed: {e}")
        print(json.dumps({'success': False, 'error': str(e)}))
        sys.exit(1)

if __name__ == "__main__":
    main()
