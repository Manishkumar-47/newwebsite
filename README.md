# Fact-Check Agent

An AI-powered fact-checking web app that accepts PDF uploads, extracts factual claims, searches live evidence sources, verifies each claim, and generates downloadable PDF and JSON reports.

## Stack

- Frontend: React, Vite, Tailwind CSS
- Backend: FastAPI, SQLAlchemy, SQLite
- AI: OpenAI via LangChain
- PDF processing: PyMuPDF, pdfplumber
- Search: Tavily, Serper, DuckDuckGo fallback
- Deployment: Vercel frontend, Render backend

## Quick Start

```bash
pip install -r requirements.txt
npm install
```

Create backend env:

```bash
cd backend
cp .env.example .env
```

Add API keys in `backend/.env`:

```bash
OPENAI_API_KEY=your_openai_key
TAVILY_API_KEY=your_tavily_key
SERPER_API_KEY=your_serper_key
```

Run the backend:

```bash
cd backend
uvicorn app.main:app --reload
```

Run the frontend:

```bash
npm run dev
```

Open `http://localhost:5173`.

## API

- `GET /health`
- `POST /upload`
- `POST /extract-claims`
- `POST /verify`
- `GET /report/{id}`
- `GET /report/{id}/download/json`
- `GET /report/{id}/download/pdf`

See [API docs](docs/API.md) for request and response details.

## Sample PDFs

Generate local fake/trap PDFs:

```bash
cd backend
python scripts/create_sample_pdfs.py
```

The files are written to `backend/sample_pdfs/`.

## Tests

```bash
cd backend
pytest
```

## Deployment

Render and Vercel setup instructions are in [Deployment](docs/DEPLOYMENT.md).

## Notes

The app runs without API keys using deterministic fallbacks, which is useful for development and tests. Production verification quality depends on setting `OPENAI_API_KEY` and at least one search API key.

