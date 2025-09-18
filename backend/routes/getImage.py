from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
import io
import asyncio
from concurrent.futures import ThreadPoolExecutor  # <-- not ProcessPoolExecutor!
from backend.StreamManager import StreamManager

router = APIRouter()

# Use thread pool instead of process pool
executor = ThreadPoolExecutor(max_workers=10)

def configure_routes(stream_manager: StreamManager):
    global streamManager
    streamManager = stream_manager

async def run_in_thread(func, *args):
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(executor, func, *args)

# Helper function must be pure sync
def grab_frame_by_id_sync(stream_id: str, mode: str):
    stream = streamManager.get_stream(stream_id)
    if not stream:
        raise Exception(f"Stream with ID {stream_id} not found")
    
    if mode == "raw":
        return asyncio.run(stream.grab_frame_raw())  # important: run async method synchronously
    elif mode == "normal":
        return asyncio.run(stream.grab_frame())
    elif mode == "computed":
        return asyncio.run(stream.grab_computed_frame())
    elif mode == "thumbnail":
        return asyncio.run(stream.grab_thumbnail())
    else:
        raise Exception(f"Unknown mode '{mode}'")

async def get_frame_response(stream_id: str, mode: str):
    try:
        frame = await run_in_thread(grab_frame_by_id_sync, stream_id, mode)
        if frame is None:
            raise HTTPException(status_code=500, detail="Failed to grab frame from stream")
        
        return StreamingResponse(io.BytesIO(frame), media_type="image/jpeg")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Routes
@router.get("/snapshotRaw/{stream_id}")
async def get_snapshot_raw(stream_id: str):
    return await get_frame_response(stream_id, "raw")

@router.get("/snapshot/{stream_id}")
async def get_snapshot(stream_id: str):
    return await get_frame_response(stream_id, "normal")

@router.get("/computed/{stream_id}")
async def get_computed_snapshot(stream_id: str):
    return await get_frame_response(stream_id, "computed")

@router.get("/thumbnail/{stream_id}")
async def get_thumbnail(stream_id: str):
    return await get_frame_response(stream_id, "thumbnail")