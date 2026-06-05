# Hugging Face API Setup

## Get Free API Key (Takes 2 minutes)

### Step 1: Create HF Account
Go to: https://huggingface.co/join
- Sign up with email or GitHub

### Step 2: Get API Key
1. Go to: https://huggingface.co/settings/tokens
2. Click "New token"
3. **Name:** `ai-search-backend`
4. **Type:** `read`
5. Click "Create token"
6. **Copy the token** (starts with `hf_...`)

### Step 3: Save for Later
Keep this token safe - you'll need it for Render

---

## What Changed

### ❌ Removed (Bloated with CUDA)
- `sentence-transformers` library
- `torch` (PyTorch) - 532MB!
- All CUDA packages - 1.4GB+

### ✅ Added (Lightweight)
- `requests` library (just HTTP calls)
- Uses **Hugging Face Inference API** (free tier)

---

## New Size

| Before | After |
|--------|-------|
| 2GB+ (CUDA bloat) | ~200MB ✅ |
| **Result:** ❌ OOM error | **Result:** ✅ Fits in 512MB |

---

## How It Works

**Old way:**
```
embed_text() 
  → Load massive PyTorch model 
  → Run locally 
  → Get embedding 
  (CUDA packages = 2GB) ❌
```

**New way:**
```
embed_text()
  → HTTP POST to Hugging Face API
  → Get embedding back
  → Done!
  (Just requests library = tiny) ✅
```

---

## Pricing (Free Tier Available!)

- **Hugging Face Inference API Free Tier:**
  - ✅ 30K API calls/month
  - ✅ Limited to one concurrent request
  - ✅ Great for testing/personal projects

- **If you exceed free tier:**
  - $0.01 per 1,000 requests
  - Very cheap for light usage

---

## Update Requirements Summary

```diff
- sentence-transformers (pulls in torch + CUDA)
- torch-2.12.0 (532MB)
+ requests (just HTTP)
```

**Total package size:** ~100MB (down from 2GB+) ✅
