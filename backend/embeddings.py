import io
import os

import numpy as np
import requests
from dotenv import load_dotenv
from PIL import Image

load_dotenv()

# Hugging Face Inference API
HF_API_KEY = os.getenv("HF_API_KEY")
if not HF_API_KEY:
    raise RuntimeError("HF_API_KEY environment variable is required")

HF_TEXT_MODEL_URL = "https://api-inference.huggingface.co/models/sentence-transformers/all-MiniLM-L6-v2"
HF_IMAGE_MODEL_URL = "https://api-inference.huggingface.co/models/sentence-transformers/clip-ViT-B-32"


def _parse_embedding_response(response_json):
    if isinstance(response_json, dict) and response_json.get("error"):
        raise RuntimeError(response_json["error"])

    if isinstance(response_json, list) and len(response_json) > 0:
        return response_json[0] if isinstance(response_json[0], list) else response_json

    return response_json


def embed_text(text: str) -> np.ndarray:
    """
    Embed text using Hugging Face Inference API (free tier)
    """
    if not text:
        raise ValueError("Text input is required")

    headers = {"Authorization": f"Bearer {HF_API_KEY}"}
    payload = {"inputs": text}

    try:
        response = requests.post(HF_TEXT_MODEL_URL, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        vector = _parse_embedding_response(response.json())
        return np.array(vector, dtype="float32")
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Failed to get text embedding from HF API: {str(e)}")


def embed_image_bytes(image_bytes: bytes) -> np.ndarray:
    """
    Embed image using Hugging Face Inference API
    """
    if not image_bytes:
        raise ValueError("Image bytes are required")

    try:
        Image.open(io.BytesIO(image_bytes)).convert("RGB")
    except Exception as e:
        raise ValueError(f"Invalid image format: {str(e)}")

    headers = {"Authorization": f"Bearer {HF_API_KEY}"}
    files = {"file": ("image.jpg", image_bytes, "image/jpeg")}

    try:
        response = requests.post(HF_IMAGE_MODEL_URL, headers=headers, files=files, timeout=30)
        response.raise_for_status()
        vector = _parse_embedding_response(response.json())
        return np.array(vector, dtype="float32")
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Failed to get image embedding from HF API: {str(e)}")
