#!/usr/bin/env python3
"""
Advanced Media Processor with AI Detection Models
Uses YOLOv8, MediaPipe, OpenCV, and Pillow for professional-grade media processing
"""

import cv2
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter
import mediapipe as mp
import sys
import os
import json
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
except ImportError:
    YOLO_AVAILABLE = False
    logger.warning("YOLOv8 not available. Falling back to OpenCV and MediaPipe.")

try:
    import mediapipe as mp
    MEDIAPIPE_AVAILABLE = True
except ImportError:
    MEDIAPIPE_AVAILABLE = False
    logger.warning("MediaPipe not available.")

class AdvancedMediaProcessor:
    def __init__(self):
        """Initialize the advanced media processor with AI models"""
        self.mp_face_detection = mp.solutions.face_detection
        self.mp_pose = mp.solutions.pose
        self.mp_hands = mp.solutions.hands
        self.mp_selfie_segmentation = mp.solutions.selfie_segmentation
        
        # Initialize MediaPipe models with lower confidence thresholds
        if MEDIAPIPE_AVAILABLE:
            self.face_detection = self.mp_face_detection.FaceDetection(
                model_selection=1, min_detection_confidence=0.3
            )
            self.pose = self.mp_pose.Pose(
                static_image_mode=True, min_detection_confidence=0.3
            )
            self.hands = self.mp_hands.Hands(
                static_image_mode=True, max_num_hands=2, min_detection_confidence=0.3
            )
            self.selfie_segmentation = self.mp_selfie_segmentation.SelfieSegmentation(
                model_selection=1
            )
        else:
            self.face_detection = None
            self.pose = None
            self.hands = None
            self.selfie_segmentation = None
        
        # Initialize YOLOv8 if available
        self.yolo_model = None
        if YOLO_AVAILABLE:
            try:
                # Use YOLOv8n (nano) for speed, can upgrade to YOLOv8s/m/l/x for accuracy
                self.yolo_model = YOLO('yolov8n.pt')
                logger.info("YOLOv8 model loaded successfully")
            except Exception as e:
                logger.warning(f"Failed to load YOLOv8: {e}")
                self.yolo_model = None

    def detect_subjects(self, image_path):
        """
        Advanced subject detection using multiple AI models
        Returns comprehensive analysis of image content
        """
        try:
            # Load image
            image = cv2.imread(image_path)
            if image is None:
                raise ValueError(f"Could not load image: {image_path}")
            
            rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            h, w = image.shape[:2]
            
            detection_results = {
                'faces': [],
                'poses': [],
                'hands': [],
                'objects': [],
                'main_subject': None,
                'confidence': 0.0,
                'focal_points': [],
                'bounding_box': None
            }
            
            # 1. Face Detection with MediaPipe
            face_results = self.face_detection.process(rgb_image)
            if face_results.detections:
                for detection in face_results.detections:
                    bbox = detection.location_data.relative_bounding_box
                    face_info = {
                        'x': bbox.xmin * w,
                        'y': bbox.ymin * h,
                        'width': bbox.width * w,
                        'height': bbox.height * h,
                        'confidence': detection.score[0],
                        'center_x': (bbox.xmin + bbox.width/2) * w,
                        'center_y': (bbox.ymin + bbox.height/2) * h
                    }
                    detection_results['faces'].append(face_info)
            
            # 2. Pose Detection with MediaPipe
            pose_results = self.pose.process(rgb_image)
            if pose_results.pose_landmarks:
                landmarks = pose_results.pose_landmarks.landmark
                # Get key pose points
                nose = landmarks[0]
                left_shoulder = landmarks[11]
                right_shoulder = landmarks[12]
                
                pose_info = {
                    'nose': {'x': nose.x * w, 'y': nose.y * h},
                    'left_shoulder': {'x': left_shoulder.x * w, 'y': left_shoulder.y * h},
                    'right_shoulder': {'x': right_shoulder.x * w, 'y': right_shoulder.y * h},
                    'confidence': min(nose.visibility, left_shoulder.visibility, right_shoulder.visibility)
                }
                detection_results['poses'].append(pose_info)
            
            # 3. Hand Detection with MediaPipe
            hand_results = self.hands.process(rgb_image)
            if hand_results.multi_hand_landmarks:
                for hand_landmarks in hand_results.multi_hand_landmarks:
                    # Get bounding box of hand
                    x_coords = [lm.x * w for lm in hand_landmarks.landmark]
                    y_coords = [lm.y * h for lm in hand_landmarks.landmark]
                    
                    hand_info = {
                        'x': min(x_coords),
                        'y': min(y_coords),
                        'width': max(x_coords) - min(x_coords),
                        'height': max(y_coords) - min(y_coords),
                        'center_x': sum(x_coords) / len(x_coords),
                        'center_y': sum(y_coords) / len(y_coords)
                    }
                    detection_results['hands'].append(hand_info)
            
            # 4. Object Detection with YOLOv8 (lowered confidence threshold)
            if self.yolo_model:
                try:
                    yolo_results = self.yolo_model(image_path, verbose=False, conf=0.15)
                    for result in yolo_results:
                        boxes = result.boxes
                        if boxes is not None:
                            for box in boxes:
                                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                                conf = box.conf[0].cpu().numpy()
                                cls = int(box.cls[0].cpu().numpy())

                                # Include more object types and lower confidence threshold
                                if conf > 0.15:  # Lower threshold for better detection
                                    object_info = {
                                        'class': self.yolo_model.names[cls],
                                        'confidence': float(conf),
                                        'x': float(x1),
                                        'y': float(y1),
                                        'width': float(x2 - x1),
                                        'height': float(y2 - y1),
                                        'center_x': float((x1 + x2) / 2),
                                        'center_y': float((y1 + y2) / 2)
                                    }
                                    detection_results['objects'].append(object_info)
                except Exception as e:
                    logger.warning(f"YOLOv8 detection failed: {e}")
            
            # 5. Determine main subject and focal points
            main_subject, focal_points, bbox = self._determine_main_subject(
                detection_results, w, h, image_path
            )
            
            detection_results['main_subject'] = main_subject
            detection_results['focal_points'] = focal_points
            detection_results['bounding_box'] = bbox
            
            return detection_results
            
        except Exception as e:
            logger.error(f"Subject detection failed: {e}")
            return self._fallback_detection(image_path)

    def _determine_main_subject(self, detection_results, w, h, image_path):
        """Determine the main subject and optimal crop area"""
        subjects = []
        
        # Prioritize faces (highest priority)
        for face in detection_results['faces']:
            subjects.append({
                'type': 'face',
                'confidence': face['confidence'],
                'area': face['width'] * face['height'],
                'center': (face['center_x'], face['center_y']),
                'bbox': (face['x'], face['y'], face['width'], face['height'])
            })
        
        # Add poses (medium priority)
        for pose in detection_results['poses']:
            # Estimate pose area from shoulder width
            shoulder_width = abs(pose['right_shoulder']['x'] - pose['left_shoulder']['x'])
            estimated_height = shoulder_width * 3  # Rough estimate
            area = shoulder_width * estimated_height
            
            subjects.append({
                'type': 'pose',
                'confidence': pose['confidence'],
                'area': area,
                'center': (pose['nose']['x'], pose['nose']['y']),
                'bbox': (
                    pose['left_shoulder']['x'] - shoulder_width/2,
                    pose['nose']['y'] - estimated_height/3,
                    shoulder_width * 2,
                    estimated_height
                )
            })
        
        # Add significant objects (lower priority) - relaxed thresholds
        for obj in detection_results['objects']:
            # Lower confidence threshold and smaller area requirement
            min_area_ratio = 0.01  # 1% of image instead of 5%
            if obj['confidence'] > 0.2 and obj['width'] * obj['height'] > (w * h * min_area_ratio):
                subjects.append({
                    'type': f"object_{obj['class']}",
                    'confidence': obj['confidence'],
                    'area': obj['width'] * obj['height'],
                    'center': (obj['center_x'], obj['center_y']),
                    'bbox': (obj['x'], obj['y'], obj['width'], obj['height'])
                })
        
        if not subjects:
            # Use content-aware fallback detection
            return self._content_aware_fallback(image_path, w, h)
        
        # Sort by priority: faces > poses > objects, then by confidence and area
        def subject_score(s):
            type_priority = {'face': 3, 'pose': 2}
            base_priority = type_priority.get(s['type'], 1)
            return base_priority * s['confidence'] * (s['area'] / (w * h))
        
        best_subject = max(subjects, key=subject_score)
        
        # Create focal points from all detected subjects
        focal_points = [s['center'] for s in subjects[:3]]  # Top 3 subjects
        
        # Convert to percentage coordinates
        focal_points_pct = [
            {'x': (x / w) * 100, 'y': (y / h) * 100} 
            for x, y in focal_points
        ]
        
        # Create bounding box with padding
        x, y, width, height = best_subject['bbox']
        padding = 0.2
        padded_x = max(0, x - width * padding)
        padded_y = max(0, y - height * padding)
        padded_width = min(w - padded_x, width * (1 + 2 * padding))
        padded_height = min(h - padded_y, height * (1 + 2 * padding))
        
        bbox_pct = {
            'x': (padded_x / w) * 100,
            'y': (padded_y / h) * 100,
            'width': (padded_width / w) * 100,
            'height': (padded_height / h) * 100
        }
        
        return best_subject['type'], focal_points_pct, bbox_pct

    def _content_aware_fallback(self, image_path, w, h):
        """Content-aware fallback using OpenCV features when AI detection fails"""
        try:
            image = cv2.imread(image_path)
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

            # 1. Try edge detection to find interesting regions
            edges = cv2.Canny(gray, 50, 150)

            # 2. Find contours for potential subjects
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            # 3. Analyze contours for significant shapes
            significant_contours = []
            for contour in contours:
                area = cv2.contourArea(contour)
                if area > (w * h * 0.005):  # At least 0.5% of image
                    x, y, cw, ch = cv2.boundingRect(contour)
                    aspect_ratio = cw / ch
                    # Prefer more square-like shapes (potential subjects)
                    if 0.3 < aspect_ratio < 3.0:
                        significant_contours.append({
                            'area': area,
                            'center': (x + cw/2, y + ch/2),
                            'bbox': (x, y, cw, ch),
                            'aspect_ratio': aspect_ratio
                        })

            # 4. Use rule of thirds if no significant contours
            if not significant_contours:
                # Rule of thirds focal points
                focal_points = [
                    (w * 0.33, h * 0.33),  # Top-left third
                    (w * 0.67, h * 0.33),  # Top-right third
                    (w * 0.33, h * 0.67),  # Bottom-left third
                    (w * 0.67, h * 0.67),  # Bottom-right third
                ]

                # Choose the point with most edge activity
                best_point = (w/2, h/2)
                max_activity = 0

                for point in focal_points:
                    x, y = int(point[0]), int(point[1])
                    # Sample area around the point
                    x1, y1 = max(0, x-50), max(0, y-50)
                    x2, y2 = min(w, x+50), min(h, y+50)
                    roi = edges[y1:y2, x1:x2]
                    activity = np.sum(roi)

                    if activity > max_activity:
                        max_activity = activity
                        best_point = point

                return "Rule of thirds composition", [best_point], {
                    'x': (best_point[0] - w*0.25) / w * 100,
                    'y': (best_point[1] - h*0.25) / h * 100,
                    'width': 50,
                    'height': 50
                }

            # 5. Use largest significant contour
            best_contour = max(significant_contours, key=lambda c: c['area'])
            x, y, cw, ch = best_contour['bbox']

            return "Content-aware detection", [best_contour['center']], {
                'x': x / w * 100,
                'y': y / h * 100,
                'width': cw / w * 100,
                'height': ch / h * 100
            }

        except Exception as e:
            logger.warning(f"Content-aware fallback failed: {e}")
            # Ultimate fallback - center crop
            return "Center composition", [(w/2, h/2)], {
                'x': 25, 'y': 25, 'width': 50, 'height': 50
            }

    def _fallback_detection(self, image_path):
        """Fallback detection using traditional OpenCV methods"""
        try:
            image = cv2.imread(image_path)
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            h, w = image.shape[:2]
            
            # Try face detection with Haar cascades
            face_cascade = cv2.CascadeClassifier(
                cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
            )
            faces = face_cascade.detectMultiScale(gray, 1.1, 4)
            
            if len(faces) > 0:
                x, y, fw, fh = max(faces, key=lambda f: f[2] * f[3])
                return {
                    'main_subject': 'Face detected (OpenCV)',
                    'focal_points': [{'x': (x + fw/2) / w * 100, 'y': (y + fh/2) / h * 100}],
                    'bounding_box': {
                        'x': (x / w) * 100,
                        'y': (y / h) * 100,
                        'width': (fw / w) * 100,
                        'height': (fh / h) * 100
                    },
                    'confidence': 0.7
                }
            
            # Use content-aware fallback
            main_subject, focal_points, bbox = self._content_aware_fallback(image_path, w, h)
            return {
                'main_subject': main_subject,
                'focal_points': [{'x': fp[0] / w * 100, 'y': fp[1] / h * 100} for fp in focal_points],
                'bounding_box': bbox,
                'confidence': 0.4
            }
            
        except Exception as e:
            logger.error(f"Fallback detection failed: {e}")
            return {
                'main_subject': 'Error - using center',
                'focal_points': [{'x': 50, 'y': 50}],
                'bounding_box': None,
                'confidence': 0.1
            }

def main():
    """Main function for command line usage"""
    if len(sys.argv) != 5:
        print("Usage: python advanced_media_processor.py <input_path> <output_path> <width> <height>")
        sys.exit(1)
    
    input_path = sys.argv[1]
    output_path = sys.argv[2]
    target_width = int(sys.argv[3])
    target_height = int(sys.argv[4])
    
    processor = AdvancedMediaProcessor()
    
    try:
        # Detect subjects
        detection_results = processor.detect_subjects(input_path)
        
        # Load and process image
        with Image.open(input_path) as img:
            # Convert palette images to RGB
            if img.mode == 'P':
                img = img.convert('RGBA')
            elif img.mode == 'L':
                img = img.convert('RGB')
            
            original_width, original_height = img.size
            
            # Calculate optimal crop area that maintains target aspect ratio
            target_ratio = target_width / target_height
            original_ratio = original_width / original_height

            if detection_results['bounding_box']:
                bbox = detection_results['bounding_box']
                # Get subject center point
                subject_center_x = (bbox['x'] + bbox['width'] / 2) / 100 * original_width
                subject_center_y = (bbox['y'] + bbox['height'] / 2) / 100 * original_height
            else:
                # Default to image center
                subject_center_x = original_width / 2
                subject_center_y = original_height / 2

            # Calculate crop dimensions that maintain target aspect ratio
            if target_ratio > original_ratio:
                # Target is wider - use full width, crop height
                crop_width = original_width
                crop_height = int(crop_width / target_ratio)
                crop_x = 0
                # Center crop around subject vertically
                crop_y = int(subject_center_y - crop_height / 2)
                crop_y = max(0, min(crop_y, original_height - crop_height))
            else:
                # Target is taller - use full height, crop width
                crop_height = original_height
                crop_width = int(crop_height * target_ratio)
                crop_y = 0
                # Center crop around subject horizontally
                crop_x = int(subject_center_x - crop_width / 2)
                crop_x = max(0, min(crop_x, original_width - crop_width))

            # Perform the smart crop
            img = img.crop((crop_x, crop_y, crop_x + crop_width, crop_y + crop_height))

            # Resize to target dimensions (no stretching since aspect ratio matches)
            img = img.resize((target_width, target_height), Image.Resampling.LANCZOS)
            
            # Enhance image quality
            enhancer = ImageEnhance.Sharpness(img)
            img = enhancer.enhance(1.1)
            
            # Save with appropriate format
            if output_path.lower().endswith('.png'):
                img.save(output_path, 'PNG', optimize=True)
            else:
                if img.mode == 'RGBA':
                    # Convert RGBA to RGB for JPEG
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                    img = background
                img.save(output_path, 'JPEG', quality=90, optimize=True, progressive=True)
        
        # Output detection results for debugging
        print(json.dumps(detection_results, indent=2))
        
    except Exception as e:
        logger.error(f"Processing failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
