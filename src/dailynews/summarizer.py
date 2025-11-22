"""Utilities for summarising news articles using the OpenRouter API."""
from __future__ import annotations

import logging
import os
import re
from dataclasses import dataclass
from html import unescape
from typing import Callable, Iterable, List

import requests

from .config import get_settings

logger = logging.getLogger(__name__)

SummarizerFn = Callable[[str, str], str]

_summarizer: SummarizerFn | None = None
_MAX_CHARS = 1000
_MAX_ARTICLES = 5
_MAX_REMOTE_CHARS = 8000
_SYSTEM_INSTRUCTION = (
    "You are a news briefing assistant. Given recent headlines and snippets, "
    "produce a factual, concise summary in 2–4 sentences. Avoid embellishment "
    "and keep the tone neutral."
)


@dataclass
class PreparedArticle:
    """Representation of article data ready for summarisation."""

    title: str
    link_text: str
    content: str

    @property
    def bullet_line(self) -> str:
        return f"- {self.title}{self.link_text}"


def _build_prompt(bullet_text: str) -> str:
    cleaned = bullet_text.strip() or "- (no headlines provided)"
    return (
        "Summarize the following recent news headlines into 2–4 concise sentences "
        "for a morning briefing:\n"
        f"{cleaned}\n"
        "Keep it factual and brief."
    )


def _is_authentication_error(exc: Exception) -> bool:
    response = getattr(exc, "response", None)
    status = getattr(response, "status_code", None)
    if status in {401, 403}:
        return True
    message = str(exc).lower()
    indicators = ["401", "403", "unauthorized", "forbidden"]
    return any(indicator in message for indicator in indicators)


def _raise_model_access_error(api_url: str, model_name: str, exc: Exception) -> None:
    raise RuntimeError(
        "Access to the OpenRouter model is restricted. Confirm the "
        "OPENROUTER_API_KEY is valid and that your account can call "
        f"'{model_name}' via {api_url}."
    ) from exc

_SCRIPT_STYLE_RE = re.compile(r"(?is)<(script|style).*?>.*?</\\1>")
_HTML_TAG_RE = re.compile(r"(?s)<[^>]+>")


def _strip_html(raw: str) -> str:
    """Remove script/style blocks and tags from HTML content."""

    if "<" not in raw:
        return raw
    cleaned = _SCRIPT_STYLE_RE.sub(" ", raw)
    cleaned = _HTML_TAG_RE.sub(" ", cleaned)
    return cleaned


def _normalise_text(text: str) -> str:
    """Normalise whitespace and HTML entities in fetched article text."""

    text = unescape(text)
    text = text.replace("\x00", " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _download_article_text(url: str) -> str:
    """Fetch article text from ``url`` and strip HTML tags.

    Network failures or non-text responses return an empty string. Only the
    first ``_MAX_REMOTE_CHARS`` characters are processed to keep responses
    manageable for summarisation.
    """

    if not url:
        return ""
    headers = {"User-Agent": "DailyNewsBot/1.0"}
    try:
        resp = requests.get(url, timeout=5, headers=headers)
        resp.raise_for_status()
    except requests.RequestException as exc:  # pragma: no cover - network errors
        logger.debug("Failed to fetch article content for %s: %s", url, exc)
        return ""

    content_type = resp.headers.get("Content-Type", "")
    if "text" not in content_type:
        return ""

    text = resp.text
    if len(text) > _MAX_REMOTE_CHARS:
        text = text[:_MAX_REMOTE_CHARS]
    text = _strip_html(text)
    return _normalise_text(text)


def _resolve_article_content(article: dict) -> str:
    """Return textual content for ``article`` using remote fetch as needed."""

    inline_body = str(
        article.get("content") or article.get("body") or ""
    ).strip()
    if inline_body:
        return _normalise_text(_strip_html(inline_body))

    url = str(article.get("url") or "").strip()
    remote = _download_article_text(url)
    if remote:
        return remote

    fallback = str(
        article.get("desc") or article.get("description") or ""
    ).strip()
    if fallback:
        return _normalise_text(_strip_html(fallback))

    return ""


def _call_openrouter(prompt: str, *, api_url: str, api_key: str, model: str) -> str:
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": _SYSTEM_INSTRUCTION},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.2,
        "max_tokens": 240,
    }

    try:
        response = requests.post(api_url, json=payload, headers=headers, timeout=20)
        response.raise_for_status()
    except requests.HTTPError as exc:  # pragma: no cover - requires network
        if _is_authentication_error(exc):
            _raise_model_access_error(api_url, model, exc)
        raise

    except requests.RequestException as exc:  # pragma: no cover - requires network
        raise RuntimeError(f"OpenRouter request failed: {exc}") from exc

    data = response.json()
    choices = data.get("choices") or []
    if choices:
        message = choices[0].get("message", {})
        content = message.get("content", "")
        if content:
            return str(content).strip()

    return ""


def get_summarizer() -> SummarizerFn:
    """Return a cached summarizer callable."""

    global _summarizer
    if _summarizer is not None:
        return _summarizer

    if os.getenv("DAILYNEWS_SKIP_HF") == "1" or os.getenv("DAILYNEWS_SKIP_SUMMARY") == "1":
        def _stub(_: str, __: str) -> str:
            return "Summarization skipped (DAILYNEWS_SKIP_SUMMARY=1)."

        _summarizer = _stub
        return _summarizer

    settings = get_settings()
    if not settings.has_openrouter_credentials:
        raise RuntimeError(
            "OPENROUTER_API_KEY must be set in the environment before summarization "
            "can run."
        )

    def _summarize(_: str, bullet_text: str) -> str:
        prompt = _build_prompt(bullet_text)
        return _call_openrouter(
            prompt,
            api_url=settings.openrouter_api_url,
            api_key=settings.openrouter_api_key or "",
            model=settings.openrouter_model,
        )

    _summarizer = _summarize
    return _summarizer


def _prepare_articles(articles: Iterable[dict]) -> List[PreparedArticle]:
    """Return a list of articles capped by ``_MAX_ARTICLES`` with content."""

    prepared: List[PreparedArticle] = []
    for article in list(articles)[:_MAX_ARTICLES]:
        content = _resolve_article_content(article)
        if not content:
            continue

        if len(content) > _MAX_CHARS:
            content = content[:_MAX_CHARS]

        raw_title = str(article.get("title") or "").strip()
        title = raw_title or "(untitled)"

        url = str(article.get("url") or "").strip()
        link_target = url or str(article.get("source_domain") or "").strip()
        link_text = f" ({link_target})" if link_target else ""

        prepared.append(
            PreparedArticle(
                title=title,
                link_text=link_text,
                content=content,
            )
        )

    return prepared


def summarize_articles(articles: list[dict], per_topic: bool = False) -> str:
    """Summarize a list of articles."""

    if not articles:
        return "No news available."

    prepared_articles = _prepare_articles(articles)
    if not prepared_articles:
        return "No news available."

    summarizer = get_summarizer()
    summaries: List[str] = []

    for item in prepared_articles:
        try:
            summary = summarizer(item.content, item.bullet_line)
        except TypeError:  # pragma: no cover - compatibility with test stubs
            summary = summarizer(item.content)  # type: ignore[misc]
        except Exception as exc:  # pragma: no cover - network/other errors
            logger.warning("Summarization failed for %s: %s", item.title, exc)
            summary = item.content[:200]

        summary = (summary or "").strip()
        if not summary:
            continue
        summaries.append(f"{item.bullet_line}\n  {summary}")

    if not summaries:
        return "No news available."

    return "\n".join(summaries)


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
