import io
import json
import logging
import os
import re
import uuid
from typing import List, Optional

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from embeddings import embed_text, embed_image_bytes
from llm import generate_answer
from vector_store import FaissStore

logger = logging.getLogger("uvicorn.error")
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# Mount images directory if it exists (for local development)
# In production on Render, users upload images via /ingest/image API
images_dir = os.path.join(os.path.dirname(__file__), "data", "images")
if os.path.exists(images_dir):
    app.mount("/data/images", StaticFiles(directory=images_dir), name="images")

store = FaissStore(path=os.path.join(os.path.dirname(__file__), "store"))
MAX_IMAGE_DISTANCE = 115.0

class QueryRequest(BaseModel):
    query: str
    top_k: Optional[int] = 5

class IngestTextRequest(BaseModel):
    content: str
    title: Optional[str] = None
    metadata: Optional[dict] = None


def query_terms(query: str) -> List[str]:
    return [term for term in re.findall(r"[a-z0-9]+", query.lower()) if len(term) > 2]


def rerank_hits(query: str, hits: List[dict], top_k: int) -> List[dict]:
    terms = query_terms(query)
    if not terms:
        return hits[:top_k]

    def lexical_score(hit: dict) -> int:
        metadata = hit.get("metadata", {})
        searchable_text = " ".join(
            str(metadata.get(field, ""))
            for field in ("title", "content", "caption", "source", "filename")
        ).lower()
        return sum(searchable_text.count(term) for term in terms)

    ranked_hits = sorted(
        hits,
        key=lambda hit: (-lexical_score(hit), hit.get("score", float("inf"))),
    )
    return ranked_hits[:top_k]


def build_retrieval_answer(query: str, hits: List[dict]) -> str:
    if not hits:
        return f'I could not find anything in the indexed documents for: "{query}".'

    useful_parts = []
    for hit in hits:
        metadata = hit.get("metadata", {})
        title = metadata.get("title") or metadata.get("source") or "Untitled"
        content = metadata.get("content") or metadata.get("caption") or ""
        source = metadata.get("source") or metadata.get("filename") or "unknown"
        if not content:
            continue
        useful_parts.append(f"{title} ({source}): {content}")

    if not useful_parts:
        return f'I found related indexed items for: "{query}", but they do not have text or captions to summarize.'

    answer = "Based on your indexed data, I found these relevant results:\n\n"
    answer += "\n\n".join(useful_parts[:3])
    return answer


def lexical_search(query: str, top_k: int = 5) -> List[dict]:
    terms = query_terms(query)
    if not terms:
        return []

    hits = []
    for item_id, metadata in store.metadata.items():
        searchable_text = " ".join(
            str(metadata.get(field, ""))
            for field in ("title", "content", "caption", "source", "filename")
        ).lower()
        score = sum(searchable_text.count(term) for term in terms)
        if score > 0:
            hits.append({
                "id": item_id,
                "score": float(1.0 / (score + 1)),
                "metadata": metadata,
            })

    hits.sort(key=lambda hit: hit["score"])
    return hits[:top_k]

@app.get("/")
def root():
    return {"status": "AI search engine backend is running"}

@app.post("/ingest/text")
def ingest_text(payload: IngestTextRequest):
    if not payload.content:
        raise HTTPException(status_code=400, detail="Text content is required")

    vector = embed_text(payload.content)
    item_id = str(uuid.uuid4())
    metadata = {
        "title": payload.title or "Text document",
        "content": payload.content,
        "type": "text",
    }
    if payload.metadata:
        metadata.update(payload.metadata)

    store.add(item_id, vector, metadata)
    return {"id": item_id, "message": "Text document indexed"}

@app.post("/ingest/image")
async def ingest_image(file: UploadFile = File(...), title: Optional[str] = Form(None), metadata: Optional[str] = Form(None)):
    contents = await file.read()
    if not contents:
        raise HTTPException(status_code=400, detail="Image file is required")

    vector = embed_image_bytes(contents)
    item_id = str(uuid.uuid4())
    meta = {
        "title": title or file.filename,
        "filename": file.filename,
        "type": "image",
    }
    if metadata:
        try:
            meta.update(json.loads(metadata))
        except json.JSONDecodeError:
            meta["metadata_text"] = metadata

    store.add(item_id, vector, meta)
    return {"id": item_id, "message": "Image document indexed"}

@app.post("/query")
def query(request: QueryRequest):
    if not request.query:
        raise HTTPException(status_code=400, detail="Query text is required")

    try:
        query_vector = embed_text(request.query)
        hits = store.search(query_vector, top_k=request.top_k)
        return {"query": request.query, "results": hits}
    except Exception as exc:
        logger.exception("Embedding failed in /query")
        hits = lexical_search(request.query, top_k=request.top_k)
        return {
            "query": request.query,
            "results": hits,
            "mode": "lexical_fallback",
            "warning": f"Embedding failed: {str(exc)}",
        }

@app.post("/query/image")
async def query_image(file: UploadFile = File(...), top_k: int = Form(5)):
    contents = await file.read()
    if not contents:
        raise HTTPException(status_code=400, detail="Image file is required")

    try:
        query_vector = embed_image_bytes(contents)
        raw_hits = store.search(query_vector, top_k=store.count())
        image_hits = [hit for hit in raw_hits if hit.get("metadata", {}).get("type") == "image"]
        confident_hits = [hit for hit in image_hits if hit.get("score", float("inf")) <= MAX_IMAGE_DISTANCE]
        return {
            "filename": file.filename,
            "results": confident_hits[:top_k],
            "raw_result_count": len(image_hits),
            "threshold": MAX_IMAGE_DISTANCE,
            "best_score": image_hits[0]["score"] if image_hits else None,
            "message": None if confident_hits else "No confident image match found in your indexed images.",
        }
    except Exception as exc:
        logger.exception("Error in /query/image")
        raise HTTPException(status_code=500, detail=str(exc))

@app.post("/ask")
def ask(request: QueryRequest):
    if not request.query:
        raise HTTPException(status_code=400, detail="Query text is required")

    requested_top_k = request.top_k or 5
    candidate_count = max(requested_top_k, 12)

    try:
        query_vector = embed_text(request.query)
        candidates = store.search(query_vector, top_k=candidate_count)
        hits = rerank_hits(request.query, candidates, requested_top_k)
    except Exception as exc:
        logger.exception("Embedding failed in /ask")
        hits = lexical_search(request.query, top_k=requested_top_k)
        answer = build_retrieval_answer(request.query, hits)
        return {
            "query": request.query,
            "answer": answer,
            "sources": hits,
            "mode": "lexical_fallback",
            "warning": f"Embedding failed: {str(exc)}",
        }

    try:
        answer = generate_answer(request.query, hits)
        mode = "groq"
    except Exception as exc:
        answer = build_retrieval_answer(request.query, hits)
        mode = "retrieval_fallback"
        return {"query": request.query, "answer": answer, "sources": hits, "mode": mode, "warning": str(exc)}

    return {"query": request.query, "answer": answer, "sources": hits, "mode": mode}

@app.get("/documents")
def documents():
    return {"count": store.count(), "documents": store.list_meta()}
