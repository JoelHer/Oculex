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
from backend.globalRessources import ocr_worker
from .ocr.OcrFactory import get_ocr_engine
import numpy as np
import asyncio
import json
import re

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

def ensure_ndarray(frame):
    if isinstance(frame, np.ndarray) and frame.dtype == np.uint8:
        return frame
    if isinstance(frame, np.ndarray) and frame.dtype.kind in {'S', 'U'}:
        frame = frame.tobytes()
    if isinstance(frame, (bytes, bytearray)):
        nparr = np.frombuffer(frame, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if frame is None or not isinstance(frame, np.ndarray):
        raise ValueError("Failed to convert frame to ndarray")
    return frame

CACHE_DIR = "/data/cache"

class StreamHandler:
    async def routine(self):
        """Routine to handle stream processing."""
        print(f"[StreamHandler] Starting routine for stream {self.id}")
        while True:
            try:
                frame = await self.grab_frame_raw()
                if frame is None:
                    print(f"[StreamHandler] No frame received for stream {self.id}, updating status to NO_STREAM")
                    await self.update_status(StreamStatus.NO_STREAM)
                    await asyncio.sleep(30)
                    continue

                self.lastFrame = np.array(frame)
                self.lastFrameTimestamp = time.time()

            except Exception as e:
                print(f"[StreamHandler] Error in routine for stream {self.id}: {e}")
                await self.update_status(StreamStatus.ERROR)
                break

            await asyncio.sleep(30)

    def OCR_value_changed(old, new):
        print(f"[StreamHandler] OCR running state changed from {old} to {new}")

    def __init__(self, stream_id, rtsp_url, config, processingSettings, ocrSettings, selectionBoxes, ws_manager=None, schedulingSettings=None):
        self.id = stream_id
        self.rtsp_url = rtsp_url
        self.config = config
        self.processingSettings = processingSettings
        self.ocrSettings = ocrSettings
        self.selectionBoxes = selectionBoxes
        self.frame = None
        self.status = StreamStatus.UNKNOWN
        self.ws_manager = ws_manager
        self.lastFrame: np.ndarray = None  
        self.lastFrameTimestamp = None
        self.ocrRunning = False
        self.last_ocr_results = None
        self.last_ocr_timestamp = 0
        if schedulingSettings:
            self.schedulingSettings = schedulingSettings
        else:
            self.schedulingSettings = {
                "executionMode": "on_api_call",
                "intervalPreset": "5",
                "intervalMinutes": 5,
                "cronExpression": "",
                "cacheEnabled": True,
                "cacheDuration": 60,
                "cacheDurationUnit": "minutes",
                "deltaTracking": False,
                "deltaAmount": 0,
                "deltaTimespan": 60,
                "deltaTimespanUnit": "minutes",
            }

    def start_routine(self):
        # schedule routine without blocking
        self.routine_task = asyncio.create_task(self.routine())

    async def _grabFrameFromStream(self, url, bustCache=False, options=None):
        def grab():
            # Cache check
            if (
                self.lastFrame is not None 
                and self.lastFrameTimestamp is not None 
                and not bustCache
            ):
                current_time = time.time()
                if current_time - self.lastFrameTimestamp < 60: # CACHE 60 SECONDS
                    print(f"[StreamHandler] Returning cached frame for {url}")
                    return self.lastFrame

            frame_data = None

            # Detect if URL is actually a file (png/jpg), not a stream
            if os.path.isfile(url) and url.lower().endswith((".png", ".jpg", ".jpeg")):
                img = cv2.imread(url, cv2.IMREAD_COLOR)
                if img is None:
                    raise RuntimeError(f"Failed to load image file: {url}")
                frame_data = img
            else:
                # Normal RTSP/video handling
                container = av.open(url, options=options)
                for packet in container.demux(video=0):
                    for frame in packet.decode():
                        img = frame.to_image()
                        frame_data = np.array(img, dtype=np.uint8)  # ensure uint8
                        # Convert from RGB (PIL format) to BGR (OpenCV format) for consistency
                        frame_data = cv2.cvtColor(frame_data, cv2.COLOR_RGB2BGR)
                        break
                    if frame_data is not None:
                        break

            if frame_data is None:
                raise RuntimeError(f"No frame extracted from {url}")

            self.lastFrame = frame_data
            self.lastFrameTimestamp = time.time()
            return frame_data

        return await asyncio.to_thread(grab)


    async def grab_frame_raw(self, generateThumbnail=True):

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
                        frame = ensure_ndarray(frame)
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
                    if generateThumbnail:
                        resized_image = create_thumbnail(buffer.tobytes(), noDecode=True)
                        if resized_image is None:
                            await self.update_status(StreamStatus.ERROR)

                        os.makedirs(f"{CACHE_DIR}/thumbnails/", exist_ok=True)
                        cache_path = f"{CACHE_DIR}/thumbnails/{self.id}.jpg"

                        cv2.imwrite(cache_path, resized_image)
                        success, tBuffer = cv2.imencode(".jpg", resized_image)
                        if not success:
                            print("[StreamHandler] Failed to encode thumbnail JPEG")
                            await self.update_status(StreamStatus.ERROR)
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
                frame = await self._grabFrameFromStream(self.rtsp_url, options={"rtsp_transport": "tcp"})
            
                if frame is not None:
                    frame = ensure_ndarray(frame)
                    # Frame is already in BGR format from _grabFrameFromStream
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

                    if generateThumbnail:
                        resized_image = create_thumbnail(buffer.tobytes(), noDecode=True)
                        if resized_image is None:
                            await self.update_status(StreamStatus.ERROR)

                        os.makedirs(f"{CACHE_DIR}/thumbnails/", exist_ok=True)
                        cache_path = f"{CACHE_DIR}/thumbnails/{self.id}.jpg"

                        cv2.imwrite(cache_path, resized_image)
                        success, tBuffer = cv2.imencode(".jpg", resized_image)
                        if not success:
                            print("[StreamHandler] Failed to encode thumbnail JPEG")
                            await self.update_status(StreamStatus.ERROR)
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
        try:
            if os.path.isfile(self.rtsp_url) and self.rtsp_url.lower().endswith((".png", ".jpg", ".jpeg")):
                frame = cv2.imread(self.rtsp_url, cv2.IMREAD_COLOR)
                if frame is None:
                    raise RuntimeError(f"Failed to read static image: {self.rtsp_url}")
            else:
                frame = await self._grabFrameFromStream(self.rtsp_url, options={"rtsp_transport": "tcp"})

            if frame is None:
                await self.update_status(StreamStatus.NO_STREAM)
                print(f"[StreamHandler] No frames found at {self.rtsp_url}")
                return None
            frame = ensure_ndarray(frame)

            print(f"[StreamHandler, grab_frame] Trying to open the RTSP stream at {self.rtsp_url}")
            print(f"[StreamHandler, grab_frame] Current processing settings: {self.processingSettings}")

            if not self.processingSettings:
                self.processingSettings = {
                    "rotation": 0, "contrast": 1.0, "brightness": 0,
                    "crop_top": 0, "crop_bottom": 0, "crop_left": 0, "crop_right": 0
                }
            for key in ["rotation", "contrast", "brightness", "crop_top", "crop_bottom", "crop_left", "crop_right"]:
                if key not in self.processingSettings:
                    self.processingSettings[key] = 0 if key != "contrast" else 1.0

            if self.processingSettings["rotation"] != 0:
                h, w = frame.shape[:2]
                center = (w // 2, h // 2)
                matrix = cv2.getRotationMatrix2D(center, self.processingSettings["rotation"], 1.0)
                frame = cv2.warpAffine(frame, matrix, (w, h))

            frame = cv2.convertScaleAbs(
                frame,
                alpha=float(self.processingSettings.get("contrast", 1.0)),
                beta=float(self.processingSettings.get("brightness", 0.0))
            )

            h, w, _ = frame.shape
            top = min(self.processingSettings["crop_top"], h)
            bottom = max(h - self.processingSettings["crop_bottom"], 0)
            left = min(self.processingSettings["crop_left"], w)
            right = max(w - self.processingSettings["crop_right"], 0)
            frame = frame[top:bottom, left:right]

            if self.selectionBoxes:
                if displayOcrResults and ocrResults and len(self.selectionBoxes) == len(ocrResults):
                    for box, result in zip(self.selectionBoxes, ocrResults):
                        cv2.rectangle(frame, (box["box_left"], box["box_top"]),
                                    (box["box_left"]+box["box_width"], box["box_top"]+box["box_height"]),
                                    color, 2)
                        cv2.putText(frame, f'"{result["text"]}", {result["confidence"]}%',
                                    (box["box_left"], box["box_top"]-10),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
                else:
                    for box in self.selectionBoxes:
                        cv2.rectangle(frame, (box["box_left"], box["box_top"]),
                                    (box["box_left"]+box["box_width"], box["box_top"]+box["box_height"]),
                                    color, 2)
                        cv2.putText(frame, f'ID: {box["id"]}',
                                    (box["box_left"], box["box_top"]-10),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

            frame_bgr = frame  # Frame is already in BGR format
            _, buffer = cv2.imencode(".jpg", frame_bgr)
            await self.update_status(StreamStatus.OK)
            return buffer.tobytes()

        except Exception as e:
            await self.update_status(StreamStatus.NO_CONNECTION)
            print(f"[StreamHandler] Error opening stream {self.rtsp_url}: {e}")
            return None


    async def grab_computed_frame(self):
        frame = await self.grab_frame(displayBoxes=False) 
        if frame is None:
            await self.update_status(StreamStatus.ERROR)
            "Error: Could not retrieve frame", 500

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
        frame_bytes = await self.grab_frame_raw(False)
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

            if type(stitched_jpeg) is tuple:
                raise RuntimeError(f"Failed to grab computed frame for OCR: {stitched_jpeg[0]}, {stitched_jpeg}")    


            stitched_img = decode_jpeg_to_array(stitched_jpeg)
        except Exception as e:
            await self.update_status(StreamStatus.ERROR)
            raise RuntimeError(f"Failed to get computed frame for OCR: {e}")

        # generate fingerprint
        image_fingerprint = str(hash(stitched_jpeg))

        oldOcrData = self.getOcrResult()

        if oldOcrData.get("aggregate", {}).get("image-fingerprint") == image_fingerprint:
            print("[StreamHandler, run_ocr] Image fingerprint matches previous OCR run, skipping OCR")
            await self.update_status(StreamStatus.OK)
            return oldOcrData

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

        self.ocrRunning = True
        await self.ws_manager.broadcast({
            "type": "stream/ocr_status",
            "stream_id": self.id,
            "ocr_running": self.ocrRunning
        })

        # Run OCR as before
        engine_type = self.processingSettings.get("ocrEngine", "easyocr")
        ocr_config = self.processingSettings.get("ocrConfig", {})
        engine = get_ocr_engine(engine_type, ocr_config)

        try:
            print(f"[StreamHandler, run_ocr] Running OCR with engine: {engine.__class__.__name__}")
            results = await ocr_worker.submit(engine, snippets, ocr_config)
            await self.update_status(StreamStatus.OK)
        except Exception as e:
            await self.update_status(StreamStatus.ERROR)
            raise RuntimeError(f"OCR execution failed: {e}")

        self.ocrRunning = False
        await self.ws_manager.broadcast({
            "type": "stream/ocr_status",
            "stream_id": self.id,
            "ocr_running": self.ocrRunning
        })
        stored = self.storeOcrResult(results, image_fingerprint=image_fingerprint)
        
        return stored

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

    def storeOcrResult(self, _results, image_fingerprint="none"):
        filename = "/data/ocr.json"

        data = {}
        try:
            with open(filename, "r") as f:
                data = json.load(f)
        except FileNotFoundError:
            print(f"[StreamHandler, storeOcrResult] No previous OCR file found ({filename}). Starting fresh.")

        # Parse results
        result_text = "".join([str(r.get("text", "")) for r in _results])
        average_conf = sum(float(r.get("confidence", 0.0)) for r in _results) / max(len(_results), 1)

        numeric_str = re.sub(r"[^0-9.]", "", result_text)
        numeric_str = re.sub(r"\.(?=.*\.)", "", numeric_str)
        try:
            parsed_value = float(numeric_str) if numeric_str else 0.0
        except ValueError:
            parsed_value = 0.0

        delta_tracking_allows: bool = self.delta_tracking(
            parsed_value,
            self.schedulingSettings.get("delta_amount", 0.0),
            self.schedulingSettings.get("delta_timespan", 0) * (60 if self.schedulingSettings.get("delta_timespan_unit", "minutes") == "minutes" else 3600 if self.schedulingSettings.get("delta_timespan_unit", "minutes") == "hours" else 1)
        )

        aggregate = {
            "value": parsed_value,
            "confidence": average_conf,
            "timestamp": int(time.time()),
            "image-fingerprint": image_fingerprint
        }

        # Update storage
        data[self.id] = {
            "results": _results,
            "aggregate": aggregate
        }

        if not self.schedulingSettings.get("allow_decreasing_values", False):
            old_val = self.getOcrResult().get("aggregate", {}).get("value", None)
            if old_val is not None and old_val > aggregate["value"]:
                print(f"[StreamHandler, storeOcrResult, AD] Decreasing value not allowed for stream {self.id}: {aggregate}; reverting to old value {old_val}")
                return self.getOcrResult()
            else:
                print(f"[StreamHandler, storeOcrResult, AD_a] Value accepted for stream {self.id}: {aggregate}; new value {aggregate['value']} >= old value {old_val if old_val is not None else 'N/A'}")

        if self.schedulingSettings.get("delta_tracking", False):
            if delta_tracking_allows:
                with open(filename, "w") as f:
                    json.dump(data, f, indent=2)
                print(f"[StreamHandler, storeOcrResult, D] Stored OCR for stream {self.id}: {aggregate}")
            else:
                print(f"[StreamHandler, storeOcrResult, D_b] Delta tracking blocked storing OCR for stream {self.id}: {aggregate}")
                #return last stored value
                return self.getOcrResult()
        else:
            with open(filename, "w") as f:
                json.dump(data, f, indent=2)
            print(f"[StreamHandler, storeOcrResult, n_D] Stored OCR for stream {self.id}: {aggregate}")


        self.last_ocr_results = _results
        self.last_ocr_timestamp = int(time.time())
        return data[self.id]

    def getOcrResult(self):
        filename = "/data/ocr.json"
        try:
            with open(filename, "r") as f:
                data = json.load(f)
                if self.id in data:
                    return data[self.id]
                else:
                    return {"value": 0.0, "confidence": 0.0, "timestamp": 0}
        except FileNotFoundError:
            print(f"[StreamHandler, getOcrResult] No OCR file found ({filename}).")
            return {"value": 0.0, "confidence": 0.0, "timestamp": 0}
        except json.JSONDecodeError:
            print(f"[StreamHandler, getOcrResult] OCR file ({filename}) is corrupted.")
            return {"value": 0.0, "confidence": 0.0, "timestamp": 0}

    def process_frame(self):
        # Return image with overlay
        pass

    def get_settings(self):
        return self.processingSettings
    
    def get_ocrsettings(self):
        return self.ocrSettings
    
    def set_settings(self, settings):
        # Safely update existing settings without overwriting the entire dict
        if not hasattr(self, 'processingSettings'):
            self.processingSettings = {}
        self.processingSettings.update(settings)

    def set_ocrsettings(self, settings):
        if not hasattr(self, 'ocrSettings'):
            self.ocrSettings = {}
        self.ocrSettings.update(settings)

    def get_boxes(self):
        return self.selectionBoxes
    
    def set_boxes(self, boxes):
        self.selectionBoxes = boxes

    def set_streamID(self, stream_id):
        self.id = stream_id

    def get_last_ocr_results(self):
        if self.last_ocr_results is None:
            #load from storage
            ocr_result = self.getOcrResult()
            self.last_ocr_results = ocr_result.get("results", [])

        return self.last_ocr_results

    def get_scheduling_settings(self):
        return self.schedulingSettings

    def set_scheduling_settings(self, settings):
        if not hasattr(self, 'schedulingSettings'):
            self.schedulingSettings = {}
        self.schedulingSettings.update(settings)

    def delta_tracking(self, new_value: float, increase: float, timespan_seconds: float) -> bool:
        """
        Delta tracking is a functionality that stops the OCR from storing faulty values. 
        It compares the last stored value with the new value and if the absolute change
        (increase or decrease) is higher than the allowed delta per elapsed time, 
        it will not store the new value.
        """
        ocr_result = self.getOcrResult()
        last_aggregate = ocr_result.get("aggregate", {})

        last_value = last_aggregate.get("value")
        last_timestamp = last_aggregate.get("timestamp")

        if last_value is None or not last_timestamp:
            return True

        if last_value == new_value:
            return True

        current_time = float(time.time())
        elapsed = current_time - float(last_timestamp)

        if elapsed < 0:
            raise ValueError("Current time is earlier than last OCR timestamp, timetravel not supported")

        if timespan_seconds <= 0:
            raise ValueError("timespan_seconds must be > 0")

        # allowed change per elapsed time
        rate_per_second = float(increase) / float(timespan_seconds)
        allowed_change = rate_per_second * elapsed

        actual_change = abs(float(new_value) - float(last_value))

        return actual_change <= allowed_change
