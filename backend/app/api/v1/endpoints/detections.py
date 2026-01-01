"""
Detection management endpoints
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timedelta

from app.db.session import get_db
from app.models.detection import Detection
from app.models.user import User
from app.schemas.detection import DetectionResponse, DetectionDetail, DetectionUpdate
from app.api.deps import get_current_user, require_role

router = APIRouter()

@router.get("/", response_model=List[DetectionResponse])
async def get_detections(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    camera_id: Optional[int] = None,
    detection_type: Optional[str] = None,
    is_verified: Optional[bool] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get detections with filters"""
    query = select(Detection)
    
    if camera_id:
        query = query.where(Detection.camera_id == camera_id)
    
    if detection_type:
        query = query.where(Detection.detection_type == detection_type)
    
    if is_verified is not None:
        query = query.where(Detection.is_verified == is_verified)
    
    if start_date:
        query = query.where(Detection.timestamp >= start_date)
    
    if end_date:
        query = query.where(Detection.timestamp <= end_date)
    
    query = query.order_by(Detection.timestamp.desc()).offset(skip).limit(limit)
    
    result = await db.execute(query)
    detections = result.scalars().all()
    
    return detections

@router.get("/{detection_id}", response_model=DetectionDetail)
async def get_detection(
    detection_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get detection by ID"""
    result = await db.execute(
        select(Detection).where(Detection.id == detection_id)
    )
    detection = result.scalar_one_or_none()
    
    if not detection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Detection not found"
        )
    
    return detection

@router.patch("/{detection_id}", response_model=DetectionResponse)
async def update_detection(
    detection_id: int,
    detection_update: DetectionUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin", "operator"))
):
    """Update detection (operator action)"""
    result = await db.execute(
        select(Detection).where(Detection.id == detection_id)
    )
    detection = result.scalar_one_or_none()
    
    if not detection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Detection not found"
        )
    
    # Update fields
    update_data = detection_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(detection, field, value)
    
    detection.operator_id = current_user.id
    detection.action_timestamp = datetime.utcnow()
    detection.updated_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(detection)
    
    return detection

@router.get("/stats/summary")
async def get_detection_summary(
    days: int = Query(7, ge=1, le=90),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get detection statistics summary"""
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # Total detections
    total_result = await db.execute(
        select(func.count(Detection.id))
        .where(Detection.timestamp >= start_date)
    )
    total = total_result.scalar() or 0
    
    # By type
    type_result = await db.execute(
        select(Detection.detection_type, func.count(Detection.id))
        .where(Detection.timestamp >= start_date)
        .group_by(Detection.detection_type)
    )
    by_type = {row[0]: row[1] for row in type_result.all()}
    
    # Verified vs unverified
    verified_result = await db.execute(
        select(Detection.is_verified, func.count(Detection.id))
        .where(Detection.timestamp >= start_date)
        .group_by(Detection.is_verified)
    )
    verification = {row[0]: row[1] for row in verified_result.all()}
    
    return {
        "period_days": days,
        "total_detections": total,
        "by_type": by_type,
        "verified": verification.get(True, 0),
        "unverified": verification.get(False, 0)
    }

@router.delete("/{detection_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_detection(
    detection_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin"))
):
    """Delete detection (admin only)"""
    result = await db.execute(
        select(Detection).where(Detection.id == detection_id)
    )
    detection = result.scalar_one_or_none()
    
    if not detection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Detection not found"
        )
    
    await db.delete(detection)
    await db.commit()