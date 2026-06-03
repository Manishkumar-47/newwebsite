# Backend Deployment Setup

Your FastAPI backend is ready to deploy on Render. All configuration is in place!

## Render Configuration

**File**: `backend/render.yaml`

```yaml
services:
  - type: web
    name: fact-check-agent-backend
    env: python
    plan: starter
    rootDir: backend
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

## Quick Deploy Steps

### Option 1: Using Render Dashboard (Recommended)

1. Go to: https://dashboard.render.com
2. Click "New" → "Web Service"
3. Connect GitHub repository: `laxmipati786/newwebsite`
4. Fill in:
   - **Name**: `fact-check-agent-backend`
   - **Root Directory**: `backend`
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. **Instance Type**: Starter ($7/month) - recommended for production
6. **Environment Variables** (add these):
   - `OPENAI_API_KEY`: Your OpenAI key
   - `TAVILY_API_KEY`: Your Tavily key
   - `SERPER_API_KEY`: Your Serper key
   - `CORS_ORIGINS`: `https://laxmipati786.github.io`
7. Click "Deploy Web Service"

### Option 2: Connect Blueprint

Render can auto-detect and use `render.yaml`:
1. Go to Render dashboard
2. New → Blueprint
3. Select repository
4. It will auto-read `backend/render.yaml`

## Environment Variables

Add these to Render dashboard before deployment:

```
OPENAI_API_KEY=sk-...
TAVILY_API_KEY=...
SERPER_API_KEY=...
CORS_ORIGINS=https://laxmipati786.github.io
DATABASE_URL=sqlite:///./storage/factcheck.db (default)
OPENAI_MODEL=gpt-4.1 (optional - default in render.yaml)
```

## After Deployment

Once backend is deployed, you'll get a URL like:
```
https://fact-check-agent-backend.onrender.com
```

Update frontend to use this URL:

**File**: `frontend/.env`
```
VITE_API_URL=https://fact-check-agent-backend.onrender.com
```

Then commit and push:
```bash
git add frontend/.env
git commit -m "Update backend API URL for production"
git push
```

This will trigger GitHub Actions to redeploy your frontend with the new backend URL!

## Troubleshooting

### Deploy fails with "gunicorn not found"
- Make sure you're using `startCommand: uvicorn app.main:app...` ✓

### CORS errors
- Update `CORS_ORIGINS` in Render dashboard with your frontend URL
- Current: `https://laxmipati786.github.io`

### Environment variables not working
- Manually add them in Render dashboard → Web Service → Environment
- Or use `.env.render` file (not recommended - use dashboard instead)

## Database

Backend uses SQLite by default (file-based):
- Path: `backend/storage/factcheck.db`
- Persisted in Render's persistent disk
- If you need PostgreSQL, ask me to update the setup

## Monitoring

After deployment:
1. Check Render dashboard for logs: https://dashboard.render.com
2. Monitor health at: `https://fact-check-agent-backend.onrender.com/docs` (API docs)

Your FastAPI backend is production-ready! 🚀
