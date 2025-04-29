from fastapi import APIRouter
from fastapi.responses import HTMLResponse
import json
from backend.StreamManager import StreamManager
from pathlib import Path

router = APIRouter(prefix="/dashboard")

def configure_routes(stream_manager: StreamManager):
    global streamManager
    streamManager = stream_manager


@router.get("/", response_class=HTMLResponse)
async def dashboard():
    """
    Serve the dashboard HTML page.
    """
    html_file_path = Path(__file__).parent / "../../frontend/static/www/html/index.html"
    html_file_path = html_file_path.resolve()  # Resolve to an absolute path
    
    return html_file_path.read_text()
