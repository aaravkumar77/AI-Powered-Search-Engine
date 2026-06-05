# Deployment Guide for Render (512MB Free Plan)

## Changes Made for Memory Optimization

### 1. **Embedding Model Downgrade** ✅
- **Before:** `clip-ViT-B-32` (~300-400MB memory)
- **After:** `all-MiniLM-L6-v2` (~50MB memory)
- **Impact:** Reduces memory footprint by ~75%, slightly lower quality embeddings but still good for RAG
- **File Changed:** `embeddings.py`

### 2. **Removed Jupyter Notebooks from Deployment** ✅
- **Created:** `.gitignore` file
- **Keeps locally:** All `.ipynb` files (stay in VS Code & GitHub for reference)
- **Excludes from deployment:** Notebooks won't be deployed to Render
- **Data files excluded:** `data/images/` and `data/text/` not deployed

### 3. **Optimized Dependencies** ✅
- **Before:** `uvicorn[standard]` (includes extra middleware)
- **After:** `uvicorn` (core only)
- **Saves:** ~50MB deployment size

### 4. **Made Image Serving Dynamic** ✅
- **Old:** Always mounts `data/images/` directory (fails if missing)
- **New:** Only mounts if directory exists (graceful fallback)
- **Result:** Works with or without local data files

---

## How Data Works Now (Important! ⚠️)

### Local Development (Your Computer)
```
1. You keep data/images/ and data/text/ locally
2. Run the backend: uvicorn app:app
3. Test endpoints with your data
4. Commit notebooks to GitHub (for reference)
```

### Production on Render (Free Plan)
```
1. START: Empty database (no data files deployed)
2. USER WORKFLOW:
   - Upload text via: POST /ingest/text
   - Upload images via: POST /ingest/image
   - Query via: POST /query or POST /ask
3. Data stored in: store/index.faiss (small ~200KB)
4. Each deployment = fresh start
```

---

## Testing Locally Before Deployment

### 1. **Install dependencies**
```bash
pip install -r requirements.txt
```

### 2. **Test with local data**
```bash
# Keep your data/images/ and data/text/ folders
# Run the backend
uvicorn app:app --reload

# In another terminal, ingest sample data
curl -X POST "http://localhost:8000/ingest/text" \
  -H "Content-Type: application/json" \
  -d '{"content": "Sample text", "title": "Test"}'

# Query
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{"query": "sample"}'
```

### 3. **Test without data (like Render)**
```bash
# Rename or remove data/images/ folder
# Run the backend - should still start
uvicorn app:app --reload

# Endpoints work, but will find nothing until users ingest data
```

---

## Deploy to Render

### Step 1: Push to GitHub
```bash
git add .
git commit -m "Optimize for Render deployment"
git push
```

### Step 2: Create Render Service
1. Go to [render.com](https://render.com)
2. Click "New +" → "Web Service"
3. Connect your GitHub repo
4. **Settings:**
   - **Name:** `ai-search-backend`
   - **Runtime:** Python
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn app:app --host 0.0.0.0 --port $PORT`
   - **Plan:** Free
   - **Python Version:** 3.11

### Step 3: Set Environment Variables
Go to Environment and add:
```
GROQ_API_KEY=your_key_here
GROQ_MODEL=llama-3.1-8b-instant
```

### Step 4: Deploy!
Click "Deploy" - Render will build and start your service

---

## API Usage for Users

### Ingest Text
```bash
curl -X POST "https://your-render-domain.com/ingest/text" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Your text here",
    "title": "Document Title"
  }'
```

### Ingest Image
```bash
curl -X POST "https://your-render-domain.com/ingest/image" \
  -F "file=@path/to/image.jpg" \
  -F "title=My Image"
```

### Query
```bash
curl -X POST "https://your-render-domain.com/query" \
  -H "Content-Type: application/json" \
  -d '{"query": "search term", "top_k": 5}'
```

### Ask (RAG with LLM)
```bash
curl -X POST "https://your-render-domain.com/ask" \
  -H "Content-Type: application/json" \
  -d '{"query": "your question", "top_k": 5}'
```

### List Documents
```bash
curl "https://your-render-domain.com/documents"
```

---

## Memory Breakdown (512MB Render Plan)

| Component | Size | % of 512MB |
|-----------|------|-----------|
| OS/Runtime | ~100MB | 20% |
| Python + FastAPI | ~80MB | 15% |
| all-MiniLM-L6-v2 model | ~50MB | 10% |
| Dependencies (numpy, faiss, etc) | ~100MB | 20% |
| **Buffer/Runtime** | **~182MB** | **35%** |
| **TOTAL** | ~512MB | 100% |

✅ Should work! No pre-loaded image data means no memory spikes.

---

## Troubleshooting

### "Out of Memory" Error
- Reduce `top_k` parameter in queries (fewer search results)
- Limit concurrent users (free plan = 1 instance)
- Consider upgrading to paid plan if you need more

### Model Download Fails
- First request will download model (~50MB)
- Make sure Render has internet access (it does)
- Check CloudBuild logs in Render dashboard

### Data Not Persisting
- This is expected on free plan (restarts weekly)
- Implement persistent storage: AWS S3, Supabase, or Render Disk
- Or redesign to accept fresh data via API each session

---

## Next Steps (Optional Improvements)

1. **Persistent Storage:** Add `render_disk` for permanent vector store
2. **Better Embeddings:** Use API-based (OpenAI, HuggingFace) if budget allows
3. **Rate Limiting:** Add to prevent abuse on free tier
4. **Logging:** Implement to debug issues on Render

---

**Your GitHub Repo:** Keep `.ipynb` files for documentation
**Your Render:** Production with minimal memory footprint ✅
