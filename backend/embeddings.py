import io
import os

import numpy as np
from dotenv import load_dotenv
from openai import OpenAI
from PIL import Image

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY environment variable is required")

OPENAI_EMBEDDING_MODEL = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
HF_API_KEY = os.getenv("HF_API_KEY")
HF_IMAGE_MODEL_URL = "https://api-inference.huggingface.co/models/sentence-transformers/clip-ViT-B-32"


def _parse_embedding_response(response_json):
    if isinstance(response_json, dict) and response_json.get("error"):
        raise RuntimeError(response_json["error"])

    if isinstance(response_json, dict) and "data" in response_json:
        data = response_json["data"]
        if isinstance(data, list) and data:
            return data[0].get("embedding") or data[0]

    if isinstance(response_json, list) and len(response_json) > 0:
        return response_json[0] if isinstance(response_json[0], list) else response_json

    return response_json


def embed_text(text: str) -> np.ndarray:
    """
    Embed text using OpenAI embeddings.
    """
    if not text:
        raise ValueError("Text input is required")

    client = OpenAI(api_key=OPENAI_API_KEY, timeout=30.0)
    try:
        response = client.embeddings.create(model=OPENAI_EMBEDDING_MODEL, input=text)
        vector = _parse_embedding_response(response)
        return np.array(vector, dtype="float32")
    except Exception as exc:
        raise RuntimeError(f"Failed to get text embedding from OpenAI: {str(exc)}")


def _local_image_embedding(image_bytes: bytes) -> np.ndarray:
    image = Image.open(io.BytesIO(image_bytes)).convert("L")
    image = image.resize((16, 32), Image.BICUBIC)
    vector = np.array(image, dtype="float32").reshape(-1) / 255.0
    return vector


def embed_image_bytes(image_bytes: bytes) -> np.ndarray:
    """
    Embed image using Hugging Face only if configured, otherwise use a local fallback embedding.
    """
    if not image_bytes:
        raise ValueError("Image bytes are required")

    try:
        Image.open(io.BytesIO(image_bytes)).convert("RGB")
    except Exception as e:
        raise ValueError(f"Invalid image format: {str(e)}")

    if HF_API_KEY:
        headers = {"Authorization": f"Bearer {HF_API_KEY}"}
        files = {"file": ("image.jpg", image_bytes, "image/jpeg")}
        try:
            import requests

            response = requests.post(HF_IMAGE_MODEL_URL, headers=headers, files=files, timeout=30)
            response.raise_for_status()
            vector = _parse_embedding_response(response.json())
            return np.array(vector, dtype="float32")
        except Exception:
            pass

    return _local_image_embedding(image_bytes)
