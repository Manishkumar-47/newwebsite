from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session, selectinload

from app.config import Settings, get_settings
from app.database import get_db
from app.models import Claim, Evidence, Report
from app.schemas import (
    ExtractClaimsResponse,
    UploadResponse,
    VerifiedClaim,
    VerifyRequest,
    VerifyResponse,
)
from app.services.claim_extraction import ClaimExtractor
from app.services.pdf import PDFProcessor
from app.services.pipeline import run_pipeline
from app.services.report import ReportBuilder
from app.services.search import SearchClient
from app.services.verification import VerificationEngine

router = APIRouter()


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "fact-check-agent"}


@router.post("/upload", response_model=UploadResponse)
async def upload_pdf(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> UploadResponse:
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Please upload a PDF file.")

    contents = await file.read()
    max_bytes = settings.max_upload_mb * 1024 * 1024
    if len(contents) > max_bytes:
        raise HTTPException(status_code=413, detail=f"PDF exceeds {settings.max_upload_mb} MB limit.")

    report_id = str(uuid4())
    upload_path = settings.storage_dir / "uploads" / f"{report_id}.pdf"
    upload_path.write_bytes(contents)

    report = Report(
        id=report_id,
        filename=file.filename,
        upload_path=str(upload_path),
        status="QUEUED",
        current_step="Queued",
        progress=0,
    )
    db.add(report)
    db.commit()
    background_tasks.add_task(run_pipeline, report_id)

    return UploadResponse(
        id=report.id,
        status=report.status,
        current_step=report.current_step,
        progress=report.progress,
    )


@router.post("/extract-claims", response_model=ExtractClaimsResponse)
async def extract_claims(
    file: UploadFile = File(...),
    settings: Settings = Depends(get_settings),
) -> ExtractClaimsResponse:
    contents = await file.read()
    pages = PDFProcessor().extract_text(contents)
    claims = ClaimExtractor(settings).extract_from_pages(pages)
    return ExtractClaimsResponse(
        claims=claims,
        character_count=sum(len(page.text) for page in pages),
        page_count=len(pages),
    )


@router.post("/verify", response_model=VerifyResponse)
def verify_claims(
    payload: VerifyRequest,
    settings: Settings = Depends(get_settings),
) -> VerifyResponse:
    search = SearchClient(settings)
    verifier = VerificationEngine(settings)
    results: list[VerifiedClaim] = []
    for item in payload.claims:
        sources = search.search(item.claim)
        verdict = verifier.verify(item.claim, item.type, sources)
        results.append(
            VerifiedClaim(
                claim=item.claim,
                type=item.type,
                status=verdict["status"],
                confidence=verdict["confidence"],
                correct_value=verdict.get("correct_value"),
                explanation=verdict["explanation"],
                sources=[
                    {
                        "title": source.title,
                        "url": source.url,
                        "snippet": source.snippet,
                        "source_type": source.source_type,
                    }
                    for source in sources
                ],
            )
        )
    return VerifyResponse(results=results)


@router.get("/report/{report_id}")
def get_report(report_id: str, db: Session = Depends(get_db), settings: Settings = Depends(get_settings)):
    report = _load_report(db, report_id)
    payload = ReportBuilder(settings).build_payload(report)
    payload["downloads"] = {
        "json": f"/report/{report_id}/download/json",
        "pdf": f"/report/{report_id}/download/pdf",
    }
    return payload


@router.get("/report/{report_id}/download/{file_format}")
def download_report(
    report_id: str,
    file_format: str,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    report = _load_report(db, report_id)
    if report.status != "COMPLETED":
        raise HTTPException(status_code=409, detail="Report is not complete yet.")

    if not report.json_report_path or not report.pdf_report_path:
        ReportBuilder(settings).write_reports(db, report)
        db.refresh(report)

    if file_format == "json":
        path = Path(report.json_report_path or "")
        media_type = "application/json"
    elif file_format == "pdf":
        path = Path(report.pdf_report_path or "")
        media_type = "application/pdf"
    else:
        raise HTTPException(status_code=400, detail="Format must be json or pdf.")

    if not path.exists():
        raise HTTPException(status_code=404, detail="Report file not found.")
    return FileResponse(path, media_type=media_type, filename=f"fact-check-report-{report_id}.{file_format}")


def _load_report(db: Session, report_id: str) -> Report:
    report = (
        db.query(Report)
        .options(selectinload(Report.claims).selectinload(Claim.evidence))
        .filter(Report.id == report_id)
        .first()
    )
    if not report:
        raise HTTPException(status_code=404, detail="Report not found.")
    return report

