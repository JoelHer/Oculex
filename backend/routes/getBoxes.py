from fastapi import APIRouter
from fastapi.responses import JSONResponse
import json
from backend.StreamManager import StreamManager


router = APIRouter(prefix="/get_boxes")

def configure_routes(stream_manager: StreamManager):
    global streamManager
    streamManager = stream_manager

@router.get("/{id}", response_class=JSONResponse)
def get_box_by_id(id: str):
    stream = streamManager.get_stream(id)
    if not stream:
        return JSONResponse(content={"error": "Stream not found"}, status_code=404)
    
    return JSONResponse(content=stream.get_boxes())
