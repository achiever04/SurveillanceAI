"""
Emotion detection using DeepFace
"""
from deepface import DeepFace
import cv2
import numpy as np
from typing import Optional, Dict

class EmotionDetector:
    def __init__(self):
        """Initialize emotion detector"""
        self.emotion_labels = [
            'angry', 'disgust', 'fear', 'happy', 'sad', 'surprise', 'neutral'
        ]
    
    def predict(
        self,
        face_image: np.ndarray,
        return_all_scores: bool = False
    ) -> Optional[str | Dict]:
        """
        Predict emotion from face image
        
        Args:
            face_image: Cropped face image (BGR)
            return_all_scores: If True, return all emotion scores
            
        Returns:
            Dominant emotion string or dict of all scores
        """
        try:
            # DeepFace expects RGB
            if len(face_image.shape) == 3 and face_image.shape[2] == 3:
                rgb_image = cv2.cvtColor(face_image, cv2.COLOR_BGR2RGB)
            else:
                rgb_image = face_image
            
            # Analyze emotion
            result = DeepFace.analyze(
                rgb_image,
                actions=['emotion'],
                enforce_detection=False,
                silent=True
            )
            
            # Handle single face result
            if isinstance(result, list):
                result = result[0]
            
            emotion_scores = result['emotion']
            
            if return_all_scores:
                return emotion_scores
            else:
                # Return dominant emotion
                dominant_emotion = max(emotion_scores, key=emotion_scores.get)
                return dominant_emotion
                
        except Exception as e:
            print(f"Emotion detection failed: {e}")
            return None
    
    def predict_from_full_image(
        self,
        image: np.ndarray,
        face_bbox: tuple
    ) -> Optional[str]:
        """
        Predict emotion from full image with face bbox
        
        Args:
            image: Full BGR image
            face_bbox: (x1, y1, x2, y2)
        """
        x1, y1, x2, y2 = face_bbox
        face_crop = image[y1:y2, x1:x2]
        
        if face_crop.size == 0:
            return None
        
        return self.predict(face_crop)
    
    def get_emotion_intensity(
        self,
        face_image: np.ndarray,
        target_emotion: str
    ) -> float:
        """
        Get intensity score for specific emotion
        
        Returns:
            Score between 0 and 100
        """
        scores = self.predict(face_image, return_all_scores=True)
        
        if scores and target_emotion in scores:
            return scores[target_emotion]
        
        return 0.0