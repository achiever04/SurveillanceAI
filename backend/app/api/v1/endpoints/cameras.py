"""
Camera management endpoints
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func
from app.models.detection import Detection
from datetime import datetime
from loguru import logger
from app.db.session import get_db
from app.models.camera import Camera
from app.models.detection import Detection  # ← ADD THIS LINE
from app.models.user import User
from app.schemas.camera import CameraCreate, CameraUpdate, CameraResponse, CameraStats
from app.api.deps import get_current_user, require_role

router = APIRouter()

@router.get("/", response_model=List[CameraResponse])
async def get_cameras(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    is_active: Optional[bool] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all cameras with optional filters"""
    query = select(Camera)
    
    if is_active is not None:
        query = query.where(Camera.is_active == is_active)
    
    query = query.offset(skip).limit(limit).order_by(Camera.id)
    
    result = await db.execute(query)
    cameras = result.scalars().all()
    
    return cameras

@router.get("/{camera_id}", response_model=CameraResponse)
async def get_camera(
    camera_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get camera by ID"""
    result = await db.execute(
        select(Camera).where(Camera.id == camera_id)
    )
    camera = result.scalar_one_or_none()
    
    if not camera:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Camera not found"
        )
    
    return camera

@router.post("/", response_model=CameraResponse, status_code=status.HTTP_201_CREATED)
async def create_camera(
    camera_in: CameraCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin", "operator"))
):
    """Create new camera"""
    camera = Camera(
        name=camera_in.name,
        source_type=camera_in.source_type,
        source_url=camera_in.source_url,
        location=camera_in.location,
        latitude=camera_in.latitude,
        longitude=camera_in.longitude,
        resolution_width=camera_in.resolution_width,
        resolution_height=camera_in.resolution_height,
        fps=camera_in.fps
    )
    
    db.add(camera)
    await db.commit()
    await db.refresh(camera)
    
    return camera

@router.put("/{camera_id}", response_model=CameraResponse)
async def update_camera(
    camera_id: int,
    camera_update: CameraUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin", "operator"))
):
    """Update camera configuration"""
    result = await db.execute(
        select(Camera).where(Camera.id == camera_id)
    )
    camera = result.scalar_one_or_none()
    
    if not camera:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Camera not found"
        )
    
    # Update fields
    update_data = camera_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(camera, field, value)
    
    camera.updated_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(camera)
    
    return camera

@router.delete("/{camera_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_camera(
    camera_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin"))
):
    """Delete camera"""
    result = await db.execute(
        select(Camera).where(Camera.id == camera_id)
    )
    camera = result.scalar_one_or_none()
    
    if not camera:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Camera not found"
        )
    
    await db.delete(camera)
    await db.commit()

@router.get("/{camera_id}/stats", response_model=CameraStats)
async def get_camera_stats(
    camera_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get camera statistics"""
    from app.models.detection import Detection
    from datetime import datetime, timedelta
    
    result = await db.execute(
        select(Camera).where(Camera.id == camera_id)
    )
    camera = result.scalar_one_or_none()
    
    if not camera:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Camera not found"
        )
    
    # Total detections
    total_result = await db.execute(
        select(func.count(Detection.id)).where(Detection.camera_id == camera_id)
    )
    total_detections = total_result.scalar() or 0
    
    # Detections today
    today = datetime.utcnow().date()
    today_result = await db.execute(
        select(func.count(Detection.id))
        .where(Detection.camera_id == camera_id)
        .where(func.date(Detection.timestamp) == today)
    )
    detections_today = today_result.scalar() or 0
    
    return CameraStats(
        camera_id=camera_id,
        total_detections=total_detections,
        detections_today=detections_today,
        uptime_percentage=95.5,  # Calculate from health logs
        avg_fps=camera.fps * 0.9  # Estimate based on processing
    )

@router.post("/{camera_id}/start")
async def start_camera(
    camera_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin", "operator"))
):
    """Start camera stream processing"""
    result = await db.execute(
        select(Camera).where(Camera.id == camera_id)
    )
    camera = result.scalar_one_or_none()
    
    if not camera:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Camera not found"
        )
    
    # Import camera integration modules
    from camera_integration.camera_manager import CameraManager, CameraConfig
    from camera_integration.stream_processor import StreamProcessor
    import asyncio
    
    # Update database status
    camera.is_active = True
    camera.is_online = True
    camera.updated_at = datetime.utcnow()
    await db.commit()
    
    try:
        # Get or create camera manager instance (should be singleton in production)
        if not hasattr(start_camera, 'manager'):
            start_camera.manager = CameraManager()
        
        # Create camera config
        config = CameraConfig(
            id=camera_id,
            name=camera.name,
            source=camera.source_url,
            fps=camera.fps,
            resolution=(camera.resolution_width, camera.resolution_height),
            enabled=True
        )
        
        # Add camera to manager
        if camera_id not in start_camera.manager.cameras:
            success = start_camera.manager.add_camera(config)
            if not success:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to initialize camera"
                )
        
        # Create stream processor
        processor = StreamProcessor(db, config={
            'enable_emotion_detection': camera.enable_emotion_detection,
            'enable_pose_estimation': camera.enable_pose_estimation,
            'enable_anti_spoof': True,
            'process_every_n': 3
        })
        
        # Register frame processing callback
        async def process_frame_callback(cam_id: int, frame, frame_number: int):
            await processor.process_frame(cam_id, frame, frame_number)
        
        start_camera.manager.register_callback(camera_id, process_frame_callback)
        
        # Start camera streaming
        start_camera.manager.start_camera(camera_id)
        
        logger.info(f"Camera {camera_id} started successfully")
        
        return {
            "message": f"Camera {camera_id} started successfully",
            "camera_id": camera_id,
            "status": "active"
        }
        
    except Exception as e:
        # Rollback database changes on error
        camera.is_active = False
        camera.is_online = False
        await db.commit()
        
        logger.error(f"Failed to start camera {camera_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start camera: {str(e)}"
        )

@router.post("/{camera_id}/stop")
async def stop_camera(
    camera_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin", "operator"))
):
    """Stop camera stream processing"""
    result = await db.execute(
        select(Camera).where(Camera.id == camera_id)
    )
    camera = result.scalar_one_or_none()
    
    if not camera:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Camera not found"
        )
    
    try:
        # Stop camera if manager exists
        if hasattr(start_camera, 'manager'):
            start_camera.manager.stop_camera(camera_id)
            start_camera.manager.remove_camera(camera_id)
        
        # Update database status
        camera.is_active = False
        camera.is_online = False
        camera.updated_at = datetime.utcnow()
        await db.commit()
        
        logger.info(f"Camera {camera_id} stopped successfully")
        
        return {
            "message": f"Camera {camera_id} stopped successfully",
            "camera_id": camera_id,
            "status": "inactive"
        }
        
    except Exception as e:
        logger.error(f"Failed to stop camera {camera_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to stop camera: {str(e)}"
        )
    
@router.get("/{camera_id}/stream")
async def stream_camera(
    camera_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Stream camera feed (MJPEG)"""
    from starlette.responses import StreamingResponse
    import cv2
    import asyncio
    
    result = await db.execute(
        select(Camera).where(Camera.id == camera_id)
    )
    camera = result.scalar_one_or_none()
    
    if not camera:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Camera not found"
        )
    
    async def generate_frames():
        """Generate frames for MJPEG stream"""
        # This is a simplified version - in production use proper camera manager
        cap = cv2.VideoCapture(int(camera.source_url) if camera.source_url.isdigit() else camera.source_url)
        
        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                # Encode frame as JPEG
                _, buffer = cv2.imencode('.jpg', frame)
                frame_bytes = buffer.tobytes()
                
                # Yield frame in MJPEG format
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
                
                await asyncio.sleep(0.1)  # ~10 FPS
        finally:
            cap.release()
    
    return StreamingResponse(
        generate_frames(),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )