from __future__ import annotations

from typing import Any
import json
import os
from urllib import request


FIRECRAWL_URL = "https://api.firecrawl.dev/v2/search"


def city_hint(zip_code: str) -> str:
    if zip_code.startswith("787"):
        return "Austin, Texas"
    return "United States"


def coverage_hint(status: str, provider: str) -> str:
    normalized = status.lower()
    provider_text = provider.strip()
    if normalized == "uninsured":
        return "uninsured low income clinic medicaid CHIP application transportation assistance"
    if normalized == "medicaid":
        return f"{provider_text or 'Medicaid'} accepted clinic benefits transportation support"
    if normalized == "chip":
        return "CHIP child health coverage clinic eligibility income requirements"
    if normalized == "medicare":
        return f"{provider_text or 'Medicare'} primary care accepted clinic assistance"
    if normalized in {"aca_marketplace", "employer_plan", "underinsured"}:
        return f"{provider_text or 'commercial insurance'} network verification sliding scale clinic payment assistance"
    if normalized in {"tricare", "va"}:
        return f"{provider_text or normalized} community care clinic coverage verification"
    return f"{provider_text or normalized} clinic eligibility assistance"


def search_live_eligibility(profile: dict[str, Any]) -> dict[str, Any]:
    api_key = os.getenv("FIRECRAWL_API_KEY")
    if not api_key:
        return {
            "available": False,
            "summary": "Live public-resource lookup is unavailable right now.",
            "sources": [],
        }

    query = " ".join(
        [
            city_hint(profile.get("zip_code", "")),
            coverage_hint(profile.get("insurance_status", ""), profile.get("insurance_provider", "")),
            profile.get("care_need", ""),
            profile.get("household", ""),
            "site:gov OR site:org",
        ]
    ).strip()

    payload = {
        "query": query,
        "limit": 4,
        "sources": ["web"],
        "location": city_hint(profile.get("zip_code", "")),
        "country": "US",
        "timeout": 45000,
        "scrapeOptions": {
            "formats": ["markdown"],
            "onlyMainContent": True,
        },
    }
    req = request.Request(
        FIRECRAWL_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with request.urlopen(req, timeout=50) as response:
            body = json.loads(response.read().decode("utf-8"))
    except Exception as exc:
        return {
            "available": False,
            "summary": "Live public-resource lookup could not be completed right now.",
            "sources": [],
            "error": str(exc),
        }

    raw_sources = body.get("data", {}).get("web", [])
    sources = []
    for item in raw_sources[:3]:
        sources.append(
            {
                "title": item.get("title") or item.get("url", "Eligibility source"),
                "url": item.get("url", ""),
                "snippet": item.get("description") or first_markdown_line(item.get("markdown", "")),
            }
        )

    if not sources:
        return {
            "available": True,
            "summary": "No live public resources were returned for this request.",
            "sources": [],
        }

    return {
        "available": True,
        "summary": f"Found {len(sources)} live public resources related to the current care and support request.",
        "sources": sources,
        "query": query,
    }


def first_markdown_line(markdown: str) -> str:
    for line in markdown.splitlines():
        cleaned = line.strip("# ").strip()
        if cleaned:
            return cleaned[:220]
    return ""
