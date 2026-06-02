# Deployment Guide

## Backend on Render

1. Push this repository to GitHub.
2. In Render, create a new Blueprint or Web Service.
3. If using the included blueprint, Render can use the root `render.yaml`.
4. Set environment variables:

```bash
OPENAI_API_KEY=...
OPENAI_MODEL=gpt-4.1
TAVILY_API_KEY=...
SERPER_API_KEY=...
CORS_ORIGINS=https://your-vercel-app.vercel.app
DATABASE_URL=sqlite:///./storage/factcheck.db
```

5. Render build command:

```bash
pip install -r requirements.txt
```

6. Render start command:

```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

For production persistence, upgrade `DATABASE_URL` to a managed PostgreSQL URL and add a persistent disk or object storage for uploaded PDFs and generated reports.

## Frontend on Vercel

1. Import the repo in Vercel.
2. Set the project root to `frontend`.
3. Set environment variable:

```bash
VITE_API_URL=https://your-render-backend.onrender.com
```

4. Build command:

```bash
npm run build
```

5. Output directory:

```bash
dist
```

The included `frontend/vercel.json` handles client-side routing rewrites.

## SQLite to PostgreSQL

The backend uses SQLAlchemy and reads the connection from `DATABASE_URL`.

SQLite:

```bash
DATABASE_URL=sqlite:///./storage/factcheck.db
```

PostgreSQL:

```bash
DATABASE_URL=postgresql+psycopg://user:password@host:5432/factcheck
```

When switching to PostgreSQL, add the matching driver to `backend/requirements.txt`.
