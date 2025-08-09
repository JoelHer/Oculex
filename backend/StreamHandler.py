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
import time
from enum import Enum
from .ocr.OcrFactory import get_ocr_engine
import numpy as np

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
        print(f"[StreamHandler, grab_frame_raw] Trying to open the RTSP stream at {self.rtsp_url}")
        
        if self.rtsp_url.startswith("file://"):
            file_path = self.rtsp_url[7:]
            print(f"[StreamHandler] Opening file {file_path} instead of RTSP stream")
            
            # Ensure processingSettings has default values if empty
            if not self.processingSettings or len(self.processingSettings) == 0:
                print("[StreamHandler, grab_frame_raw] No processing settings found, using default values")
                self.processingSettings = {
                    "rotation": 0,
                    "contrast": 1.0,
                    "brightness": 0,
                    "crop_top": 0,
                    "crop_bottom": 0,
                    "crop_left": 0,
                    "crop_right": 0
                }
            
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
                        img = frame.to_image()           # PIL.Image in RGB
                        frame = np.array(img)            # NumPy array in RGB
                        break  # Just grab one frame
                    if frame is not None:
                        break

                if frame is not None:
                    frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                    _, buffer = cv2.imencode(".jpg", frame_bgr)
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
                await self.update_status(StreamStatus.ERROR)
                print(f"[StreamHandler] Error opening RTSP stream with url {self.rtsp_url}: {e}")
                return None

    async def grab_frame(self, displayBoxes=True, displayOcrResults=False, ocrResults=None, color=(0, 255, 0)):
        print(f"[StreamHandler, grab_frame] Trying to open the RTSP stream at {self.rtsp_url}")
        print(f"[StreamHandler, grab_frame] Current processing settings: {self.processingSettings}")
        # Ensure processingSettings has default values if empty
        if not self.processingSettings or len(self.processingSettings) == 0:
            print("[StreamHandler, grab_frame] No processing settings found, using default values")
            self.processingSettings = {
                "rotation": 0,
                "contrast": 1.0,
                "brightness": 0,
                "crop_top": 0,
                "crop_bottom": 0,
                "crop_left": 0,
                "crop_right": 0
            }

        # make sure that self.processingSettings has all required keys
        required_keys = ["rotation", "contrast", "brightness", "crop_top", "crop_bottom", "crop_left", "crop_right"]
        for key in required_keys:
            if key not in self.processingSettings:
                print(f"[StreamHandler, grab_frame] Missing processing setting: {key}, using default value")
                self.processingSettings[key] = 0 if key != "contrast" else 1.0

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
                frame = cv2.convertScaleAbs(frame, alpha=int(self.processingSettings["contrast"]), beta=int(self.processingSettings["brightness"]))

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
                    if displayOcrResults and ocrResults is not None and len(self.selectionBoxes) == len(ocrResults):
                        for box, result in zip(self.selectionBoxes, ocrResults):
                            box_top = box["box_top"]
                            box_left = box["box_left"]
                            box_width = box["box_width"]
                            box_height = box["box_height"]
                            if displayBoxes:
                                cv2.rectangle(frame, (box_left, box_top), (box_left + box_width, box_top + box_height), color, 2)
                                cv2.putText(frame, f'"{result["text"]}", {result["confidence"]}%', (box_left, box_top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
                    else:
                        for box in self.selectionBoxes:
                            box_top = box["box_top"]
                            box_left = box["box_left"]
                            box_width = box["box_width"]
                            box_height = box["box_height"]
                            if displayBoxes:
                                cv2.rectangle(frame, (box_left, box_top), (box_left + box_width, box_top + box_height), color, 2)
                                cv2.putText(frame, f'ID: {box["id"]}', (box_left, box_top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)


            
            
            if frame is not None:
                frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                _, buffer = cv2.imencode(".jpg", frame_bgr)
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
        os.makedirs(f"{CACHE_DIR}/thumbnails/", exist_ok=True)
        cache_path = f"{CACHE_DIR}/thumbnails/{self.id}.jpg"

        # Check if thumbnail exists
        if os.path.exists(cache_path):
            file_age_seconds = time.time() - os.path.getmtime(cache_path)
            if file_age_seconds > 3600:  # older than 1 hour
                print(f"[StreamHandler] Thumbnail \"{self.id}.jpg\" is stale, deleting")
                os.remove(cache_path)
            else:
                print(f"[StreamHandler] Thumbnail \"{self.id}.jpg\" already exists, loading from cache instead")
                thumbnail = cv2.imread(cache_path)
                _, buffer = cv2.imencode(".jpg", thumbnail)
                return buffer.tobytes()

        # If we get here, we need to generate a new one
        frame_bytes = await self.grab_frame_raw()
        if frame_bytes is None:
            await self.update_status(StreamStatus.ERROR)
            return None

        resized_image = create_thumbnail(frame_bytes, noDecode=True)
        if resized_image is None:
            await self.update_status(StreamStatus.ERROR)
            return None

        cv2.imwrite(cache_path, resized_image)
        success, buffer = cv2.imencode(".jpg", resized_image)
        if not success:
            print("[StreamHandler] Failed to encode thumbnail JPEG")
            await self.update_status(StreamStatus.ERROR)
            return None

        await self.update_status(StreamStatus.OK)
        return buffer.tobytes()
        
    async def delete_cache(self):
        cache_path = os.path.join(CACHE_DIR, "thumbnails", f"{self.id}.jpg")
        if os.path.exists(cache_path):
            os.remove(cache_path)
            print(f"[StreamHandler] Cache for stream {self.id} deleted.")
        else:
            print(f"[StreamHandler] No cache found for stream {self.id}.")

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


    async def run_ocr(self):
        def decode_jpeg_to_array(jpeg_bytes):
            nparr = np.frombuffer(jpeg_bytes, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            if img is None:
                raise ValueError("Failed to decode JPEG bytes to image")
            return img
        try:
            stitched_jpeg = await self.grab_computed_frame()
            if stitched_jpeg is None:
                await self.update_status(StreamStatus.ERROR)
                raise RuntimeError("Failed to grab computed frame for OCR")

            stitched_img = decode_jpeg_to_array(stitched_jpeg)
        except Exception as e:
            await self.update_status(StreamStatus.ERROR)
            raise RuntimeError(f"Failed to get computed frame for OCR: {e}")

        # Now split stitched image into snippets per selection box
        try:
            # Compute widths of each box
            widths = [box["box_width"] for box in self.selectionBoxes]
            heights = [box["box_height"] for box in self.selectionBoxes]

            # Since you resized all snippets to same height when stitching,
            # we use the stitched image height as height for all.
            height = stitched_img.shape[0]

            snippets = []
            x_offset = 0
            for w in widths:
                snippet = stitched_img[0:height, x_offset:x_offset + w]
                snippets.append(snippet)
                x_offset += w

            if not snippets:
                await self.update_status(StreamStatus.ERROR)
                raise RuntimeError("No valid boxes after splitting stitched image")
        except Exception as e:
            await self.update_status(StreamStatus.ERROR)
            raise RuntimeError(f"Splitting stitched image failed: {e}")

        # Run OCR as before
        engine_type = self.processingSettings.get("ocrEngine", "easyocr")
        ocr_config = self.processingSettings.get("ocrConfig", {})
        engine = get_ocr_engine(engine_type, ocr_config)

        try:
            results = engine.recognize(snippets, config=ocr_config)
        except Exception as e:
            await self.update_status(StreamStatus.ERROR)
            raise RuntimeError(f"OCR execution failed: {e}")

        await self.update_status(StreamStatus.OK)
        return results

    async def show_ocr_results(self, ocrResults, color=(255,0,0)):
        # Try to get the latest frame with OCR results overlay
        try:
            frame_bytes = await self.grab_frame(displayBoxes=True, displayOcrResults=True, ocrResults=ocrResults, color=color)
            if frame_bytes is None:
                await self.update_status(StreamStatus.ERROR)
                return None

            np_frame = np.frombuffer(frame_bytes, np.uint8)
            image = cv2.imdecode(np_frame, cv2.IMREAD_COLOR)
            if image is None:
                await self.update_status(StreamStatus.ERROR)
                return None

            await self.update_status(StreamStatus.OK)
            return frame_bytes
        except Exception as e:
            await self.update_status(StreamStatus.ERROR)
            print(f"[StreamHandler] show_ocr_results error: {e}")
            return None
        



    def process_frame(self):
        # Return image with overlay
        pass

    def get_settings(self):
        return self.processingSettings
    
    def set_settings(self, settings):
    # Safely update existing settings without overwriting the entire dict
        if not hasattr(self, 'processingSettings'):
            self.processingSettings = {}
        self.processingSettings.update(settings)


    def get_boxes(self):
        return self.selectionBoxes
    
    def set_boxes(self, boxes):
        self.selectionBoxes = boxes

    def set_streamID(self, stream_id):
        self.id = stream_id

