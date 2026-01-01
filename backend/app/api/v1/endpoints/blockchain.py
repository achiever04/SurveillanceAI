"""
Blockchain query endpoints
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from app.db.session import get_db
from app.models.user import User
from app.api.deps import get_current_user
from app.services.blockchain_service import BlockchainService
from app.schemas.blockchain import ProvenanceQuery, ProvenanceResponse

router = APIRouter()

@router.get("/transactions")
async def get_blockchain_transactions(
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get recent blockchain transactions"""
    # Since we don't have the full service code, return a mock list if service fails
    # or implement a simple DB query if you store receipts locally.
    
    # Mock response to satisfy frontend for now:
    return [
        {
            "tx_id": "0x1234...abcd",
            "type": "EVIDENCE_LOG",
            "timestamp": datetime.utcnow(),
            "asset_id": "EVT-001",
            "status": "COMMITTED"
        },
        {
            "tx_id": "0x5678...ef90",
            "type": "ACCESS_LOG",
            "timestamp": datetime.utcnow(),
            "asset_id": "USER-ADMIN",
            "status": "COMMITTED"
        }
    ]

@router.post("/provenance", response_model=ProvenanceResponse)
async def get_evidence_provenance(
    query: ProvenanceQuery,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get evidence provenance from blockchain"""
    service = BlockchainService(db)
    return await service.get_evidence_provenance(query.event_id)

@router.post("/verify/{event_id}")
async def verify_evidence_blockchain(
    event_id: str,
    current_hash: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Verify evidence integrity using blockchain"""
    service = BlockchainService(db)
    is_valid = await service.verify_evidence_integrity(event_id, current_hash)
    
    return {
        "event_id": event_id,
        "is_valid": is_valid,
        "verified_at": datetime.utcnow().isoformat()
    }