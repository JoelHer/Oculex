from fastapi import APIRouter
from fastapi.responses import JSONResponse
import json
import os

router = APIRouter(prefix="/set_boxes")

static_path = os.path.join(os.path.dirname(__file__), "../frontend/static")

@router.get("/{id}", response_class=JSONResponse)
def set_box_by_id(id: int, boxes: list):
    print("Saving boxes:", boxes)
    return json.loads(save_boxes(boxes).body)

@router.post("/", response_class=JSONResponse)
def save_boxes(boxes: list):
    print("Saving boxes:", boxes)
    try:
        with open(static_path, "w") as file:
            json.dump(boxes, file, indent=4)
        return JSONResponse(content={"message": "Boxes saved successfully"})
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)
