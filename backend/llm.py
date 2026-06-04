import os
from typing import Any, Dict, List

from dotenv import load_dotenv
from google import genai

load_dotenv()

GEMINI_MODEL = "gemini-2.5-flash"


def _format_context(retrieved_items: List[Dict[str, Any]]) -> str:
    context_blocks = []

    for index, item in enumerate(retrieved_items, start=1):
        metadata = item.get("metadata", {})
        title = metadata.get("title", "Untitled")
        item_type = metadata.get("type", "unknown")
        content = metadata.get("content") or metadata.get("caption") or ""
        source = metadata.get("source") or metadata.get("filename") or "unknown"

        context_blocks.append(
            f"Source {index}\n"
            f"Title: {title}\n"
            f"Type: {item_type}\n"
            f"File: {source}\n"
            f"Content: {content}"
        )

    return "\n\n---\n\n".join(context_blocks)


def generate_answer(query: str, retrieved_items: List[Dict[str, Any]]) -> str:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is missing. Add it to backend/.env")

    context = _format_context(retrieved_items)
    prompt = f"""
You are a helpful RAG assistant.

Answer the user's question using only the retrieved context below.
If the answer is not present in the context, say:
"I don't know based on the indexed documents."

User question:
{query}

Retrieved context:
{context}
"""

    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt,
    )

    return response.text or ""
