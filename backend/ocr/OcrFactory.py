from .EasyOcrEngine import EasyOCREngine

def get_ocr_engine(engine_type: str, config: dict = {}):
    if engine_type == "easyocr":
        lang = config.get("language", "en")
        return EasyOCREngine(lang=lang)
    else:
        raise ValueError(f"Unsupported OCR engine: {engine_type}")
