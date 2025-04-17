from fastapi import APIRouter
from fastapi.responses import JSONResponse
import json

router = APIRouter(prefix="/get_boxes")

@router.get("/", response_class=JSONResponse)
def read_root():
    with open("/data/boxes.json", "r") as file:
        boxes = json.load(file)
    return JSONResponse(content=boxes)

@router.get("/{id}", response_class=JSONResponse)
def get_box_by_id(id: int):
    return json.loads(read_root().body)
