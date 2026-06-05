# Pre-Deployment Checklist for Render

## ✅ Already Done (Automated)
- [x] Changed embedding model to `all-MiniLM-L6-v2` (saves ~250MB)
- [x] Updated `requirements.txt` (removed `uvicorn[standard]`)
- [x] Created `.gitignore` (notebooks excluded from deployment)
- [x] Made image serving optional (handles missing data gracefully)
- [x] Created `Procfile` for Render
- [x] Created `render.yaml` config
- [x] Created `DEPLOYMENT.md` guide

## 🔧 Manual Steps - Do These:

### 1. Test Locally First
```bash
cd backend
python -m venv test_env  # Fresh environment
source test_env/Scripts/activate  # or .venv/Scripts/Activate.ps1 on Windows
pip install -r requirements.txt
uvicorn app:app --reload
```

### 2. Verify Dependencies Download
- First request will download `all-MiniLM-L6-v2` model (~50MB)
- This happens during first API call, not on startup
- ✅ Much better than loading at startup!

### 3. Test without data (like production)
```bash
# Temporarily rename data folder
mv backend/data backend/data_backup

# Start server - should work fine
uvicorn app:app --reload

# Try: curl http://localhost:8000/
# Should see: "AI search engine backend is running"

# Restore data
mv backend/data_backup backend/data
```

### 4. Push to GitHub
```bash
git add .
git commit -m "Optimize for Render 512MB: use all-MiniLM-L6-v2 model, exclude notebooks"
git push
```

### 5. Deploy on Render
- Go to render.com
- Create new Web Service
- Connect GitHub repo (select `backend` folder)
- Use settings from `render.yaml`
- Add env vars: `GROQ_API_KEY`, `GROQ_MODEL`
- Click Deploy!

## 📝 How Users Will Use It (Production)

1. **Frontend calls:** `/ingest/text` or `/ingest/image` with their data
2. **Backend ingests:** Converts to embeddings, stores in FAISS
3. **User queries:** `/query` or `/ask` endpoints
4. **No pre-loaded data needed!** ✅

## 🚨 Important Notes

- **.ipynb files:** Stay local & GitHub (not deployed) ✅
- **Data files:** Start empty on Render (users upload via API) ✅
- **First startup:** Model downloads (~50MB) on first embedding request
- **Memory:** Should fit in 512MB now! ✅
- **Weekly restart:** Render free tier restarts weekly (data lost, but fine since users provide it)

## 💡 If Still Out of Memory

1. Scale down `top_k` parameter (fewer results per query)
2. Use smaller `batch_size` in embeddings
3. Enable Render Disk (paid feature) for persistent storage
4. Switch to paid plan ($7/month)

---

**Ready to deploy?** Run the checklist above! 🚀
