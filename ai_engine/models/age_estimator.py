"""
Age estimation (simplified version using DeepFace)
"""
from deepface import DeepFace
import cv2
import numpy as np
from typing import Optional

class AgeEstimator:
    def __init__(self):
        """Initialize age estimator"""
        pass
    
    def estimate(self, face_image: np.ndarray) -> Optional[int]:
        """
        Estimate age from face image
        
        Args:
            face_image: Cropped face image (BGR)
            
        Returns:
            Estimated age or None
        """
        try:
            # Convert to RGB
            rgb_image = cv2.cvtColor(face_image, cv2.COLOR_BGR2RGB)
            
            # Analyze
            result = DeepFace.analyze(
                rgb_image,
                actions=['age'],
                enforce_detection=False,
                silent=True
            )
            
            if isinstance(result, list):
                result = result[0]
            
            return int(result['age'])
            
        except Exception as e:
            print(f"Age estimation failed: {e}")
            return None
    
    def estimate_age_range(self, face_image: np.ndarray) -> Optional[str]:
        """
        Estimate age range category
        
        Returns:
            Age range string (child, teen, adult, senior) or None
        """
        age = self.estimate(face_image)
        
        if age is None:
            return None
        
        if age < 13:
            return "child"
        elif age < 20:
            return "teen"
        elif age < 60:
            return "adult"
        else:
            return "senior"