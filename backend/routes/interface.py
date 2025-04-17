from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from pathlib import Path

router = APIRouter(prefix="")

@router.get("/", response_class=HTMLResponse)
def returnHomepage():
    html_file_path = Path(__file__).parent / "../../frontend/templates/index.html"
    html_file_path = html_file_path.resolve()  # Resolve to an absolute path
    
    return html_file_path.read_text()