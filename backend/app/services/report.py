import json
from pathlib import Path
from typing import Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.models import Claim, Report


class ReportBuilder:
    def __init__(self, settings: Settings | None = None):
        self.settings = settings or get_settings()

    def build_payload(self, report: Report) -> dict[str, Any]:
        claims = [
            {
                "id": claim.id,
                "claim": claim.claim,
                "claim_type": claim.claim_type,
                "page": claim.page,
                "status": claim.status,
                "confidence": claim.confidence,
                "correct_value": claim.correct_value,
                "explanation": claim.explanation,
                "evidence": [
                    {
                        "title": source.title,
                        "url": source.url,
                        "snippet": source.snippet,
                        "source_type": source.source_type,
                    }
                    for source in claim.evidence
                ],
            }
            for claim in report.claims
        ]
        return {
            "id": report.id,
            "filename": report.filename,
            "status": report.status,
            "current_step": report.current_step,
            "progress": report.progress,
            "error": report.error,
            "summary": self.summarize(report.claims),
            "claims": claims,
            "created_at": report.created_at.isoformat(),
            "updated_at": report.updated_at.isoformat(),
            "completed_at": report.completed_at.isoformat() if report.completed_at else None,
        }

    def write_reports(self, db: Session, report: Report) -> tuple[str, str]:
        reports_dir = self.settings.storage_dir / "reports" / report.id
        reports_dir.mkdir(parents=True, exist_ok=True)
        json_path = reports_dir / "report.json"
        pdf_path = reports_dir / "report.pdf"

        payload = self.build_payload(report)
        json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        self._write_pdf(pdf_path, payload)

        report.json_report_path = str(json_path)
        report.pdf_report_path = str(pdf_path)
        db.add(report)
        db.commit()
        return str(json_path), str(pdf_path)

    def _write_pdf(self, path: Path, payload: dict[str, Any]) -> None:
        styles = getSampleStyleSheet()
        doc = SimpleDocTemplate(str(path), pagesize=A4, rightMargin=28, leftMargin=28)
        story: list[Any] = [
            Paragraph("Fact-Check Report", styles["Title"]),
            Paragraph(f"Source PDF: {payload['filename']}", styles["Normal"]),
            Spacer(1, 12),
        ]

        summary = payload["summary"]
        story.append(
            Paragraph(
                (
                    f"Total claims: {summary['total']} | Verified: {summary['verified']} | "
                    f"Outdated: {summary['outdated']} | Inaccurate: {summary['inaccurate']} | "
                    f"False: {summary['false']} | Insufficient: {summary['insufficient_evidence']}"
                ),
                styles["Normal"],
            )
        )
        story.append(Spacer(1, 16))

        table_data = [["Claim", "Status", "Confidence", "Correct Fact"]]
        for claim in payload["claims"]:
            table_data.append(
                [
                    Paragraph(claim["claim"], styles["BodyText"]),
                    claim["status"],
                    f"{claim['confidence']}%",
                    Paragraph(claim.get("correct_value") or "—", styles["BodyText"]),
                ]
            )

        table = Table(table_data, colWidths=[230, 88, 70, 145], repeatRows=1)
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#172033")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#CBD5E1")),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 8),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
                ]
            )
        )
        story.append(table)
        story.append(Spacer(1, 18))
        story.append(Paragraph("Evidence Sources", styles["Heading2"]))

        for claim in payload["claims"]:
            if not claim["evidence"]:
                continue
            story.append(Paragraph(claim["claim"], styles["Heading4"]))
            for source in claim["evidence"][:5]:
                story.append(
                    Paragraph(
                        f"{source['title']} ({source['source_type']}): {source['url']}",
                        styles["BodyText"],
                    )
                )
            story.append(Spacer(1, 8))

        doc.build(story)

    @staticmethod
    def summarize(claims: list[Claim]) -> dict[str, int]:
        summary = {
            "total": len(claims),
            "verified": 0,
            "outdated": 0,
            "inaccurate": 0,
            "false": 0,
            "insufficient_evidence": 0,
            "pending": 0,
        }
        for claim in claims:
            key = claim.status.lower().replace(" ", "_")
            if key in summary:
                summary[key] += 1
        return summary

