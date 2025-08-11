# backend/ocr/engines/easyocr_engine.py
from .OCREngineBase import OCREngine
import easyocr
import numpy as np

class EasyOCREngine(OCREngine):
    def __init__(self, lang: str = "en", gpu: bool = False):
        # this loads models (expensive) - if you can reuse engines, do so
        self.reader = easyocr.Reader([lang], gpu=gpu)

    def recognize_sync(self, images, config: dict):
        # images: list of numpy arrays
        results = []
        for img in images:
            detections = self.reader.readtext(img)
            full_text = " ".join([d[1] for d in detections])
            confidence = sum([d[2] for d in detections]) / len(detections) if detections else 0
            results.append({"text": full_text.strip(), "confidence": round(confidence, 3)})
        return results

    # Keep async wrapper if you want:
    async def recognize(self, images, config: dict):
        return self.recognize_sync(images, config)
