from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.concurrency import run_in_threadpool
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
    

async def run_in_process(fn, *args):
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(executor, fn, *args)

@router.get("/{stream_source_uri}")
async def get_thumbnail(stream_source_uri: str):
    try:
        img = await run_in_process(grab_frame_raw, base64.b64decode(stream_source_uri).decode('UTF-8'))
        return StreamingResponse(io.BytesIO(img), media_type="image/jpeg")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def grab_frame_raw(uri): # TODO FIX HUGE SECURITY LIABILITY ASAP
    if uri.startswith("file://"):
        file_path = uri[7:]
        print(f"[PreviewStreamHandler] Opening file {file_path} instead of RTSP stream")
        
        try:
            container = av.open(file_path)
            frame = None
            for packet in container.demux(video=0):
                for frame in packet.decode():
                    img = frame.to_image()  # Convert frame to PIL Image
                    frame = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)  # Convert to NumPy array (BGR)
                    break  # Grab only one frame
                if frame is not None:
                    break

            if frame is not None:
                _, buffer = cv2.imencode(".jpg", frame)
                return buffer.tobytes()
            else:
                print(f"[PreviewStreamHandler] No frames found in the file {file_path}")
                return None

        except Exception as e:
            print(f"[PreviewStreamHandler] Error opening file {file_path}: {e}")
            return None
    else:
        try:
            print(f"[PreviewStreamHandler] Trying to open the RTSP stream at {uri}")
            container = av.open(uri, options={"rtsp_transport": "tcp"}) # make this an option
            frame = None
            for packet in container.demux(video=0):
                for frame in packet.decode():
                    img = frame.to_image()  # Convert frame to PIL Image
                    frame = np.array(img)   # Convert to NumPy array
                    break  # Just grab one frame
                if frame is not None:
                    break

            if frame is not None:
                _, buffer = cv2.imencode(".jpg", frame)
                return buffer.tobytes()
            else:
                print(f"[PreviewStreamHandler] No frames found in the RTSP stream at {uri}")
                return None

        except Exception as e:
            print(f"[PreviewStreamHandler] Error opening RTSP stream with url {uri}: {e}")
            return None
    
