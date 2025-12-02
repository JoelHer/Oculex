import os
from fastapi import FastAPI, WebSocket
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from backend.routes import getImage, helloworld, getBoxes, setBoxes, getSettings, setSettings, dashboard, streams, preview
import uuid
from backend.StreamManager import StreamManager
from backend.StreamHandler import StreamHandler
from backend.WebSocketManager import WebSocketManager
from backend.SchedulingManager import SchedulingManager
from backend.DatabaseManager import DatabaseManager
import json
import sys
import asyncio

HttpServer = FastAPI()
ws_manager = WebSocketManager()
db_manager = DatabaseManager(db_path="/data/database/app.db", migrations_dir="./backend/DBMigrations")

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

streamManager = StreamManager(verbose_logging=True, ws_manager=ws_manager, db_manager=db_manager)
previewStreamManager = StreamManager(verbose_logging=True, ws_manager=ws_manager, db_manager=db_manager)
#streamManager.add_stream("a", "rtsp://admin:herbstnvr@10.250.100.88:554/ch01.264", {"configValue": "12"}, settings, boxes)
streamManager.load_streams("/data/streams.json")
streamManager.store_streams("/data/streams.json")

scheduler = SchedulingManager(streamManager)
for stream in streamManager.streams.values():
    if stream.get_scheduling_settings().get("execution_mode", "manual") == "interval" and stream.get_scheduling_settings().get("cron_expression", None):
        scheduler.add_job(stream.get_scheduling_settings().get("cron_expression", None), stream.id)
streamManager.scheduler = scheduler
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
HttpServer.include_router(getBoxes.router)
HttpServer.include_router(setBoxes.router)
HttpServer.include_router(getSettings.router)
HttpServer.include_router(getImage.router)
HttpServer.include_router(setSettings.router)
HttpServer.include_router(dashboard.router)
HttpServer.include_router(streams.router)
HttpServer.include_router(preview.router)

print(f"Current execution path: {os.getcwd()}")

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


# Redirect root to the dashboard
@HttpServer.get("/", include_in_schema=False)
async def root_redirect():
    return RedirectResponse(url="/dashboard", status_code=302)


@HttpServer.on_event("startup")
async def startup_event():
    # Start routines after FastAPI's event loop is running
    for handler in streamManager.streams.values():
        handler.start_routine()
    ws_manager.loop = asyncio.get_running_loop()
    scheduler.start()