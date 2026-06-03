import io
import os

import numpy as np
from PIL import Image

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    SentenceTransformer = None

_model = None


def _load_model():
    global _model
    if _model is None:
        if SentenceTransformer is None:
            raise RuntimeError("sentence-transformers is required for embedding generation")
        _model = SentenceTransformer("clip-ViT-B-32")
    return _model


def embed_text(text: str) -> np.ndarray:
    if not text:
        raise ValueError("Text input is required")
    model = _load_model()
    vector = model.encode([text], convert_to_numpy=True, show_progress_bar=False)
    return np.array(vector[0], dtype="float32")


def embed_image_bytes(image_bytes: bytes) -> np.ndarray:
    if not image_bytes:
        raise ValueError("Image bytes are required")
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    model = _load_model()
    vector = model.encode([image], convert_to_numpy=True, show_progress_bar=False)
    return np.array(vector[0], dtype="float32")
