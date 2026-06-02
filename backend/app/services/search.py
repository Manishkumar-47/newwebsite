from dataclasses import dataclass
from urllib.parse import urlparse

import httpx

from app.config import Settings, get_settings


@dataclass
class SearchSource:
    title: str
    url: str
    snippet: str | None = None
    source_type: str = "web"


class SearchClient:
    def __init__(self, settings: Settings | None = None):
        self.settings = settings or get_settings()

    def search(self, claim: str) -> list[SearchSource]:
        sources: list[SearchSource] = []
        if self.settings.tavily_api_key:
            sources.extend(self._search_tavily(claim))
        if len(sources) < self.settings.search_results_per_claim and self.settings.serper_api_key:
            sources.extend(self._search_serper(claim))
        if len(sources) < self.settings.search_results_per_claim:
            sources.extend(self._search_duckduckgo(claim))
        return self._dedupe(sources)[: self.settings.search_results_per_claim]

    def _search_tavily(self, claim: str) -> list[SearchSource]:
        try:
            with httpx.Client(timeout=self.settings.request_timeout_seconds) as client:
                response = client.post(
                    "https://api.tavily.com/search",
                    json={
                        "api_key": self.settings.tavily_api_key,
                        "query": claim,
                        "search_depth": "basic",
                        "max_results": self.settings.search_results_per_claim,
                        "include_answer": False,
                    },
                )
                response.raise_for_status()
        except Exception:
            return []

        results = response.json().get("results", [])
        return [
            SearchSource(
                title=item.get("title") or item.get("url") or "Untitled source",
                url=item.get("url", ""),
                snippet=item.get("content"),
                source_type=self._classify_source(item.get("url", "")),
            )
            for item in results
            if item.get("url")
        ]

    def _search_serper(self, claim: str) -> list[SearchSource]:
        try:
            with httpx.Client(timeout=self.settings.request_timeout_seconds) as client:
                response = client.post(
                    "https://google.serper.dev/search",
                    headers={"X-API-KEY": self.settings.serper_api_key or ""},
                    json={"q": claim, "num": self.settings.search_results_per_claim},
                )
                response.raise_for_status()
        except Exception:
            return []

        results = response.json().get("organic", [])
        return [
            SearchSource(
                title=item.get("title") or item.get("link") or "Untitled source",
                url=item.get("link", ""),
                snippet=item.get("snippet"),
                source_type=self._classify_source(item.get("link", "")),
            )
            for item in results
            if item.get("link")
        ]

    def _search_duckduckgo(self, claim: str) -> list[SearchSource]:
        try:
            from duckduckgo_search import DDGS

            with DDGS(timeout=self.settings.request_timeout_seconds) as ddgs:
                results = list(ddgs.text(claim, max_results=self.settings.search_results_per_claim))
        except Exception:
            return []

        return [
            SearchSource(
                title=item.get("title") or item.get("href") or "Untitled source",
                url=item.get("href", ""),
                snippet=item.get("body"),
                source_type=self._classify_source(item.get("href", "")),
            )
            for item in results
            if item.get("href")
        ]

    def _dedupe(self, sources: list[SearchSource]) -> list[SearchSource]:
        seen: set[str] = set()
        unique: list[SearchSource] = []
        for source in sources:
            normalized = source.url.rstrip("/")
            if normalized and normalized not in seen:
                seen.add(normalized)
                unique.append(source)
        return sorted(unique, key=lambda item: self._source_priority(item.source_type))

    def _classify_source(self, url: str) -> str:
        domain = urlparse(url).netloc.lower()
        if not domain:
            return "web"
        if ".gov" in domain or domain.endswith(".nic.in") or domain.endswith(".gov.in"):
            return "government"
        if domain.endswith(".edu") or "ac." in domain:
            return "academic"
        if any(name in domain for name in ("worldbank", "imf.org", "oecd", "who.int", "un.org")):
            return "institutional"
        if any(name in domain for name in ("reuters", "apnews", "bbc", "thehindu", "economist")):
            return "trusted_news"
        return "web"

    @staticmethod
    def _source_priority(source_type: str) -> int:
        order = {
            "government": 0,
            "institutional": 1,
            "academic": 2,
            "trusted_news": 3,
            "web": 4,
        }
        return order.get(source_type, 5)

