from datetime import datetime

from sqlalchemy.orm import selectinload

from app.config import get_settings
from app.database import SessionLocal
from app.models import Claim, Evidence, Report
from app.services.claim_extraction import ClaimExtractor
from app.services.pdf import PDFProcessor
from app.services.report import ReportBuilder
from app.services.search import SearchClient
from app.services.verification import VerificationEngine


def run_pipeline(report_id: str) -> None:
    settings = get_settings()
    db = SessionLocal()
    try:
        report = db.get(Report, report_id)
        if not report:
            return

        _update(report, db, "PROCESSING", "Parsing PDF", 8)
        pages = PDFProcessor().extract_text(open(report.upload_path, "rb").read())

        _update(report, db, "PROCESSING", "Extracting factual claims", 28)
        extracted_claims = ClaimExtractor(settings).extract_from_pages(pages)
        for item in extracted_claims:
            db.add(
                Claim(
                    report_id=report.id,
                    claim=item.claim,
                    claim_type=item.type,
                    page=item.page,
                )
            )
        db.commit()

        claims = (
            db.query(Claim)
            .filter(Claim.report_id == report.id)
            .order_by(Claim.id)
            .all()
        )
        if not claims:
            report.error = "No factual claims were extracted from the PDF."
            report.status = "COMPLETED"
            report.current_step = "No claims found"
            report.progress = 100
            report.completed_at = datetime.utcnow()
            db.add(report)
            db.commit()
            report = (
                db.query(Report)
                .options(selectinload(Report.claims).selectinload(Claim.evidence))
                .filter(Report.id == report_id)
                .one()
            )
            ReportBuilder(settings).write_reports(db, report)
            return

        search_client = SearchClient(settings)
        verifier = VerificationEngine(settings)
        total = len(claims)
        for index, claim in enumerate(claims, start=1):
            progress = 35 + int((index - 1) / total * 55)
            _update(report, db, "PROCESSING", f"Verifying claim {index} of {total}", progress)

            sources = search_client.search(claim.claim)
            for source in sources:
                db.add(
                    Evidence(
                        claim_id=claim.id,
                        title=source.title,
                        url=source.url,
                        snippet=source.snippet,
                        source_type=source.source_type,
                    )
                )

            verdict = verifier.verify(claim.claim, claim.claim_type, sources)
            claim.status = verdict["status"]
            claim.confidence = verdict["confidence"]
            claim.correct_value = verdict.get("correct_value")
            claim.explanation = verdict["explanation"]
            db.add(claim)
            db.commit()

        _update(report, db, "PROCESSING", "Generating reports", 94)
        report = (
            db.query(Report)
            .options(selectinload(Report.claims).selectinload(Claim.evidence))
            .filter(Report.id == report_id)
            .one()
        )
        report.status = "COMPLETED"
        report.current_step = "Completed"
        report.progress = 100
        report.completed_at = datetime.utcnow()
        db.add(report)
        db.commit()
        ReportBuilder(settings).write_reports(db, report)
    except Exception as exc:
        report = db.get(Report, report_id)
        if report:
            report.status = "FAILED"
            report.current_step = "Failed"
            report.error = str(exc)
            db.add(report)
            db.commit()
    finally:
        db.close()


def _update(report: Report, db, status: str, step: str, progress: int) -> None:
    report.status = status
    report.current_step = step
    report.progress = progress
    db.add(report)
    db.commit()
