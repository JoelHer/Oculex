from fastapi import APIRouter, Body
from fastapi.responses import JSONResponse
import json
import os
from backend.StreamManager import StreamManager

router = APIRouter(prefix="/set_settings")

def configure_routes(stream_manager: StreamManager):
    global streamManager
    streamManager = stream_manager


settings_path = "/data/settings.json"

@router.post("/", response_class=JSONResponse)
def save_settings(settings: dict = Body(...)):
    """
    Save settings to the settings.json file.
    """
    try:
        # Ensure the directory exists
        os.makedirs(os.path.dirname(settings_path), exist_ok=True)
        
        # Save settings to the file
        with open(settings_path, "w") as file:
            json.dump(settings, file, indent=4)
        
        return JSONResponse(content={"message": "Settings saved successfully"})
    except Exception as e:
        print(f"[setSettings]: Error saving settings: {e}")
        return JSONResponse(content={"error": str(e)}, status_code=500)
    

@router.post("/{id}", response_class=JSONResponse)
def set_settings_by_id(id: str, settings: dict = Body(...)):
    """
    Get settings by stream ID.
    """
    stream = streamManager.get_stream(id)
    if not stream:
        return JSONResponse(content={"error": "Stream not found"}, status_code=404)
    
    stream.set_settings(settings)
    return JSONResponse(content=stream.get_settings())