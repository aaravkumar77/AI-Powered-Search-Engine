# AI-Powered Search Engine

A simple multi-modal RAG demo with:
- FastAPI backend for text/image ingestion and vector search
- FAISS vector store for retrieval
- CLIP/OpenAI embeddings for text and images
- Minimal React frontend for query and upload

## Setup

### Backend

1. Open a terminal in `backend`
2. Create a virtual environment:
   - `python -m venv .venv`
   - `./.venv/Scripts/Activate.ps1` on Windows PowerShell
3. Install requirements:
   - `pip install -r requirements.txt`
4. Run the backend:
   - `uvicorn app:app --reload --port 8000`

### Frontend

1. Open a terminal in `frontend`
2. Install dependencies:
   - `npm install`
3. Start the UI:
   - `npm run dev`

## Add data

### Text data

Place `.txt` or `.md` files into `backend/data/text/`.
Use `backend/data_loader.py` to index local files.

### Image data

Place images into `backend/data/images/`.
Optionally add captions in `backend/data/images/image_metadata.json`.

## API Endpoints

- `POST /ingest/text` — index a text document
- `POST /ingest/image` — index an image
- `POST /query` — search with a text query
- `GET /documents` — list indexed documents

## Notes

- Start with a small corpus of documents/images
- Use your own notes or dataset samples
- This demo is enough to show a working RAG pipeline for internship projects
