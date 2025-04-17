from fastapi import APIRouter
from fastapi.responses import JSONResponse
import json

router = APIRouter(prefix="/get_settings")

@router.get("/", response_class=JSONResponse)
def get_settings():
    with open("/data/settings.json", "r") as file:
        boxes = json.load(file)
    return JSONResponse(content=boxes)