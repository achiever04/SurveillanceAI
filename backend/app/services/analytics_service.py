"""
Analytics service for dashboard statistics and insights
"""
from datetime import datetime, timedelta
from typing import Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.detection import Detection
from app.models.camera import Camera
from app.models.watchlist import WatchlistPerson

class AnalyticsService:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_dashboard_stats(self) -> Dict[str, Any]:
        """
        Get main dashboard statistics
        """
        # Total cameras
        camera_count_result = await self.db.execute(
            select(func.count(Camera.id))
        )
        total_cameras = camera_count_result.scalar() or 0
        
        # Active cameras
        active_cameras_result = await self.db.execute(
            select(func.count(Camera.id)).where(Camera.is_active == True)
        )
        active_cameras = active_cameras_result.scalar() or 0
        
        # Total detections (last 24 hours)
        yesterday = datetime.utcnow() - timedelta(days=1)
        detections_24h_result = await self.db.execute(
            select(func.count(Detection.id))
            .where(Detection.timestamp >= yesterday)
        )
        detections_24h = detections_24h_result.scalar() or 0
        
        # Total detections (all time)
        total_detections_result = await self.db.execute(
            select(func.count(Detection.id))
        )
        total_detections = total_detections_result.scalar() or 0
        
        # Watchlist persons
        watchlist_count_result = await self.db.execute(
            select(func.count(WatchlistPerson.id))
            .where(WatchlistPerson.is_active == True)
        )
        watchlist_count = watchlist_count_result.scalar() or 0
        
        # Unverified detections
        unverified_result = await self.db.execute(
            select(func.count(Detection.id))
            .where(Detection.is_verified == False)
        )
        unverified_count = unverified_result.scalar() or 0
        
        # High priority alerts (last 24 hours)
        high_priority_result = await self.db.execute(
            select(func.count(Detection.id))
            .where(Detection.timestamp >= yesterday)
            .where(Detection.detection_type.in_(["face_match", "suspicious_behavior"]))
        )
        high_priority = high_priority_result.scalar() or 0
        
        return {
            "total_cameras": total_cameras,
            "active_cameras": active_cameras,
            "detections_24h": detections_24h,
            "total_detections": total_detections,
            "watchlist_persons": watchlist_count,
            "unverified_detections": unverified_count,
            "high_priority_alerts": high_priority,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def get_detection_trends(self, days: int = 7) -> Dict[str, Any]:
        """
        Get detection trends over time
        """
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Detections by day
        daily_result = await self.db.execute(
            select(
                func.date(Detection.timestamp).label('date'),
                func.count(Detection.id).label('count')
            )
            .where(Detection.timestamp >= start_date)
            .group_by(func.date(Detection.timestamp))
            .order_by(func.date(Detection.timestamp))
        )
        
        daily_data = [
            {"date": row.date.isoformat(), "count": row.count}
            for row in daily_result.all()
        ]
        
        # Detections by type
        type_result = await self.db.execute(
            select(
                Detection.detection_type,
                func.count(Detection.id).label('count')
            )
            .where(Detection.timestamp >= start_date)
            .group_by(Detection.detection_type)
        )
        
        by_type = {
            row.detection_type: row.count
            for row in type_result.all()
        }
        
        return {
            "period_days": days,
            "daily_detections": daily_data,
            "by_type": by_type
        }
    
    async def get_camera_health(self) -> Dict[str, Any]:
        """
        Get health status of all cameras
        """
        result = await self.db.execute(select(Camera))
        cameras = result.scalars().all()
        
        health_data = []
        for camera in cameras:
            # Calculate uptime (mock calculation)
            uptime = 95.0 if camera.is_online else 0.0
            
            # Get recent detections count
            recent_detections_result = await self.db.execute(
                select(func.count(Detection.id))
                .where(Detection.camera_id == camera.id)
                .where(Detection.timestamp >= datetime.utcnow() - timedelta(hours=1))
            )
            recent_detections = recent_detections_result.scalar() or 0
            
            health_data.append({
                "camera_id": camera.id,
                "name": camera.name,
                "status": camera.health_status,
                "is_online": camera.is_online,
                "uptime_percentage": uptime,
                "recent_detections": recent_detections,
                "error_count": camera.error_count,
                "last_seen": camera.last_seen.isoformat() if camera.last_seen else None
            })
        
        return {"cameras": health_data}