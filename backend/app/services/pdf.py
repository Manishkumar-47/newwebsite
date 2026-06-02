from dataclasses import dataclass
from io import BytesIO

import fitz
import pdfplumber


@dataclass
class PageText:
    page: int
    text: str


class PDFProcessor:
    def extract_text(self, contents: bytes) -> list[PageText]:
        pages = self._extract_with_pymupdf(contents)
        if self._has_enough_text(pages):
            return pages

        fallback_pages = self._extract_with_pdfplumber(contents)
        return fallback_pages if self._has_enough_text(fallback_pages) else pages

    def _extract_with_pymupdf(self, contents: bytes) -> list[PageText]:
        document = fitz.open(stream=contents, filetype="pdf")
        try:
            return [
                PageText(page=index + 1, text=(page.get_text("text") or "").strip())
                for index, page in enumerate(document)
            ]
        finally:
            document.close()

    def _extract_with_pdfplumber(self, contents: bytes) -> list[PageText]:
        with pdfplumber.open(BytesIO(contents)) as pdf:
            return [
                PageText(page=index + 1, text=(page.extract_text() or "").strip())
                for index, page in enumerate(pdf.pages)
            ]

    @staticmethod
    def _has_enough_text(pages: list[PageText]) -> bool:
        return sum(len(page.text) for page in pages) >= 25

