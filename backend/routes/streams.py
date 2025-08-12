from fastapi import APIRouter , HTTPException, Body
from fastapi.responses import JSONResponse, StreamingResponse
import json
from backend.StreamManager import StreamManager
from pathlib import Path
from pydantic import BaseModel
import re
import io
from typing import Optional
from fastapi import Query

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
        "selectionBoxes": stream_handler.selectionBoxes,
        "status": stream_handler.status,
    }
    
    return JSONResponse(content=stream_info)

@router.delete("/{stream_id}", response_class=JSONResponse)
async def delete_stream(stream_id: str):
    """
    Delete a stream.
    """
    stream_handler = streamManager.get_stream(stream_id)
    if not stream_handler:
        return JSONResponse(status_code=404, content={"error": "Stream not found"})
    
    streamManager.delete_stream(stream_id)
    streamManager.store_streams()
    
    return JSONResponse(status_code=200, content={"success": True})


class StreamModel(BaseModel):
    name: str
    stream_src: str | None = "rtsp://user:password@host/h264"

@router.post("/add", response_class=JSONResponse)
async def add_stream(stream: StreamModel):
    pattern = re.compile("^[a-zA-Z0-9-_]{3,35}$")
    print(stream)
    if pattern.match(stream.name):
        streamManager.add_stream(stream.name,stream.stream_src,None,[],{},[])
        streamManager.store_streams()
        return JSONResponse(status_code=200, content={"success": True})
    else:
        return JSONResponse(status_code=406, content={"error": "Illegal characters"}) # 406 Not Acceptable, This response is sent when the web server, after performing server-driven content negotiation, doesn't find any content that conforms to the criteria given by the user agent.

@router.put("/{stream_id}", response_class=JSONResponse)
async def update_stream(stream_id: str, stream: StreamModel):
    """
    Update the details of a specific stream.
    """
    stream_handler = streamManager.get_stream(stream_id)
    if not stream_handler:
        return JSONResponse(status_code=404, content={"error": "Stream not found"})
    
    # Update the stream handler with new values
    stream_handler.rtsp_url = stream.stream_src
    print(f"Updating stream {stream_id} with URL: {stream.stream_src} and name: {stream.name}")
    stream_handler.set_streamID(stream.name)
    
    # Save the updated streams
    streamManager.store_streams()
    stream_handler.delete_cache()
    
    return JSONResponse(status_code=200, content={"success": True})


@router.get("/{stream_id}/ocr")
async def ocr_stream(stream_id: str):
    handler = streamManager.get_stream(stream_id)
    if handler is None:
        raise HTTPException(status_code=404, detail="Stream not found")
    
    try:
        results = await handler.run_ocr()
        return {"results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OCR failed: {e}")
    
@router.get("/{stream_id}/ocr-withimage")
async def ocr_stream(
    stream_id: str
):
    
    color = streamManager.get_stream(stream_id).get_ocrsettings().get("ocr_color", "#00ff33")
    

    if color:
        if not re.match(r'^#([0-9a-fA-F]{3}|[0-9a-fA-F]{6})$', color):
            raise HTTPException(status_code=400, detail="Invalid color format. Use hex format like '#FF0000'.")
        color = tuple(int(color.lstrip('#')[i:i+2], 16) for i in (0, 2, 4)) if len(color) == 7 else tuple(int(color.lstrip('#')[i]*2, 16) for i in (0, 1, 2))

    handler = streamManager.get_stream(stream_id)
    if handler is None:
        raise HTTPException(status_code=404, detail="Stream not found")
    
    try:
        results = await handler.run_ocr()
        frame = await handler.show_ocr_results(results, color=color)
        if frame is None:
            raise HTTPException(status_code=500, detail="Failed to grab frame from stream")
        
        return StreamingResponse(io.BytesIO(frame), media_type="image/jpeg")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OCR failed: {e}")
    
@router.post("/{id}/ocr-settings", response_class=JSONResponse)
def set_settings_by_id(id: str, settings: dict = Body(...)):
    """
    Set ocr settings by stream ID.
    """
    stream = streamManager.get_stream(id)
    if not stream:
        return JSONResponse(content={"error": "Stream not found"}, status_code=404)
    
    stream.set_ocrsettings(settings)
    streamManager.save_stream(stream)
    return JSONResponse(content=stream.get_ocrsettings())

@router.get("/{id}/ocr-settings", response_class=JSONResponse)
def set_settings_by_id(id: str):
    """
    Get ocr settings by stream ID.
    """
    stream = streamManager.get_stream(id)
    if not stream:
        return JSONResponse(content={"error": "Stream not found"}, status_code=404)
    
    settings = stream.get_ocrsettings()
    if not settings:
        return JSONResponse(content={"error": "No OCR settings found for this stream"}, status_code=404)
    
    return JSONResponse(content=settings)
    