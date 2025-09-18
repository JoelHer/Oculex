from abc import ABC, abstractmethod
from typing import List, Dict
import numpy as np

class OCREngine(ABC):
    @abstractmethod
    def recognize(self, images: List[np.ndarray], config: Dict = {}) -> List[Dict]:
        """
        Perform OCR on list of images.
        Returns: [{ "text": ..., "confidence": ... }, ...]
        """
        pass
