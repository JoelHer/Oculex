from fastapi import APIRouter, Body
from fastapi.responses import JSONResponse
from typing import List
import json
import os
from backend.StreamManager import StreamManager

router = APIRouter(prefix="/set_boxes")

def configure_routes(stream_manager: StreamManager):
    global streamManager
    streamManager = stream_manager


static_path = "/data/boxes.json"

@router.post("/{id}", response_class=JSONResponse)
def set_box_by_id(id: str, boxes: List[dict] = Body(...)):
    stream = streamManager.get_stream(id)
    if not stream:
        return JSONResponse(content={"error": "Stream not found"}, status_code=404)
    stream.set_boxes(boxes)
    try:
        with open(static_path, "w") as file:
            json.dump(boxes, file, indent=4)
        return JSONResponse(content={"message": "Boxes saved successfully"})
    except Exception as e:
        print(f"[setBoxes]: Error saving boxes: {e}")
        return JSONResponse(content={"error": str(e)}, status_code=500)
