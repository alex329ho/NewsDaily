"""Utilities for summarising news articles using HuggingFace transformers."""
from __future__ import annotations

import logging
import os
from typing import Callable, Iterable, List

from .config import get_settings

logger = logging.getLogger(__name__)

SummarizerFn = Callable[[str, str], str]

_summarizer: SummarizerFn | None = None
_MAX_CHARS = 1000
_MAX_ARTICLES = 5


def _build_prompt(bullet_text: str) -> str:
    cleaned = bullet_text.strip() or "- (no headlines provided)"
    return (
        "Summarize the following recent news headlines into 2–4 concise sentences "
        "for a morning briefing:\n"
        f"{cleaned}\n"
        "Keep it factual and brief."
    )


def get_summarizer() -> SummarizerFn:
    """Return a cached summarizer callable."""

    global _summarizer
    if _summarizer is not None:
        return _summarizer

    if os.getenv("DAILYNEWS_SKIP_HF") == "1":
        def _stub(_: str, __: str) -> str:
            return "Summarization skipped (DAILYNEWS_SKIP_HF=1)."

        _summarizer = _stub
        return _summarizer

    settings = get_settings()
    if not settings.has_hf_credentials:
        raise RuntimeError(
            "HF_MODEL and HF_API_TOKEN must be set in the environment before "
            "summarization can run."
        )

    try:
        from transformers import pipeline  # type: ignore

        summarization_pipeline = pipeline(
            "summarization",
            model=settings.hf_model,
            use_auth_token=settings.hf_api_token,
        )

        def _summarize(text: str, bullet_text: str) -> str:
            normalized = (text or bullet_text).replace("\n", " ").strip()
            result = summarization_pipeline(
                normalized,
                max_length=160,
                min_length=20,
                do_sample=False,
            )
            summary = result[0].get("summary_text", "") if result else ""
            return str(summary).strip()

        _summarizer = _summarize
        return _summarizer
    except Exception as exc:  # pragma: no cover - requires external model
        logger.warning(
            "Could not initialise summarization pipeline, falling back to text "
            "generation: %s",
            exc,
        )
        try:
            from transformers import pipeline  # type: ignore

            text_generation = pipeline(
                "text-generation",
                model=settings.hf_model,
                use_auth_token=settings.hf_api_token,
                max_new_tokens=160,
                do_sample=False,
                temperature=0.0,
            )

            def _generate(_: str, bullet_text: str) -> str:
                prompt = _build_prompt(bullet_text)
                outputs = text_generation(prompt)
                generated = outputs[0].get("generated_text", "") if outputs else ""
                if generated.startswith(prompt):
                    generated = generated[len(prompt) :]
                return generated.strip()

            _summarizer = _generate
            return _summarizer
        except Exception as inner:  # pragma: no cover - requires external model
            raise RuntimeError(
                "Unable to load Hugging Face model for summarization"
            ) from inner


def _prepare_text(articles: Iterable[dict]) -> tuple[str, str]:
    text_parts: List[str] = []
    bullet_lines: List[str] = []
    total_chars = 0

    for article in list(articles)[:_MAX_ARTICLES]:
        title = str(article.get("title") or "").strip()
        desc = str(article.get("desc") or article.get("description") or "").strip()
        content = " ".join(part for part in [title, desc] if part).strip()
        if not content:
            continue
        content = content.replace("\n", " ")
        remaining = _MAX_CHARS - total_chars
        if remaining <= 0:
            break
        if len(content) > remaining:
            content = content[:remaining]
        total_chars += len(content)
        text_parts.append(content)
        bullet_label = title or (desc[:60] + ("..." if len(desc) > 60 else ""))
        bullet_lines.append(f"- {bullet_label.strip()}" if bullet_label else "- (untitled)")

    text = " ".join(text_parts).strip()
    bullets = "\n".join(bullet_lines).strip()
    return text, bullets


def summarize_articles(articles: list[dict], per_topic: bool = False) -> str:
    """Summarize a list of articles."""
    if not articles:
        return "No news available."

    text, bullets = _prepare_text(articles)
    if not text and not bullets:
        return "No news available."

    summarizer = get_summarizer()

    try:
        summary = summarizer(text, bullets)
    except TypeError:  # pragma: no cover - compatibility with test stubs
        summary = summarizer(text)  # type: ignore[misc]
    except Exception as exc:  # pragma: no cover - network/other errors
        logger.warning("Summarization failed: %s", exc)
        summary = text[:200]

    summary = (summary or "").strip()
    return summary or "No news available."


def summarize_by_topic(topics: list[str], articles: list[dict]) -> dict[str, str]:
    """Group articles by topic keyword and summarize each group."""
    from collections import defaultdict

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
