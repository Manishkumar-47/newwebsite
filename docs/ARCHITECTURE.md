# Architecture

## Flow

1. User uploads a PDF through the React UI.
2. FastAPI stores the file and creates a `Report` row.
3. A background task extracts text with PyMuPDF and falls back to pdfplumber when needed.
4. LangChain + OpenAI extracts structured factual claims. If no key is configured, a deterministic rule extractor is used.
5. Each claim is searched through Tavily, then Serper, then DuckDuckGo fallback.
6. LangChain + OpenAI compares claims to evidence and returns a normalized verdict.
7. SQLAlchemy persists claims, evidence, statuses, confidence, and corrected facts.
8. ReportLab generates the PDF report and the backend writes a JSON report.
9. The frontend polls `GET /report/{id}` and renders the final claim cards.

## Backend Modules

- `app/api/routes.py`: public API endpoints
- `app/models.py`: SQLAlchemy database models
- `app/services/pdf.py`: PDF text extraction
- `app/services/claim_extraction.py`: OpenAI and fallback claim extraction
- `app/services/search.py`: Tavily, Serper, DuckDuckGo search adapters
- `app/services/verification.py`: OpenAI and fallback verification engine
- `app/services/report.py`: JSON/PDF report generation
- `app/services/pipeline.py`: upload job orchestration

## Data Model

`Report` has many `Claim` rows. Each `Claim` has many `Evidence` rows.

This keeps SQLite simple while allowing a direct PostgreSQL upgrade through `DATABASE_URL`.

