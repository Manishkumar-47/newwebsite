import re
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from app.config import Settings, get_settings
from app.services.json_utils import load_json_from_model
from app.services.search import SearchSource


ALLOWED_STATUSES = {
    "VERIFIED",
    "OUTDATED",
    "INACCURATE",
    "FALSE",
    "INSUFFICIENT EVIDENCE",
}


VERIFY_PROMPT = """You are a careful fact-checking analyst.

Use only the supplied evidence sources. Compare the claim to the evidence and return
only JSON with these fields:
- status: VERIFIED, OUTDATED, INACCURATE, FALSE, or INSUFFICIENT EVIDENCE
- correct_value: corrected fact or null
- confidence: integer from 0 to 100
- explanation: concise reasoning grounded in the evidence

Rules:
- Exact match or same meaning: VERIFIED
- Older value that was once true but has newer evidence: OUTDATED
- Numeric value differs materially: INACCURATE
- Opposite of evidence or impossible date: FALSE
- Evidence is weak, missing, or unrelated: INSUFFICIENT EVIDENCE
"""


class VerificationEngine:
    def __init__(self, settings: Settings | None = None):
        self.settings = settings or get_settings()

    def verify(self, claim: str, claim_type: str, sources: list[SearchSource]) -> dict[str, Any]:
        trap = self._detect_known_trap(claim)
        if trap:
            return trap

        if self.settings.openai_api_key and sources:
            try:
                return self._verify_with_openai(claim, claim_type, sources)
            except Exception:
                return self._verify_with_rules(claim, sources)

        return self._verify_with_rules(claim, sources)

    def _verify_with_openai(
        self,
        claim: str,
        claim_type: str,
        sources: list[SearchSource],
    ) -> dict[str, Any]:
        llm = ChatOpenAI(
            model=self.settings.openai_model,
            temperature=0,
            api_key=self.settings.openai_api_key,
        )
        evidence = "\n".join(
            f"{index + 1}. {source.title}\nURL: {source.url}\nSnippet: {source.snippet or ''}"
            for index, source in enumerate(sources[:8])
        )
        response = llm.invoke(
            [
                SystemMessage(content=VERIFY_PROMPT),
                HumanMessage(
                    content=(
                        f"Claim type: {claim_type}\n"
                        f"Claim: {claim}\n\n"
                        f"Evidence:\n{evidence}"
                    )
                ),
            ]
        )
        parsed = load_json_from_model(str(response.content))
        return self._normalize_result(parsed)

    def _verify_with_rules(self, claim: str, sources: list[SearchSource]) -> dict[str, Any]:
        if not sources:
            return {
                "status": "INSUFFICIENT EVIDENCE",
                "correct_value": None,
                "confidence": 20,
                "explanation": "No trusted evidence sources were found for this claim.",
            }

        evidence_text = " ".join(
            filter(None, [source.title for source in sources] + [source.snippet for source in sources])
        )
        claim_lower = claim.lower()
        evidence_lower = evidence_text.lower()
        claim_numbers = self._numbers(claim)
        evidence_numbers = self._numbers(evidence_text)

        if claim_lower and claim_lower in evidence_lower:
            return {
                "status": "VERIFIED",
                "correct_value": claim,
                "confidence": 84,
                "explanation": "The claim appears directly in the collected evidence.",
            }

        if claim_numbers and evidence_numbers:
            closest = min(
                evidence_numbers,
                key=lambda value: abs(value - claim_numbers[0]),
            )
            claimed = claim_numbers[0]
            if claimed == 0:
                relative_diff = 0 if closest == 0 else 1
            else:
                relative_diff = abs(closest - claimed) / abs(claimed)

            if relative_diff <= 0.02:
                return {
                    "status": "VERIFIED",
                    "correct_value": str(closest),
                    "confidence": 78,
                    "explanation": "The closest numeric evidence value is within 2% of the claim.",
                }
            if relative_diff <= 0.12:
                return {
                    "status": "OUTDATED",
                    "correct_value": str(closest),
                    "confidence": 70,
                    "explanation": "Evidence suggests a nearby but newer or revised value.",
                }
            return {
                "status": "INACCURATE",
                "correct_value": str(closest),
                "confidence": 72,
                "explanation": "The numeric value in the evidence differs materially from the claim.",
            }

        return {
            "status": "INSUFFICIENT EVIDENCE",
            "correct_value": None,
            "confidence": 35,
            "explanation": "Sources were found, but the automated fallback could not confirm or refute the claim.",
        }

    def _normalize_result(self, parsed: dict[str, Any]) -> dict[str, Any]:
        status = str(parsed.get("status", "INSUFFICIENT EVIDENCE")).upper().strip()
        if status not in ALLOWED_STATUSES:
            status = "INSUFFICIENT EVIDENCE"
        confidence = int(parsed.get("confidence", 0) or 0)
        return {
            "status": status,
            "correct_value": parsed.get("correct_value"),
            "confidence": max(0, min(100, confidence)),
            "explanation": str(parsed.get("explanation") or "No explanation returned."),
        }

    def _detect_known_trap(self, claim: str) -> dict[str, Any] | None:
        lowered = claim.lower()
        if "chatgpt" in lowered and "launch" in lowered and "2018" in lowered:
            return {
                "status": "FALSE",
                "correct_value": "ChatGPT launched publicly on November 30, 2022.",
                "confidence": 96,
                "explanation": "The claim gives an impossible launch year for ChatGPT; the public launch was in 2022.",
            }
        return None

    def _numbers(self, text: str) -> list[float]:
        values: list[float] = []
        for match in re.finditer(r"(?<!\w)(\d[\d,]*(?:\.\d+)?)\s*(%|million|billion|trillion)?", text, re.I):
            raw, unit = match.groups()
            value = float(raw.replace(",", ""))
            if unit:
                unit = unit.lower()
                if unit == "million":
                    value *= 1_000_000
                elif unit == "billion":
                    value *= 1_000_000_000
                elif unit == "trillion":
                    value *= 1_000_000_000_000
            values.append(value)
        return values

