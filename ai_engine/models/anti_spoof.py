"""
Anti-spoofing detection using DeepFace (MiniFASNet)
"""
import cv2
import numpy as np
from typing import Tuple
from deepface import DeepFace

class AntiSpoofDetector:
    def __init__(self):
        """Initialize anti-spoofing detector"""
        # DeepFace initializes models lazily on the first call
        pass
    
    def predict(
        self,
        image: np.ndarray,
        face_bbox: Tuple[int, int, int, int]
    ) -> Tuple[bool, float]:
        """
        Predict if face is real or spoofed
        
        Args:
            image: Full BGR image
            face_bbox: (x1, y1, x2, y2)
            
        Returns:
            (is_real, confidence_score)
        """
        try:
            x1, y1, x2, y2 = face_bbox
            # Ensure bbox is within image bounds
            h, w = image.shape[:2]
            x1 = max(0, x1)
            y1 = max(0, y1)
            x2 = min(w, x2)
            y2 = min(h, y2)
            
            # Crop the face
            face_crop = image[y1:y2, x1:x2]
            
            if face_crop.size == 0:
                return True, 0.0
                
            # Use DeepFace's built-in anti-spoofing (MiniFASNet)
            # enforce_detection=False because we are providing a crop
            # anti_spoofing=True enables the liveness check
            results = DeepFace.extract_faces(
                img_path=face_crop,
                enforce_detection=False,
                anti_spoofing=True,
                align=False  # Speed optimization
            )
            
            if results:
                # DeepFace returns a list of result dicts
                result = results[0]
                is_real = result.get("is_real", True)
                # Use the score if available, otherwise default based on result
                confidence = result.get("antispoof_score", 0.95 if is_real else 0.05)
                return is_real, confidence
                
            # Default fallback
            return True, 0.5
            
        except Exception as e:
            # print(f"Anti-spoofing detection failed: {e}")
            # Fail-open (assume real) to prevent blocking entry on error
            return True, 0.5
    
    def predict_from_crop(self, face_crop: np.ndarray) -> bool:
        """
        Predict from cropped face image
        """
        try:
            results = DeepFace.extract_faces(
                img_path=face_crop,
                enforce_detection=False,
                anti_spoofing=True,
                align=False
            )
            if results:
                return results[0].get("is_real", True)
            return True
        except:
            return True