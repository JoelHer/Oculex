from fastapi import APIRouter

router = APIRouter(prefix="/hello")

@router.get("/")
def read_root():
    return {"Hello": "World"}
