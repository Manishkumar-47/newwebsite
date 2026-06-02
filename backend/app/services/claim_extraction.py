import re
from collections import OrderedDict

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from app.config import Settings, get_settings
from app.schemas import ExtractedClaim
from app.services.json_utils import load_json_from_model
from app.services.pdf import PageText


CLAIM_PROMPT = """You extract factual claims from PDFs for a fact-checking system.

Return only a JSON array. Each item must contain:
- claim: a concise factual claim copied or lightly normalized from the document
- type: one of statistic, date, financial, technical, percentage, market, revenue, company, general
- page: page number if known

Focus on checkable claims: statistics, dates, financial figures, technical figures,
percentages, market claims, revenue claims, launch dates, comparisons, and named facts.
Ignore opinions, slogans, vague predictions, and unsupported marketing fluff.
"""


class ClaimExtractor:
    def __init__(self, settings: Settings | None = None):
        self.settings = settings or get_settings()

    def extract_from_pages(self, pages: list[PageText]) -> list[ExtractedClaim]:
        text = "\n\n".join(f"[Page {page.page}]\n{page.text}" for page in pages if page.text)
        return self.extract(text)

    def extract(self, text: str) -> list[ExtractedClaim]:
        if self.settings.openai_api_key:
            try:
                return self._extract_with_openai(text)
            except Exception:
                return self._extract_with_rules(text)
        return self._extract_with_rules(text)

    def _extract_with_openai(self, text: str) -> list[ExtractedClaim]:
        llm = ChatOpenAI(
            model=self.settings.openai_model,
            temperature=0,
            api_key=self.settings.openai_api_key,
        )
        content = text[:14000]
        response = llm.invoke(
            [
                SystemMessage(content=CLAIM_PROMPT),
                HumanMessage(content=f"PDF text:\n{content}"),
            ]
        )
        payload = load_json_from_model(str(response.content))
        claims: list[ExtractedClaim] = []
        for item in payload:
            if not isinstance(item, dict) or not item.get("claim"):
                continue
            claims.append(
                ExtractedClaim(
                    claim=str(item["claim"]).strip(),
                    type=str(item.get("type", "general")).strip().lower() or "general",
                    page=item.get("page"),
                )
            )
        return self._dedupe(claims)

    def _extract_with_rules(self, text: str) -> list[ExtractedClaim]:
        page_lookup = self._split_pages(text)
        claims: list[ExtractedClaim] = []
        for page, page_text in page_lookup.items():
            for sentence in self._sentences(page_text):
                if self._looks_like_claim(sentence):
                    claims.append(
                        ExtractedClaim(
                            claim=sentence,
                            type=self._classify(sentence),
                            page=page,
                        )
                    )
        return self._dedupe(claims)[:50]

    def _split_pages(self, text: str) -> OrderedDict[int | None, str]:
        matches = list(re.finditer(r"\[Page\s+(\d+)\]\s*", text, flags=re.IGNORECASE))
        if not matches:
            return OrderedDict([(None, text)])

        pages: OrderedDict[int | None, str] = OrderedDict()
        for index, match in enumerate(matches):
            start = match.end()
            end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
            pages[int(match.group(1))] = text[start:end]
        return pages

    def _sentences(self, text: str) -> list[str]:
        normalized = re.sub(r"\s+", " ", text).strip()
        chunks = re.split(r"(?<=[.!?])\s+", normalized)
        return [chunk.strip(" -•\t\n\r") for chunk in chunks if 18 <= len(chunk.strip()) <= 280]

    def _looks_like_claim(self, sentence: str) -> bool:
        lowered = sentence.lower()
        has_number = bool(re.search(r"(\d[\d,]*(?:\.\d+)?\s*%?)", sentence))
        claim_terms = (
            "million",
            "billion",
            "trillion",
            "crore",
            "lakh",
            "revenue",
            "market",
            "users",
            "customers",
            "launched",
            "founded",
            "grew",
            "growth",
            "percent",
            "percentage",
            "share",
            "valuation",
            "internet",
            "gdp",
            "inflation",
            "temperature",
            "patent",
            "registered",
        )
        factual_verbs = (" is ", " are ", " was ", " were ", " has ", " have ", " had ")
        event_verbs = (
            " launched ",
            " founded ",
            " grew ",
            " increased ",
            " decreased ",
            " reported ",
            " reached ",
            " crossed ",
            " released ",
        )
        padded = f" {lowered} "
        return (has_number or any(term in lowered for term in claim_terms)) and (
            any(verb in padded for verb in factual_verbs)
            or any(verb in padded for verb in event_verbs)
        )

    def _classify(self, sentence: str) -> str:
        lowered = sentence.lower()
        if "%" in sentence or "percent" in lowered or "percentage" in lowered:
            return "percentage"
        if any(token in lowered for token in ("revenue", "profit", "valuation", "$", "₹", "rs.")):
            return "financial"
        if any(token in lowered for token in ("market", "share", "industry")):
            return "market"
        if any(token in lowered for token in ("launched", "founded", "established")) or re.search(
            r"\b(19|20)\d{2}\b", sentence
        ):
            return "date"
        if any(token in lowered for token in ("gb", "mbps", "mw", "km", "celsius", "api", "model")):
            return "technical"
        if re.search(r"\d", sentence):
            return "statistic"
        return "general"

    def _dedupe(self, claims: list[ExtractedClaim]) -> list[ExtractedClaim]:
        seen: OrderedDict[str, ExtractedClaim] = OrderedDict()
        for claim in claims:
            key = re.sub(r"\W+", " ", claim.claim.lower()).strip()
            if key and key not in seen:
                seen[key] = claim
        return list(seen.values())
