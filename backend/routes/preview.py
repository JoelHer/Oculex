from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from backend.StreamManager import StreamManager
from concurrent.futures import ProcessPoolExecutor
import io
import base64
import cv2
import numpy as np
import av
import asyncio

executor = ProcessPoolExecutor(max_workers=4)
router = APIRouter(prefix="/preview")

# Inject the shared StreamManager instance
def configure_routes(stream_manager: StreamManager):
    global streamManager
    streamManager = stream_manager

# Async wrapper for running sync CPU-bound tasks in a process
async def run_in_process(fn, *args):
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(executor, fn, *args)

# Make this a sync function (must be for use in process pool)
def grab_frame_raw_sync(uri: str) -> bytes | None:
    if uri.startswith("file://"):
        file_path = uri[7:]
        print(f"[PreviewStreamHandler] Opening file {file_path} instead of RTSP stream")

        try:
            container = av.open(file_path)
            for packet in container.demux(video=0):
                for frame in packet.decode():
                    img = frame.to_image()
                    np_img = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
                    _, buffer = cv2.imencode(".jpg", np_img)
                    return buffer.tobytes()
        except Exception as e:
            print(f"[PreviewStreamHandler] Error opening file {file_path}: {e}")
            return None

    else:
        try:
            print(f"[PreviewStreamHandler] Trying to open RTSP stream at {uri}")
            container = av.open(uri, options={"rtsp_transport": "tcp"})
            for packet in container.demux(video=0):
                for frame in packet.decode():
                    img = frame.to_image()
                    np_img = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
                    _, buffer = cv2.imencode(".jpg", np_img)
                    return buffer.tobytes()
        except Exception as e:
            print(f"[PreviewStreamHandler] Error opening RTSP stream at {uri}: {e}")
            return None

@router.get("/{stream_source_uri}")
async def get_thumbnail(stream_source_uri: str):
    try:
        decoded_uri = base64.b64decode(stream_source_uri).decode('UTF-8')
        img_bytes = await run_in_process(grab_frame_raw_sync, decoded_uri)
        if img_bytes is None:
            raise HTTPException(status_code=500, detail="Failed to grab frame")
        return StreamingResponse(io.BytesIO(img_bytes), media_type="image/jpeg")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
