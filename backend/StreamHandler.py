#StreamHandler
#    Manages one RTSP stream.
#    Has its own:
#        Frame grabber
#        Processing pipeline
#        Config

import cv2
import av
import numpy as np
import os
from enum import Enum

class StreamStatus(str, Enum):
    """Enum for stream status."""
    OK = "OK"
    ERROR = "ERROR"
    NO_STREAM = "NO_STREAM"
    NO_CONNECTION = "NO_CONNECTION"
    TIMEOUT = "TIMEOUT"
    UNKNOWN = "UNKNOWN"

def create_thumbnail(frame_bytes, target_width=320, target_height=240, noDecode=False):
    if frame_bytes is None:
        return None
    
    nparr = np.frombuffer(frame_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    if img is None:
        print("[StreamHandler] Failed to decode JPEG")
        return None
    
    height, width = img.shape[:2]
    target_width = 320
    target_height = 240

    aspect_ratio = width / height

    if (target_width / target_height) > aspect_ratio:
        new_height = target_height
        new_width = int(aspect_ratio * target_height)
    else:
        new_width = target_width
        new_height = int(target_width / aspect_ratio)
    
    resized_img = cv2.resize(img, (new_width, new_height), interpolation=cv2.INTER_AREA)

    if noDecode:
        return resized_img

    success, buffer = cv2.imencode(".jpg", resized_img)
    if not success:
        print("[StreamHandler] Failed to encode thumbnail JPEG")
        return None
    
    return buffer.tobytes()

CACHE_DIR = "/data/cache"

class StreamHandler:
    def __init__(self, stream_id, rtsp_url, config, processingSettings, selectionBoxes, ws_manager=None):
        self.id = stream_id
        self.rtsp_url = rtsp_url
        self.config = config
        self.processingSettings = processingSettings
        self.selectionBoxes = selectionBoxes
        self.frame = None
        self.status = StreamStatus.UNKNOWN
        self.ws_manager = ws_manager
        # Init grabbing, OCR, etc.

    async def grab_frame_raw(self):
        print(f"[StreamHandler] Trying to open the RTSP stream at {self.rtsp_url}")
        
        if self.rtsp_url.startswith("file://"):
            file_path = self.rtsp_url[7:]
            print(f"[StreamHandler] Opening file {file_path} instead of RTSP stream")
            
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
                    await self.update_status(StreamStatus.OK)
                    resized_image = create_thumbnail(buffer, noDecode=True)
                    cv2.imwrite(f"{CACHE_DIR}/thumbnails/{self.id}.jpg", resized_image)
                    if self.ws_manager:
                        await self.ws_manager.broadcast({
                            "type": "stream/thumbnail_update",
                            "stream_id": self.id,
                            "status": self.status
                        })
                    return buffer.tobytes()
                else:
                    await self.update_status(StreamStatus.NO_STREAM)
                    print(f"[StreamHandler] No frames found in the file {file_path}")
                    return None

            except Exception as e:
                await self.update_status(StreamStatus.ERROR)
                print(f"[StreamHandler] Error opening file {file_path}: {e}")
                return None

        else:
            try:
                container = av.open(self.rtsp_url, options={"rtsp_transport": "tcp"})
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
                    await self.update_status(StreamStatus.OK)
                    resized_image = create_thumbnail(buffer, noDecode=True)
                    cv2.imwrite(f"{CACHE_DIR}/thumbnails/{self.id}.jpg", resized_image)
                    if self.ws_manager:
                        await self.ws_manager.broadcast({
                            "type": "stream/thumbnail_update",
                            "stream_id": self.id,
                            "status": self.status
                        })
                    return buffer.tobytes()
                else:
                    await self.update_status(StreamStatus.NO_STREAM)
                    print(f"[StreamHandler] No frames found in the RTSP stream at {self.rtsp_url}")
                    return None

            except Exception as e:
                await self.update_status(StreamStatus.NO_STREAM)
                print(f"[StreamHandler] Error opening RTSP stream with url {self.rtsp_url}: {e}")
                return None

    async def grab_frame(self, displayBoxes=True):
        print(f"[StreamHandler] Trying to open the RTSP stream at {self.rtsp_url}")
        try:
            # Use av.open with RTSP options
            container = av.open(self.rtsp_url, options={"rtsp_transport": "tcp"})
            frame = None
            for packet in container.demux(video=0):
                for frame in packet.decode():
                    img = frame.to_image()  # Convert frame to PIL Image
                    frame = np.array(img)   # Convert to NumPy array
                    break  # Just grab one frame
                if frame is not None:
                    break

            if self.processingSettings["rotation"] != 0 and frame is not None:
                (h, w) = frame.shape[:2]
                center = (w // 2, h // 2)
                matrix = cv2.getRotationMatrix2D(center, self.processingSettings["rotation"], 1.0)
                frame = cv2.warpAffine(frame, matrix, (w, h))

            # Apply contrast & brightness
            if frame is not None:
                frame = cv2.convertScaleAbs(frame, alpha=self.processingSettings["contrast"], beta=self.processingSettings["brightness"])

            # Apply cropping
            if frame is not None:
                h, w, _ = frame.shape
                top = min(self.processingSettings["crop_top"], h)
                bottom = max(h - self.processingSettings["crop_bottom"], 0)
                left = min(self.processingSettings["crop_left"], w)
                right = max(w - self.processingSettings["crop_right"], 0)
                frame = frame[top:bottom, left:right]

            # Draw self.selectionBoxes on the image
            if frame is not None:
                if self.selectionBoxes is not None and len(self.selectionBoxes) > 0:
                    for box in self.selectionBoxes:
                        box_top = box["box_top"]
                        box_left = box["box_left"]
                        box_width = box["box_width"]
                        box_height = box["box_height"]
                        color = (0, 255, 0)  # Default color
                        if displayBoxes:
                            cv2.rectangle(frame, (box_left, box_top), (box_left + box_width, box_top + box_height), color, 2)
                            cv2.putText(frame, f'ID: {box["id"]}', (box_left, box_top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)


            
            
            if frame is not None:
                _, buffer = cv2.imencode(".jpg", frame)
                await self.update_status(StreamStatus.OK)
                return buffer.tobytes()
            else:
                await self.update_status(StreamStatus.NO_STREAM)
                print(f"[StreamHandler] No frames found in the RTSP stream at {self.rtsp_url}")
                return None

        except Exception as e:
            await self.update_status(StreamStatus.NO_CONNECTION)
            print(f"[StreamHandler] Error opening RTSP stream with url {self.rtsp_url}: {e}")
            return None

    async def grab_computed_frame(self):
        frame = await self.grab_frame(displayBoxes=False)  # Add 'await' here
        if frame is None:
            await self.update_status(StreamStatus.ERROR)
            return "Error: Could not retrieve frame", 500

        np_frame = np.frombuffer(frame, np.uint8)
        image = cv2.imdecode(np_frame, cv2.IMREAD_COLOR)

        if image is None:
            await self.update_status(StreamStatus.ERROR)
            return "Error: Could not decode frame", 500

        
        snippets = []
        for box in self.selectionBoxes:
            box_top = box["box_top"]
            box_left = box["box_left"]
            box_width = box["box_width"]
            box_height = box["box_height"]

            snippet = image[box_top:box_top + box_height, box_left:box_left + box_width]
            if snippet.size > 0:
                snippets.append(snippet)

        if not snippets:
            await self.update_status(StreamStatus.ERROR)
            return "Error: No valid boxes to process", 400

        target_height = max(snippet.shape[0] for snippet in snippets)
        resized_snippets = [cv2.resize(snippet, (snippet.shape[1], target_height)) for snippet in snippets]

        stitched_image = cv2.hconcat(resized_snippets)

        _, buffer = cv2.imencode(".jpg", stitched_image)
        await self.update_status(StreamStatus.OK)
        return buffer.tobytes()

    async def grab_thumbnail(self):
        os.makedirs(CACHE_DIR+"/thumbnails/", exist_ok=True)
        # check if f"/data/cache/thumbnails/{self.id}.jpg" exists, else create the thumbnail and save it
        if os.path.exists(f"{CACHE_DIR}/thumbnails/{self.id}.jpg"):
            print(f"[StreamHandler] Thumbnail \"{self.id}.jpg\" already exists, loading from cache instead")
            thmbnail = cv2.imread(f"{CACHE_DIR}/thumbnails/{self.id}.jpg")
            _, buffer = cv2.imencode(".jpg", thmbnail)
            return buffer.tobytes()
        frame_bytes = await self.grab_frame_raw()
        if frame_bytes is None:
            await self.update_status(StreamStatus.NO_STREAM)
            return None
        resized_image = create_thumbnail(frame_bytes, noDecode=True)
        if resized_image is None:
            await self.update_status(StreamStatus.ERROR)
            return None
        # create /data/cache/thumbnails/ directory if it doesn't exist
        cv2.imwrite(f"{CACHE_DIR}/thumbnails/{self.id}.jpg", resized_image)
        success, buffer = cv2.imencode(".jpg", resized_image)
        if not success:
            print("[StreamHandler] Failed to encode thumbnail JPEG")
            await self.update_status(StreamStatus.ERROR)
            return None
        await self.update_status(StreamStatus.OK)
        return buffer.tobytes()
        

    async def update_status(self, new_status):
        if self.status != new_status:
            print(f"[StreamHandler] Stream {self.id} status changed: {self.status} -> {new_status}")
            self.status = new_status
            if self.ws_manager:
                await self.ws_manager.broadcast({
                    "type": "stream/status_update",
                    "stream_id": self.id,
                    "status": self.status
                })

    def process_frame(self):
        # Return image with overlay
        pass

    def get_settings(self):
        return self.processingSettings
    
    def set_settings(self, settings):
        self.processingSettings = settings

    def get_boxes(self):
        return self.selectionBoxes
    
    def set_boxes(self, boxes):
        self.selectionBoxes = boxes
