import os
from typing import Any, Dict, List

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

GROQ_BASE_URL = "https://api.groq.com/openai/v1"
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")


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
    api_key = os.getenv("GROQ_API_KEY") or os.getenv("GORQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY is missing. Add it to backend/.env")

    context = _format_context(retrieved_items)
    prompt = f"""
You are a helpful hybrid RAG assistant.

First, check whether any retrieved source contains a useful answer to the user's question.
Some retrieved sources may be weak matches, so do not reject the whole context just because one source is unrelated.

If the answer is present in the retrieved context:
- Answer using the retrieved context.
- Mention that the answer is based on indexed data.

If the answer is not present in the retrieved context:
- Start with: "I could not find this in the indexed documents."
- Then give a short general answer using your own knowledge.
- Put "General answer:" on the next line by itself before the general answer.

User question:
{query}

Retrieved context:
{context}
"""

    client = OpenAI(api_key=api_key, base_url=GROQ_BASE_URL, timeout=20.0)
    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {
                "role": "system",
                "content": "You answer user questions using retrieved RAG context when it is relevant.",
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0.2,
    )

    return response.choices[0].message.content or ""
