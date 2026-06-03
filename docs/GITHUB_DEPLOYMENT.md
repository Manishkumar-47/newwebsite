# GitHub Deployment Guide

## Current Setup

Your project is configured for:
- **Frontend**: React + Vite → GitHub Pages
- **Backend**: FastAPI (Python) → GitHub Actions + Render/Railway/Fly.io

## Step 1: Initialize & Push to GitHub

### Check if git is already initialized:
```bash
cd c:\Users\asus\Downloads\manish
git status
```

### If NOT initialized:
```bash
git init
git add .
git commit -m "Initial commit: Fact-Check Agent full-stack app"
git branch -M main
git remote add origin https://github.com/laxmipati786/newwebsite.git
git push -u origin main
```

### If already initialized:
```bash
git add .
git commit -m "Setup GitHub deployment workflows"
git push
```

---

## Step 2: Configure GitHub Pages

1. Go to your repo: https://github.com/laxmipati786/newwebsite
2. Settings → Pages
3. **Source**: Deploy from a branch
4. **Branch**: `main` / `/ (root)`
   - OR use `main` / `/frontend/dist` if you prefer
5. Save

Your frontend will be live at: `https://laxmipati786.github.io/newwebsite/`

**Note**: If using a subdirectory, update `frontend/vite.config.js`:
```javascript
export default {
  base: '/newwebsite/',
  // ... rest of config
}
```

---

## Step 3: Configure Backend Deployment

### Option A: Render (Recommended - easiest from Render)
1. Visit render.com
2. New → Web Service
3. Connect your GitHub repository
4. Use existing `render.yaml` config

### Option B: Railway
1. Visit railway.app
2. New Project → Deploy from GitHub
3. Connect repo and select `/backend` directory

### Option C: Fly.io
1. Visit fly.io
2. `flyctl launch` in project root
3. Follow prompts

### Option D: Automatic via GitHub Actions
If using Render and want automatic deploys from GitHub:

1. Get your **Render Service ID** from: https://dashboard.render.com
2. Get your **Render API Key** from: https://dashboard.render.com/account/api-tokens
3. Go to your GitHub repo → Settings → Secrets and variables → Actions
4. Add secrets:
   - `RENDER_SERVICE_ID`: (your service ID)
   - `RENDER_API_KEY`: (your API key)

The workflow in `.github/workflows/deploy-backend.yml` will now auto-deploy when you push to `main`.

---

## Step 4: Update Frontend API URL

Once your backend is deployed, update the frontend API URL:

**frontend/src/api.js**:
```javascript
const API_BASE_URL = process.env.VITE_API_URL || 'http://localhost:8000';
```

**frontend/.env** (create this file):
```
VITE_API_URL=https://your-backend-domain.render.com
```

---

## Step 5: Configure Environment Variables

### Backend Environment Variables
In your hosting platform's dashboard (Render/Railway/Fly.io), add:
- `OPENAI_API_KEY`
- `TAVILY_API_KEY`
- `SERPER_API_KEY`
- `CORS_ORIGINS` (e.g., `https://laxmipati786.github.io`)

---

## Step 6: Verify Deployments

After pushing code:

1. **Check GitHub Actions**: Go to repo → Actions tab
2. **Frontend Status**: Check `deploy-frontend.yml` workflow
3. **Backend Status**: Check `deploy-backend.yml` workflow

### URLs After Deployment:
- **Frontend**: https://laxmipati786.github.io/newwebsite/
- **Backend**: https://your-service.render.com (or equivalent)

---

## Troubleshooting

### Frontend not updating on GitHub Pages?
- Check GitHub Actions for build errors
- Clear browser cache
- Verify `frontend/vite.config.js` has correct `base` path

### Backend not deploying?
- Verify API keys in secrets
- Check `backend/requirements.txt` has all dependencies
- Ensure `render.yaml` rootDir is correct: `backend`

### CORS Issues?
- Backend: Update `CORS_ORIGINS` to include GitHub Pages URL
- Example: `CORS_ORIGINS=https://laxmipati786.github.io`

---

## Optional: Use GitHub CLI

```bash
# Install GitHub CLI from: https://cli.github.com

# Login
gh auth login

# Create repo (if not exists)
gh repo create newwebsite --public

# Push from existing repo
git push -u origin main
```

---

## Summary

✅ Created GitHub Actions workflows for automated deployment
✅ Frontend will auto-deploy to GitHub Pages on push to main
✅ Backend needs to be connected to Render/Railway/Fly.io
✅ See GitHub Actions tab to monitor deployments
