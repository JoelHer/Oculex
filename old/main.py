import cv2
import pytesseract
import os
import time
import threading
from flask import Flask, send_from_directory

# Flask App erstellen
app = Flask(__name__)

# Verzeichnis für Snapshots
SNAPSHOT_DIR = "./snapshots"
os.makedirs(SNAPSHOT_DIR, exist_ok=True)

# RTSP-URL
RTSP_URL = "rtsp://admin:herbstnvr@10.250.100.88:554/ch01.264"
LATEST_SNAPSHOT = None


def capture_rtsp_snapshot():
    global LATEST_SNAPSHOT
    while True:
        cap = cv2.VideoCapture(RTSP_URL)
        if not cap.isOpened():
            print("Error: Could not open RTSP stream.")
            time.sleep(300)
            continue
        
        ret, frame = cap.read()
        cap.release()
        
        if ret:
            filename = f"snapshot_{int(time.time())}.jpg"
            output_path = os.path.join(SNAPSHOT_DIR, filename)
            cv2.imwrite(output_path, frame)
            LATEST_SNAPSHOT = filename
            print(f"Snapshot saved: {filename}")
        else:
            print("Error: Could not capture frame.")
        
        time.sleep(300)  # Alle 5 Minuten


# Thread starten, um Snapshots automatisch zu erstellen
threading.Thread(target=capture_rtsp_snapshot, daemon=True).start()


@app.route('/')
def show_latest_snapshot():
    """Zeigt das aktuellste Snapshot-Bild an."""
    if LATEST_SNAPSHOT:
        return send_from_directory(SNAPSHOT_DIR, LATEST_SNAPSHOT)
    return "No snapshot available", 404


if __name__ == '__main__':
    print("Starting server...")
    app.run(host="0.0.0.0", port=5000)
