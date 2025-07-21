import face_recognition
import cv2
import numpy as np
import logging
import os
from typing import List, Tuple, Optional
from app.models import User, db
from config.config import Config as cfg

logger = logging.getLogger(__name__)

class FaceRecognitionService:
    """Service for handling face recognition operations"""
    
    def __init__(self, tolerance=cfg.FACE_RECOGNITION_TOLERANCE):
        self.tolerance = tolerance
        self.known_encodings = []
        self.known_user_ids = []
        self.load_known_faces()
    
    def load_known_faces(self):
        """Load all registered user face encodings"""
        try:
            users = User.query.filter(User.face_encoding.isnot(None)).all()
            self.known_encodings = []
            self.known_user_ids = []
            
            for user in users:
                encoding = user.get_face_encoding()
                if encoding is not None:
                    self.known_encodings.append(encoding)
                    self.known_user_ids.append(user.id)
            
            logger.info(f"Loaded {len(self.known_encodings)} face encodings")
        except Exception as e:
            logger.error(f"Error loading known faces: {str(e)}")
    
    def extract_face_encoding(self, image_path: str) -> Optional[np.ndarray]:
        """Extract face encoding from image file"""
        try:
            # Load image
            image = face_recognition.load_image_file(image_path)
            
            # Find face locations
            face_locations = face_recognition.face_locations(image)
            
            if not face_locations:
                logger.warning("No face found in image")
                return None
            
            if len(face_locations) > 1:
                logger.warning("Multiple faces found, using the first one")
            
            # Get face encoding
            face_encodings = face_recognition.face_encodings(image, face_locations)
            
            if face_encodings:
                return face_encodings[0]
            
            return None
            
        except Exception as e:
            logger.error(f"Error extracting face encoding: {str(e)}")
            return None
    
    def recognize_face_from_camera(self) -> Tuple[Optional[int], float]:
        """Recognize face from camera feed"""
        try:
            # Initialize camera
            cap = cv2.VideoCapture(0)
            
            if not cap.isOpened():
                logger.error("Could not open camera")
                return None, 0.0
            
            # Capture frame
            ret, frame = cap.read()
            cap.release()
            
            if not ret:
                logger.error("Could not capture frame")
                return None, 0.0
            
            # Convert BGR to RGB
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Find faces in frame
            face_locations = face_recognition.face_locations(rgb_frame)
            face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)
            
            if not face_encodings:
                logger.warning("No face detected in camera")
                return None, 0.0
            
            # Compare with known faces
            face_encoding = face_encodings[0]  # Use first detected face
            
            if not self.known_encodings:
                logger.warning("No known faces loaded")
                return None, 0.0
            
            # Calculate distances to all known faces
            face_distances = face_recognition.face_distance(self.known_encodings, face_encoding)
            
            # Find best match
            best_match_index = np.argmin(face_distances)
            best_distance = face_distances[best_match_index]
            
            # Check if match is within tolerance
            if best_distance <= self.tolerance:
                user_id = self.known_user_ids[best_match_index]
                confidence = 1.0 - best_distance  # Convert distance to confidence
                logger.info(f"Face recognized: User ID {user_id}, Confidence: {confidence:.2f}")
                return user_id, confidence
            else:
                logger.info(f"Face not recognized. Best distance: {best_distance:.2f}")
                return None, 0.0
                
        except Exception as e:
            logger.error(f"Error in face recognition: {str(e)}")
            return None, 0.0
    
    def recognize_face_from_image(self, image_path: str) -> Tuple[Optional[int], float]:
        """Recognize face from uploaded image"""
        try:
            # Extract encoding from uploaded image
            face_encoding = self.extract_face_encoding(image_path)
            
            if face_encoding is None:
                return None, 0.0
            
            if not self.known_encodings:
                logger.warning("No known faces loaded")
                return None, 0.0
            
            # Compare with known faces
            face_distances = face_recognition.face_distance(self.known_encodings, face_encoding)
            
            # Find best match
            best_match_index = np.argmin(face_distances)
            best_distance = face_distances[best_match_index]
            
            # Check if match is within tolerance
            if best_distance <= self.tolerance:
                user_id = self.known_user_ids[best_match_index]
                confidence = 1.0 - best_distance
                return user_id, confidence
            else:
                return None, 0.0
                
        except Exception as e:
            logger.error(f"Error recognizing face from image: {str(e)}")
            return None, 0.0
    
    def validate_face_image(self, image_path: str) -> bool:
        """Validate that image contains exactly one clear face"""
        try:
            image = face_recognition.load_image_file(image_path)
            face_locations = face_recognition.face_locations(image)
            
            return len(face_locations) == 1
            
        except Exception as e:
            logger.error(f"Error validating face image: {str(e)}")
            return False

