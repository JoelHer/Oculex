import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from backend.routes import getImage, helloworld, interface, getBoxes, setBoxes, getSettings, setSettings
import uuid
from backend.StreamManager import StreamManager
import json
from backend.database.createdb import create_db
from backend.database.session import SessionLocal
from backend.database.models import Stream, StreamSettings, SelectionBox

create_db()

HttpServer = FastAPI()

settings = {}
with open("/data/settings.json", "r") as file:
    settings = json.load(file)

boxes = {}
with open("/data/boxes.json", "r") as file:
    boxes = json.load(file)

streamManager = StreamManager(SessionLocal)
#streamManager.add_stream("a", "rtsp://admin:herbstnvr@10.250.100.88:554/ch01.264", {"configValue": "12"}, settings, boxes)

# Configure snapshot routes with the shared StreamManager
getImage.configure_routes(streamManager)
getSettings.configure_routes(streamManager)
setSettings.configure_routes(streamManager)
setBoxes.configure_routes(streamManager)
getBoxes.configure_routes(streamManager)

HttpServer.include_router(helloworld.router)
HttpServer.include_router(interface.router)
HttpServer.include_router(getBoxes.router)
HttpServer.include_router(setBoxes.router)
HttpServer.include_router(getSettings.router)
HttpServer.include_router(getImage.router)
HttpServer.include_router(setSettings.router)


"""
db = SessionLocal()
try:
    stream = Stream(name="stream2", rtsp_url="rtsp://example.com")
    db.add(stream)
    db.commit()
    db.refresh(stream)
except Exception as e:
    print(f"[Backend]: Error adding stream to database: {e}")
finally:
    db.close()

"""


static_path = os.path.join(os.path.dirname(__file__), "../frontend/static")

if not os.path.exists(static_path):
    raise RuntimeError(f"Directory '{static_path}' does not exist")

# Expose static files of the static directory under the /static route
HttpServer.mount("/static", StaticFiles(directory=static_path), name="static")