import io
import os
import json
import uuid
from typing import List, Optional

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from embeddings import embed_text, embed_image_bytes
from llm import generate_answer
from vector_store import FaissStore

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

store = FaissStore(path=os.path.join(os.path.dirname(__file__), "store"))

class QueryRequest(BaseModel):
    query: str
    top_k: Optional[int] = 5

class IngestTextRequest(BaseModel):
    content: str
    title: Optional[str] = None
    metadata: Optional[dict] = None

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

    query_vector = embed_text(request.query)
    hits = store.search(query_vector, top_k=request.top_k)
    return {"query": request.query, "results": hits}

@app.post("/ask")
def ask(request: QueryRequest):
    if not request.query:
        raise HTTPException(status_code=400, detail="Query text is required")

    query_vector = embed_text(request.query)
    hits = store.search(query_vector, top_k=request.top_k)
    answer = generate_answer(request.query, hits)
    return {"query": request.query, "answer": answer, "sources": hits}

@app.get("/documents")
def documents():
    return {"count": store.count(), "documents": store.list_meta()}
