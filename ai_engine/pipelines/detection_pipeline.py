"""
Complete detection pipeline integrating all AI models
"""
import cv2
import numpy as np
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field

from ai_engine.models.face_detector import FaceDetector
from ai_engine.models.face_recognizer import FaceRecognizer
from ai_engine.models.emotion_detector import EmotionDetector
from ai_engine.models.pose_estimator import PoseEstimator
from ai_engine.models.anti_spoof import AntiSpoofDetector
from ai_engine.models.age_estimator import AgeEstimator
from ai_engine.utils.performance_optimizer import CPUOptimizer, MotionDetector

@dataclass
class DetectionResult:
    """Detection result container"""
    has_face: bool
    face_bbox: Optional[tuple] = None
    face_embedding: Optional[np.ndarray] = None
    face_quality_score: float = 0.0
    is_real_face: bool = True
    emotion: Optional[str] = None
    age: Optional[int] = None
    pose_keypoints: Optional[dict] = None
    body_orientation: Optional[str] = None
    action: Optional[str] = None
    matched_person_id: Optional[int] = None
    confidence: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

class DetectionPipeline:
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize complete detection pipeline
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        
        # Initialize models (lazy loading)
        self.face_detector = None
        self.face_recognizer = None
        self.emotion_detector = None
        self.pose_estimator = None
        self.anti_spoof = None
        self.age_estimator = None
        
        # Initialize utilities
        self.motion_detector = MotionDetector(threshold=25.0)
        
        # Configure CPU optimization
        CPUOptimizer.configure_pytorch()
        
        # Feature flags from config
        self.enable_emotion = config.get('enable_emotion_detection', True)
        self.enable_pose = config.get('enable_pose_estimation', True)
        self.enable_anti_spoof = config.get('enable_anti_spoof', True)
        self.enable_age = config.get('enable_age_estimation', False)
    
    def _ensure_models_loaded(self):
        """Lazy load models only when needed"""
        if self.face_detector is None:
            self.face_detector = FaceDetector(min_confidence=0.9)
        
        if self.face_recognizer is None:
            self.face_recognizer = FaceRecognizer(model_name="buffalo_l")
        
        if self.enable_emotion and self.emotion_detector is None:
            self.emotion_detector = EmotionDetector()
        
        if self.enable_pose and self.pose_estimator is None:
            self.pose_estimator = PoseEstimator(min_detection_confidence=0.5)
        
        if self.enable_anti_spoof and self.anti_spoof is None:
            self.anti_spoof = AntiSpoofDetector()
        
        if self.enable_age and self.age_estimator is None:
            self.age_estimator = AgeEstimator()
    
    async def process_frame(
        self,
        frame: np.ndarray,
        watchlist_embeddings: Optional[List[tuple]] = None,
        skip_motion_check: bool = False
    ) -> Optional[DetectionResult]:
        """
        Process single frame through complete pipeline
        
        Args:
            frame: BGR image from camera
            watchlist_embeddings: List of (person_id, embedding) tuples
            skip_motion_check: If True, skip motion detection
            
        Returns:
            DetectionResult or None if no detection
        """
        # Check for motion first (optimization)
        if not skip_motion_check and not self.motion_detector.has_motion(frame):
            return None
        
        # Ensure models are loaded
        self._ensure_models_loaded()
        
        # Optimize frame size
        optimized_frame = CPUOptimizer.optimize_image_size(frame, max_dimension=640)
        
        # Step 1: Detect faces
        faces = self.face_detector.detect(optimized_frame)
        
        if len(faces) == 0:
            return DetectionResult(has_face=False)
        
        # Use largest face
        face_bbox = max(faces, key=lambda x: (x[2] - x[0]) * (x[3] - x[1]))
        x1, y1, x2, y2 = face_bbox
        face_crop = optimized_frame[y1:y2, x1:x2]
        
        if face_crop.size == 0:
            return DetectionResult(has_face=False)
        
        # Step 2: Anti-spoofing check (if enabled)
        is_real = True
        if self.enable_anti_spoof:
            is_real, spoof_confidence = self.anti_spoof.predict(optimized_frame, face_bbox)
            if not is_real:
                return DetectionResult(
                    has_face=True,
                    face_bbox=face_bbox,
                    is_real_face=False,
                    confidence=spoof_confidence,
                    metadata={"spoof_detected": True}
                )
        
        # Step 3: Extract face embedding
        embedding = self.face_recognizer.extract_embedding(optimized_frame, face_bbox)
        
        if embedding is None:
            return DetectionResult(
                has_face=True,
                face_bbox=face_bbox,
                is_real_face=is_real,
                confidence=0.0
            )
        
        # Step 4: Search in watchlist
        matched_id = None
        max_confidence = 0.0
        
        if watchlist_embeddings:
            for person_id, watch_emb in watchlist_embeddings:
                is_match, similarity = self.face_recognizer.compare_embeddings(
                    embedding, watch_emb
                )
                if is_match and similarity > max_confidence:
                    matched_id = person_id
                    max_confidence = similarity
        
        # Step 5: Emotion detection (if enabled)
        emotion = None
        if self.enable_emotion:
            emotion = self.emotion_detector.predict(face_crop)
        
        # Step 6: Age estimation (if enabled)
        age = None
        if self.enable_age:
            age = self.age_estimator.estimate(face_crop)
        
        # Step 7: Pose estimation (if enabled)
        pose_data = None
        body_orientation = None
        action = None
        
        if self.enable_pose:
            pose_data = self.pose_estimator.detect(optimized_frame)
            if pose_data:
                body_orientation = self.pose_estimator.get_body_orientation(pose_data)
                action = self.pose_estimator.detect_action(pose_data)
        
        # Calculate face quality score
        face_quality = self._calculate_face_quality(face_bbox, optimized_frame.shape)
        
        return DetectionResult(
            has_face=True,
            face_bbox=face_bbox,
            face_embedding=embedding,
            face_quality_score=face_quality,
            is_real_face=is_real,
            emotion=emotion,
            age=age,
            pose_keypoints=pose_data,
            body_orientation=body_orientation,
            action=action,
            matched_person_id=matched_id,
            confidence=max_confidence,
            metadata={
                "face_count": len(faces),
                "face_size": (x2 - x1, y2 - y1),
                "frame_size": optimized_frame.shape[:2]
            }
        )
    
    def _calculate_face_quality(
        self,
        face_bbox: tuple,
        frame_shape: tuple
    ) -> float:
        """
        Calculate face quality score based on size and position
        
        Returns:
            Score between 0 and 1
        """
        x1, y1, x2, y2 = face_bbox
        h, w = frame_shape[:2]
        
        face_w = x2 - x1
        face_h = y2 - y1
        face_area = face_w * face_h
        frame_area = h * w
        
        # Size score (faces should be 5-50% of frame)
        size_ratio = face_area / frame_area
        if size_ratio < 0.05:
            size_score = size_ratio / 0.05
        elif size_ratio > 0.5:
            size_score = (1.0 - size_ratio) * 2
        else:
            size_score = 1.0
        
        # Position score (faces should be in center 80% of frame)
        center_x = (x1 + x2) / 2
        center_y = (y1 + y2) / 2
        frame_center_x = w / 2
        frame_center_y = h / 2
        
        dist_from_center = np.sqrt(
            ((center_x - frame_center_x) / w) ** 2 +
            ((center_y - frame_center_y) / h) ** 2
        )
        
        position_score = max(0, 1.0 - dist_from_center * 2)
        
        # Combined score
        quality = (size_score + position_score) / 2
        
        return min(1.0, max(0.0, quality))