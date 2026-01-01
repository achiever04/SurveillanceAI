"""
Watchlist service for managing persons of interest
"""
import hashlib
import json
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime
from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import shutil

from app.models.watchlist import WatchlistPerson
from app.utils.ipfs_client import IPFSClient
from ai_engine.models.face_recognizer import FaceRecognizer
import cv2
import numpy as np

class WatchlistService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.ipfs_client = IPFSClient()
        self.face_recognizer = FaceRecognizer()
        self.storage_path = Path("data/watchlist")
        self.storage_path.mkdir(parents=True, exist_ok=True)
    
    async def enroll_person(
        self,
        person_data: Dict[str, Any],
        photos: List[UploadFile],
        enrolled_by: str
    ) -> WatchlistPerson:
        """
        Enroll new person with face photos
        """
        person_id = person_data["person_id"]
        
        # Process photos and extract embeddings
        embeddings = []
        photo_hashes = []
        local_paths = []
        ipfs_cids = []
        
        for idx, photo in enumerate(photos):
            # Read photo
            contents = await photo.read()
            
            # Save locally
            person_folder = self.storage_path / person_id
            person_folder.mkdir(exist_ok=True)
            
            photo_filename = f"photo_{idx}.jpg"
            photo_path = person_folder / photo_filename
            
            with open(photo_path, "wb") as f:
                f.write(contents)
            
            local_paths.append(str(photo_path))
            
            # Compute hash
            photo_hash = hashlib.sha256(contents).hexdigest()
            photo_hashes.append(photo_hash)
            
            # Extract face embedding
            image = cv2.imdecode(
                np.frombuffer(contents, np.uint8),
                cv2.IMREAD_COLOR
            )
            
            embedding = self.face_recognizer.extract_embedding(image)
            
            if embedding is not None:
                embeddings.append(embedding.tolist())
            
            # Upload to IPFS (optional)
            try:
                cid = await self.ipfs_client.add_file(contents)
                ipfs_cids.append(cid)
            except Exception as e:
                print(f"IPFS upload failed: {e}")
                ipfs_cids.append(None)
        
        if not embeddings:
            raise ValueError("No valid faces detected in provided photos")
        
        # Create watchlist person
        person = WatchlistPerson(
            person_id=person_id,
            name=person_data["name"],
            category=person_data["category"],
            risk_level=person_data.get("risk_level", "low"),
            age=person_data.get("age"),
            gender=person_data.get("gender"),
            description=person_data.get("description"),
            authorization_ref=person_data.get("authorization_ref"),
            face_embeddings=embeddings,
            photo_hashes=photo_hashes,
            num_photos=len(photos),
            photos_local_paths=local_paths,
            photos_ipfs_cids=ipfs_cids,
            enrolled_by=enrolled_by,
            alert_on_detection=person_data.get("alert_on_detection", True)
        )
        
        self.db.add(person)
        await self.db.commit()
        await self.db.refresh(person)
        
        # TODO: Register on blockchain
        # blockchain_tx = await self.blockchain_service.register_watchlist_enrollment(person)
        # person.blockchain_enrollment_tx = blockchain_tx
        # await self.db.commit()
        
        return person
    
    async def get_all_active_embeddings(self) -> List[tuple]:
        """
        Get all active watchlist embeddings for matching
        Returns: List of (person_id, embedding) tuples
        """
        result = await self.db.execute(
            select(WatchlistPerson)
            .where(WatchlistPerson.is_active == True)
        )
        persons = result.scalars().all()
        
        embeddings_list = []
        for person in persons:
            for embedding in person.face_embeddings:
                embeddings_list.append((person.id, np.array(embedding)))
        
        return embeddings_list
    
    async def update_last_seen(
        self,
        person_id: int,
        camera_id: int,
        location: str
    ):
        """Update last seen information"""
        result = await self.db.execute(
            select(WatchlistPerson).where(WatchlistPerson.id == person_id)
        )
        person = result.scalar_one_or_none()
        
        if person:
            person.last_seen_at = datetime.utcnow()
            person.last_seen_location = location
            person.last_seen_camera_id = camera_id
            person.total_detections += 1
            
            await self.db.commit()
    
    async def search_by_embedding(
        self,
        query_embedding: np.ndarray,
        threshold: float = 0.4
    ) -> tuple:
        """
        Search for matching person by face embedding
        Returns: (person_id, similarity_score) or None
        """
        embeddings_list = await self.get_all_active_embeddings()
        
        if not embeddings_list:
            return None
        
        best_match = None
        best_similarity = threshold
        
        for person_id, embedding in embeddings_list:
            similarity = np.dot(query_embedding, embedding)
            
            if similarity > best_similarity:
                best_similarity = similarity
                best_match = person_id
        
        if best_match:
            return (best_match, float(best_similarity))
        
        return None