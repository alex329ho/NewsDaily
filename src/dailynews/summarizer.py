"""Utilities for summarising news articles using HuggingFace transformers."""
from __future__ import annotations

import logging
import os
from collections import defaultdict
from typing import Iterable

logger = logging.getLogger(__name__)

_summarizer = None
_MAX_CHARS = 1000


def get_summarizer():
    """Return a cached summarizer pipeline or a stub.

    When ``DAILYNEWS_SKIP_HF=1`` is set in the environment a tiny stub is
    returned that avoids loading Hugging Face models. Otherwise the
    ``sshleifer/distilbart-cnn-12-6`` model is loaded on first use.
    """

    global _summarizer
    if _summarizer is not None:
        return _summarizer

    if os.getenv("DAILYNEWS_SKIP_HF") == "1":
        def _stub(text: str, **_: object) -> list[dict]:
            return [{"summary_text": "Model disabled."}]

        _summarizer = _stub
        return _summarizer

    try:
        from transformers import pipeline  # type: ignore

        _summarizer = pipeline(
            "summarization", model="sshleifer/distilbart-cnn-12-6"
        )
    except Exception as exc:  # pragma: no cover
        logger.warning("Could not load summarization model: %s", exc)

        def _fallback(text: str, **_: object) -> list[dict]:
            return [{"summary_text": text[:200]}]

        _summarizer = _fallback
    return _summarizer


def _prepare_text(articles: Iterable[dict]) -> str:
    parts: list[str] = []
    for art in list(articles)[:5]:
        title = art.get("title") or ""
        desc = art.get("desc") or ""
        parts.append(f"{title}. {desc}".strip())
    combined = " ".join(p for p in parts if p)
    return combined[:_MAX_CHARS]


def summarize_articles(articles: list[dict], per_topic: bool = False) -> str:
    """Summarize a list of articles."""
    if not articles:
        return "No news available."

    text = _prepare_text(articles)
    if not text.strip():
        return "No news available."

    summ = get_summarizer()

    try:
        result = summ(text, max_length=100, do_sample=False)
        summary = result[0]["summary_text"].strip()
    except Exception as exc:  # pragma: no cover - network/other errors
        logger.warning("Summarization failed: %s", exc)
        summary = text[:200]

    return summary or "No news available."


def summarize_by_topic(topics: list[str], articles: list[dict]) -> dict[str, str]:
    """Group articles by topic keyword and summarize each group."""
    grouped: dict[str, list[dict]] = defaultdict(list)
    for art in articles:
        text = f"{art.get('title','')} {art.get('desc','')}".lower()
        for topic in topics:
            if topic.lower() in text:
                grouped[topic].append(art)

    summaries: dict[str, str] = {}
    for topic, arts in grouped.items():
        summaries[topic] = summarize_articles(arts)
    return summaries
