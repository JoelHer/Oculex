print("[INFO]: Loading Libs...")
import cv2
import numpy as np
import json
from dotenv import dotenv_values
import time
import threading
import queue
import easyocr
import av
import os
import sys
import datetime
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import uvicorn
from fastapi.testclient import TestClient

print("[INFO]: Libs loaded.")

# suppresses print
class suppress_stdout_stderr:
    def __enter__(self):
        self._stdout = sys.stdout
        sys.stdout = open(os.devnull, 'w')

    def __exit__(self, exc_type, exc_val, exc_tb):
        sys.stdout.close()
        sys.stdout = self._stdout

print ("[EASYOCR]: Loading Loading EN language model...")
with suppress_stdout_stderr():
    global reader
    reader = easyocr.Reader(['en'])
print ("[EASYOCR]: EN language model loaded.")

print("[INFO]: Loading Environment Variables and Configs...")
_env = dotenv_values(".env") 

options_file = '/data/options.json'
if os.path.exists(options_file):
    with open(options_file, 'r') as f:
        config = json.load(f)
    print("HASS configuration loaded successfully.")
else:
    print(f"{options_file} not found. Ensure the add-on has been started.")

app = FastAPI()

# Set up Jinja2 templates
templates = Jinja2Templates(directory="templates")

# Mount static files for serving static content
app.mount("/static", StaticFiles(directory="static"), name="static")

OCR_RESULTS_FILE = "/data/ocr_results.json"
RTSP_URL = config.get('rtsp_url', "rtsp://user:password@ip:port/location" )
DEBUG_MODE = config.get('debug_mode', False)

print(f"[INFO]: RTSP URL: {RTSP_URL}, Debug Mode: {DEBUG_MODE}")



DISABLE_RTSP = False

if ("DISABLE_RTSP" in _env):
    DISABLE_RTSP=bool(_env["DISABLE_RTSP"])
    if (DISABLE_RTSP):
        print("[INFO]: RTSP is disabled.")

SETTINGS_FILE = "/data/settings.json"
BOXES_FILE = "/data/boxes.json"

# Standardwerte für die Einstellungen
default_settings = {
    "rotation": 0,
    "contrast": 1.0,
    "brightness": 0,
    "crop_top": 0,
    "crop_bottom": 0,
    "crop_left": 0,
    "crop_right": 0,
    "box_top": 100,
    "box_left": 100,
    "box_width": 150,
    "box_height": 150
}
print("[INFO]: Environment Variables and Configs loaded.")


def ocrThreadFunc(result_queue):
    print("[OCR]: Starting an OCR task.")
    reader = easyocr.Reader(['en'])
    result = reader.readtext('./computed.png', allowlist="0123456789")
    value = {
        "number": result[0][1],
        "certainty": result[0][2]
    }
    result_queue.put(value)
    print("[OCR]: End Task")

print("[INFO]: Starting the server...")

# Laden der Einstellungen aus einer Datei oder Nutzung der Standardwerte
def load_settings():
    try:
        with open(SETTINGS_FILE, "r") as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return default_settings

# Speichern der Einstellungen in eine Datei
def save_settings(settings):
    with open(SETTINGS_FILE, "w") as file:
        json.dump(settings, file, indent=4)

# Load the OCR results from a file or initialize with default values
def load_ocr_results():
    try:
        with open(OCR_RESULTS_FILE, "r") as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"number": None, "certainty": 0, "timestamp": None}

# Save the OCR results to a file
def save_ocr_results(results):
    with open(OCR_RESULTS_FILE, "w") as file:
        json.dump(results, file, indent=4)

# Laden der Boxen aus einer Datei oder Nutzung eines leeren Arrays
def load_boxes():
    try:
        with open(BOXES_FILE, "r") as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

# Speichern der Boxen in eine Datei
def save_boxes(boxes):
    with open(BOXES_FILE, "w") as file:
        json.dump(boxes, file, indent=4)

# Lade die Einstellungen und Boxen beim Start des Servers
settings = load_settings()
boxes = load_boxes()

def get_frame(displayBoxes=True):
    if DISABLE_RTSP:
        # Load image from file
        frame = cv2.imread("image.png")
    else:
        print(f"Trying to open the RTSP stream at {RTSP_URL}")
        try:
            # Use av.open with RTSP options
            container = av.open(RTSP_URL, options={"rtsp_transport": "tcp"})
            frame = None
            for packet in container.demux(video=0):
                for frame in packet.decode():
                    img = frame.to_image()  # Convert frame to PIL Image
                    frame = np.array(img)   # Convert to NumPy array
                    break  # Just grab one frame
                if frame is not None:
                    break
        except av.AVError as e:
            print(f"Error opening RTSP stream: {e}")
            return None
        
    # Apply rotation
    if settings["rotation"] != 0 and frame is not None:
        (h, w) = frame.shape[:2]
        center = (w // 2, h // 2)
        matrix = cv2.getRotationMatrix2D(center, settings["rotation"], 1.0)
        frame = cv2.warpAffine(frame, matrix, (w, h))

    # Apply contrast & brightness
    if frame is not None:
        frame = cv2.convertScaleAbs(frame, alpha=settings["contrast"], beta=settings["brightness"])

    # Apply cropping
    if frame is not None:
        h, w, _ = frame.shape
        top = min(settings["crop_top"], h)
        bottom = max(h - settings["crop_bottom"], 0)
        left = min(settings["crop_left"], w)
        right = max(w - settings["crop_right"], 0)
        frame = frame[top:bottom, left:right]

    # Draw boxes on the image
    if frame is not None:
        for box in boxes:
            box_top = box["box_top"]
            box_left = box["box_left"]
            box_width = box["box_width"]
            box_height = box["box_height"]
            color = (0, 255, 0)  # Default color
            if displayBoxes:
                cv2.rectangle(frame, (box_left, box_top), (box_left + box_width, box_top + box_height), color, 2)
                cv2.putText(frame, f'ID: {box["id"]}', (box_left, box_top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

        _, buffer = cv2.imencode(".jpg", frame)
        return buffer.tobytes()
    return None

@app.get('/readocr')
def readocr():
    result_queue = queue.Queue()

    def ocr_from_computed(result_queue):
        # Create a TestClient instance for testing
        client = TestClient(app)

        # Replace the Flask test_client usage with FastAPI's TestClient
        response = client.get('/computed')
        if response.status_code != 200:
            result_queue.put({"error": "Failed to retrieve computed image"})
            return

        # Decode the image from the response
        np_frame = np.frombuffer(response.content, np.uint8)  # Use 'content' instead of 'data'
        image = cv2.imdecode(np_frame, cv2.IMREAD_COLOR)
        if image is None:
            result_queue.put({"error": "Failed to decode computed image"})
            return

        result = reader.readtext(image, allowlist="0123456789")
        if not result:
            result_queue.put({"error": "No text detected"})
            return

        value = {
            "number": result[0][1],
            "certainty": result[0][2]
        }
        result_queue.put(value)

    # Start the OCR task in a separate thread
    ocr_thread = threading.Thread(target=ocr_from_computed, args=(result_queue,), daemon=True)
    ocr_thread.start()

    ocr_thread.join()

    result = result_queue.get()

    if "error" in result:
        return JSONResponse(content={"error": result["error"]}, status_code=500)

    ocr_results = load_ocr_results()

    new_number = int(result["number"])
    previous_number = int(ocr_results["number"]) if ocr_results["number"] is not None else 0
    previous_ocr_certainty = ocr_results["certainty"] if ocr_results["certainty"] is not None else 0

    if new_number < previous_number:
        return JSONResponse(content={
            "error": "OCR value cannot decrease. Expected: >= " + str(previous_number) + " Received: " + str(new_number),
            "number": previous_number,
            "certainty": previous_ocr_certainty,
            "timestamp": ocr_results["timestamp"],
            "timezone": "UTC+0"

        }, status_code=400)
    ocr_results["number"] = new_number
    ocr_results["certainty"] = result["certainty"]
    ocr_results["timestamp"] = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())

    save_ocr_results(ocr_results)

    return JSONResponse(content={
        "number": ocr_results["number"],
        "certainty": ocr_results["certainty"],
        "timestamp": ocr_results["timestamp"],
        "timezone": "UTC+0"
    })

@app.get('/cachedocr')
def cachedocr():
    ocr_results = load_ocr_results()
    if ocr_results["number"] is None:
        return JSONResponse(content={"error": "No OCR results available"}, status_code=404)

    return JSONResponse(content={
        "number": ocr_results["number"],
        "certainty": ocr_results["certainty"],
        "timestamp": ocr_results["timestamp"],
        "timezone": "UTC+0"
    })

@app.get('/snapshot')
def snapshot():
    frame = get_frame()
    if frame is None:
        return "Error: Could not retrieve frame", 500
    return Response(frame, media_type='image/jpeg')

@app.get('/computed')
def computed():
    frame = get_frame(displayBoxes=False)
    if frame is None:
        return "Error: Could not retrieve frame", 500

    np_frame = np.frombuffer(frame, np.uint8)
    image = cv2.imdecode(np_frame, cv2.IMREAD_COLOR)

    if image is None:
        return "Error: Could not decode frame", 500

    snippets = []
    for box in boxes:
        box_top = box["box_top"]
        box_left = box["box_left"]
        box_width = box["box_width"]
        box_height = box["box_height"]

        snippet = image[box_top:box_top + box_height, box_left:box_left + box_width]
        if snippet.size > 0:
            snippets.append(snippet)

    if not snippets:
        return "Error: No valid boxes to process", 400

    target_height = max(snippet.shape[0] for snippet in snippets)
    resized_snippets = [cv2.resize(snippet, (snippet.shape[1], target_height)) for snippet in snippets]

    stitched_image = cv2.hconcat(resized_snippets)

    _, buffer = cv2.imencode(".jpg", stitched_image)
    return Response(buffer.tobytes(), media_type='image/jpeg')

@app.post("/set_settings")
async def set_settings(request: Request):
    global settings
    data = await request.json()
    for key in settings:
        if key in data:
            settings[key] = data[key]
    save_settings(settings)
    return JSONResponse(content={"message": "Settings gespeichert", "settings": settings})

@app.get('/get_settings')
def get_settings():
    return JSONResponse(content=settings)

@app.post("/set_boxes")
async def set_boxes(request: Request):
    global boxes
    boxes = await request.json()
    save_boxes(boxes)
    return JSONResponse(content={"message": "Boxes gespeichert", "boxes": boxes})


@app.get('/get_boxes')
def get_boxes():
    return JSONResponse(content=boxes)

OCR_INTERVAL = config.get('ocr_interval', 60)

last_ocr_execution = time.time()

def periodic_ocr_task():
    global last_ocr_execution
    client = TestClient(app)  # Use TestClient for FastAPI
    while True:
        print("[INFO]: Triggering periodic OCR reading...")
        try:
            response = client.get('/readocr')  # Use the TestClient instance
            if response.status_code == 200:
                print("[INFO]: OCR reading successful:", response.json())
            else:
                print("[ERROR]: OCR reading failed:", response.json())
        except Exception as e:
            print("[ERROR]: Exception during periodic OCR reading:", e)
        last_ocr_execution = time.time()
        time.sleep(OCR_INTERVAL)

@app.get('/get_next_ocr_interval')
def get_next_ocr_interval():
    global last_ocr_execution
    elapsed_time = time.time() - last_ocr_execution
    remaining_time = max(OCR_INTERVAL - elapsed_time, 0)
    return JSONResponse(content={
        "next_ocr_in_seconds": remaining_time,
        "last_execution_time": datetime.datetime.utcfromtimestamp(last_ocr_execution).strftime('%Y-%m-%d %H:%M:%S UTC')
    })

@app.post("/set_ocr_interval")
async def set_ocr_interval(request: Request):
    global OCR_INTERVAL
    data = await request.json()
    if (
        "ocr_interval" in data
        and isinstance(data["ocr_interval"], int)
        and data["ocr_interval"] > 0
    ):
        OCR_INTERVAL = data["ocr_interval"]
        print(f"[INFO]: OCR interval updated to {OCR_INTERVAL} seconds.")
        return JSONResponse(content={"message": "OCR interval updated", "ocr_interval": OCR_INTERVAL})
    return JSONResponse(content={"error": "Invalid OCR interval"}, status_code=400)

ocr_thread = threading.Thread(target=periodic_ocr_task, daemon=True)
ocr_thread.start()

@app.get('/', response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=5000, reload=False)
