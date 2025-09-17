"""Shared service orchestration between CLI and API."""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from .fetcher import fetch_news
from .summarizer import summarize_articles


def _format_headlines(articles: List[dict], limit: int = 10) -> List[Dict[str, str]]:
    formatted: List[Dict[str, str]] = []
    for article in articles[:limit]:
        formatted.append(
            {
                "title": str(article.get("title") or ""),
                "url": str(article.get("url") or ""),
                "source_domain": str(article.get("source_domain") or ""),
                "seendate": str(article.get("seendate") or ""),
            }
        )
    return formatted


def summarize_run(
    topics: List[str],
    hours: int,
    *,
    region: Optional[str] = None,
    language: Optional[str] = None,
    maxrecords: int = 75,
) -> Dict[str, Any]:
    """Fetch articles then summarise them."""

    articles = fetch_news(
        topics,
        hours,
        region=region,
        language=language,
        maxrecords=maxrecords,
    )
    summary = summarize_articles(articles)

    return {
        "topics": topics,
        "hours": hours,
        "region": region,
        "language": language,
        "fetched_count": len(articles),
        "summary": summary,
        "headlines": _format_headlines(articles),
    }
