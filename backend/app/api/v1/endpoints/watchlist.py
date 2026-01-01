"""
Watchlist management endpoints
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime
import json

from app.db.session import get_db
from app.models.watchlist import WatchlistPerson
from app.models.user import User
from app.schemas.watchlist import WatchlistCreate, WatchlistUpdate, WatchlistResponse, WatchlistDetail
from app.api.deps import get_current_user, require_role
from app.services.watchlist_service import WatchlistService

router = APIRouter()

@router.get("/", response_model=List[WatchlistResponse])
async def get_watchlist(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    category: Optional[str] = None,
    risk_level: Optional[str] = None,
    is_active: Optional[bool] = True,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all watchlist persons with filters"""
    query = select(WatchlistPerson)
    
    if category:
        query = query.where(WatchlistPerson.category == category)
    
    if risk_level:
        query = query.where(WatchlistPerson.risk_level == risk_level)
    
    if is_active is not None:
        query = query.where(WatchlistPerson.is_active == is_active)
    
    query = query.offset(skip).limit(limit).order_by(WatchlistPerson.priority.desc())
    
    result = await db.execute(query)
    persons = result.scalars().all()
    
    return persons

@router.get("/{person_id}", response_model=WatchlistDetail)
async def get_watchlist_person(
    person_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get watchlist person by ID"""
    result = await db.execute(
        select(WatchlistPerson).where(WatchlistPerson.id == person_id)
    )
    person = result.scalar_one_or_none()
    
    if not person:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Person not found in watchlist"
        )
    
    return person

@router.post("/", response_model=WatchlistResponse, status_code=status.HTTP_201_CREATED)
async def enroll_person(
    person_data: str = Query(...),  # JSON string
    photos: List[UploadFile] = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin", "operator"))
):
    """Enroll new person in watchlist with photos"""
    # Parse person data
    try:
        person_dict = json.loads(person_data)
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON in person_data"
        )
    
    # Check if person_id already exists
    result = await db.execute(
        select(WatchlistPerson).where(WatchlistPerson.person_id == person_dict["person_id"])
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Person ID already exists"
        )
    
    # Use service to process enrollment
    service = WatchlistService(db)
    person = await service.enroll_person(person_dict, photos, current_user.username)
    
    return person

@router.put("/{person_id}", response_model=WatchlistResponse)
async def update_watchlist_person(
    person_id: int,
    person_update: WatchlistUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin", "operator"))
):
    """Update watchlist person"""
    result = await db.execute(
        select(WatchlistPerson).where(WatchlistPerson.id == person_id)
    )
    person = result.scalar_one_or_none()
    
    if not person:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Person not found"
        )
    
    # Update fields
    update_data = person_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(person, field, value)
    
    person.updated_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(person)
    
    return person

@router.delete("/{person_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_watchlist_person(
    person_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin"))
):
    """Delete person from watchlist"""
    result = await db.execute(
        select(WatchlistPerson).where(WatchlistPerson.id == person_id)
    )
    person = result.scalar_one_or_none()
    
    if not person:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Person not found"
        )
    
    await db.delete(person)
    await db.commit()

@router.get("/search/by-name")
async def search_by_name(
    name: str = Query(..., min_length=2),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Search watchlist by name"""
    result = await db.execute(
        select(WatchlistPerson)
        .where(WatchlistPerson.name.ilike(f"%{name}%"))
        .where(WatchlistPerson.is_active == True)
    )
    persons = result.scalars().all()
    
    return [p.to_dict() for p in persons]