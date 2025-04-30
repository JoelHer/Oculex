import os
from fastapi import FastAPI, WebSocket
from fastapi.staticfiles import StaticFiles
from backend.routes import getImage, helloworld, interface, getBoxes, setBoxes, getSettings, setSettings, dashboard, streams, preview
import uuid
from backend.StreamManager import StreamManager
from backend.WebSocketManager import WebSocketManager
import json
import sys
import asyncio

HttpServer = FastAPI()
ws_manager = WebSocketManager()

ws_connections = []
@HttpServer.websocket("/ws/streamstatus")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    ws_connections.append(websocket)
    await ws_manager.register(websocket)

    try:
        while True:
            await asyncio.sleep(60)
    except Exception:
        print("Client disconnected")
    finally:
        await ws_manager.unregister(websocket)
        ws_connections.remove(websocket)

async def notify_status_change(stream_id: str, new_status: str):
    message = {"streamid": stream_id, "status": new_status}
    for websocket in ws_connections:
        await websocket.send_json(message)

settings = {}
with open("/data/settings.json", "r") as file:
    settings = json.load(file)

boxes = {}
with open("/data/boxes.json", "r") as file:
    boxes = json.load(file)

streamManager = StreamManager(verbose_logging=True, ws_manager=ws_manager)
previewStreamManager = StreamManager(verbose_logging=True, ws_manager=ws_manager)
#streamManager.add_stream("a", "rtsp://admin:herbstnvr@10.250.100.88:554/ch01.264", {"configValue": "12"}, settings, boxes)
streamManager.load_streams("/data/streams.json")
streamManager.store_streams("/data/streams.json")

# Configure snapshot routes with the shared StreamManager
getImage.configure_routes(streamManager)
getSettings.configure_routes(streamManager)
setSettings.configure_routes(streamManager)
setBoxes.configure_routes(streamManager)
getBoxes.configure_routes(streamManager)
dashboard.configure_routes(streamManager)
streams.configure_routes(streamManager)
preview.configure_routes(previewStreamManager)

HttpServer.include_router(helloworld.router)
HttpServer.include_router(interface.router)
HttpServer.include_router(getBoxes.router)
HttpServer.include_router(setBoxes.router)
HttpServer.include_router(getSettings.router)
HttpServer.include_router(getImage.router)
HttpServer.include_router(setSettings.router)
HttpServer.include_router(dashboard.router)
HttpServer.include_router(streams.router)
HttpServer.include_router(preview.router)

static_path = os.path.join(os.path.dirname(__file__), "../frontend/static")
dashboard_build_path = os.path.join(os.path.dirname(__file__), "../frontend/static/www/compiled")
if not os.path.exists(static_path):
    raise RuntimeError(f"Directory '{static_path}' does not exist")

if not os.path.exists(dashboard_build_path):
    raise RuntimeError(f"Directory '{dashboard_build_path}' does not exist")


if not os.path.exists(static_path):
    raise RuntimeError(f"Directory '{static_path}' does not exist")

# Expose static files of the static directory under the /static route
HttpServer.mount("/static", StaticFiles(directory=static_path), name="static")




# Mount the dashboard build for Vite 
HttpServer.mount("/dashboard/assets", StaticFiles(directory=os.path.join(dashboard_build_path, "assets")), name="dashboard-assets")
HttpServer.mount("/dashboard", StaticFiles(directory=dashboard_build_path), name="dashboard-static")