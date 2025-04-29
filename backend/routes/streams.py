from fastapi import APIRouter
from fastapi.responses import JSONResponse
import json
from backend.StreamManager import StreamManager
from pathlib import Path

router = APIRouter(prefix="/streams")

def configure_routes(stream_manager: StreamManager):
    global streamManager
    streamManager = stream_manager

@router.get("/", response_class=JSONResponse)
async def get_streams():
    """
    Get the list of active streams.
    """
    stream_ids = streamManager.list_streams()
    return JSONResponse(content={"streams": stream_ids})

@router.get("/{stream_id}", response_class=JSONResponse)
async def get_stream(stream_id: str):
    """
    Get the details of a specific stream.
    """
    stream_handler = streamManager.get_stream(stream_id)
    if not stream_handler:
        return JSONResponse(status_code=404, content={"error": "Stream not found"})
    
    stream_info = {
        "rtsp_url": stream_handler.rtsp_url,
        "config": stream_handler.config,
        "processingSettings": stream_handler.processingSettings,
        "selectionBoxes": stream_handler.selectionBoxes
    }
    
    return JSONResponse(content=stream_info)
