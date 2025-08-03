from .OCREngineBase import OCREngine
import easyocr
import numpy as np
from typing import List, Dict

class EasyOCREngine(OCREngine):
    def __init__(self, lang: str = "en"):
        self.reader = easyocr.Reader([lang], gpu=False)  # Set gpu=True if you want to use CUDA

    def recognize(self, images: List[np.ndarray], config: Dict = {}) -> List[Dict]:
        results = []
        for img in images:
            detections = self.reader.readtext(img)

            # Combine all text parts into one line
            full_text = " ".join([d[1] for d in detections])
            confidence = sum([d[2] for d in detections]) / len(detections) if detections else 0

            results.append({
                "text": full_text.strip(),
                "confidence": round(confidence, 3)
            })
        return results
