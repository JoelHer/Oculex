from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from backend.StreamManager import StreamManager
import io

router = APIRouter()

# Inject the shared StreamManager instance
def configure_routes(stream_manager: StreamManager):
    global streamManager
    streamManager = stream_manager

@router.get("/snapshotRaw/{stream_id}")
async def get_snapshot(stream_id: str):
    try:
        stream = streamManager.get_stream(stream_id)
        if not stream:
            raise HTTPException(status_code=404, detail=f"Stream with ID {stream_id} not found")
        
        frame = await stream.grab_frame_raw()
        if frame is None:
            raise HTTPException(status_code=500, detail="Failed to grab frame from stream")
        
        return StreamingResponse(io.BytesIO(frame), media_type="image/jpeg")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.get("/snapshot/{stream_id}")
async def get_snapshot(stream_id: str):
    try:
        stream = streamManager.get_stream(stream_id)
        if not stream:
            raise HTTPException(status_code=404, detail=f"Stream with ID {stream_id} not found")
        
        frame = await stream.grab_frame()
        if frame is None:
            raise HTTPException(status_code=500, detail="Failed to grab frame from stream")
        
        return StreamingResponse(io.BytesIO(frame), media_type="image/jpeg")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.get("/computed/{stream_id}")
async def get_computed_snapshot(stream_id: str):
    try:
        stream = streamManager.get_stream(stream_id)
        if not stream:
            raise HTTPException(status_code=404, detail=f"Stream with ID {stream_id} not found")
        
        frame = await stream.grab_computed_frame()
        if frame is None:
            raise HTTPException(status_code=500, detail="Failed to grab computed frame from stream")
        
        return StreamingResponse(io.BytesIO(frame), media_type="image/jpeg")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.get("/thumbnail/{stream_id}")
async def get_thumbnail(stream_id: str):
    try:
        stream = streamManager.get_stream(stream_id)
        if not stream:
            raise HTTPException(status_code=404, detail=f"Stream with ID {stream_id} not found")
        
        frame = await stream.grab_thumbnail()
        if frame is None:
            raise HTTPException(status_code=500, detail="Failed to grab thumbnail from stream")
        
        return StreamingResponse(io.BytesIO(frame), media_type="image/jpeg")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))