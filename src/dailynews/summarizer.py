"""Utilities for summarising news articles using HuggingFace transformers."""
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

def _model_access_url(model_name: str | None) -> str:
    if not model_name:
        return "https://huggingface.co/"
    sanitized = model_name.strip("/")
    return f"https://huggingface.co/{sanitized}?library=transformers"


def _ensure_transformer_backend_available(model_name: str | None) -> None:
    try:
        from transformers.utils import (  # type: ignore
            is_flax_available,
            is_tf_available,
            is_torch_available,
        )
    except ImportError as exc:  # pragma: no cover - requires transformers package
        raise RuntimeError(
            "The 'transformers' package is required for summarization. Install it "
            "with `pip install transformers` or set DAILYNEWS_SKIP_HF=1 for offline "
            "runs."
        ) from exc

    if not any([is_torch_available(), is_tf_available(), is_flax_available()]):
        model_label = model_name or "the configured model"
        raise RuntimeError(
            "Cannot load Hugging Face model "
            f"'{model_label}' because no deep learning backend is available. "
            "Install PyTorch, TensorFlow >= 2.0, or Flax (for example: `pip install "
            "torch`) before running DailyNews summarization, or set "
            "DAILYNEWS_SKIP_HF=1 for offline development."
        )


def _is_authentication_error(exc: Exception) -> bool:
    response = getattr(exc, "response", None)
    status = getattr(response, "status_code", None)
    if status in {401, 403}:
        return True
    message = str(exc).lower()
    indicators = [
        "401",
        "403",
        "gated repo",
        "access to model",
        "please log in",
    ]
    return any(indicator in message for indicator in indicators)


def _raise_model_access_error(model_name: str | None, exc: Exception) -> None:
    link = _model_access_url(model_name)
    model_label = model_name or "the configured model"
    raise RuntimeError(
        "Access to the Hugging Face model "
        f"'{model_label}' is restricted. Request access at {link} and ensure "
        "HF_API_TOKEN has permission for the repository."
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

    _ensure_transformer_backend_available(settings.hf_model)

    try:
        from transformers import pipeline  # type: ignore
    except ImportError as exc:  # pragma: no cover - requires transformers package
        raise RuntimeError(
            "The 'transformers' package is required for summarization. Install it "
            "with `pip install transformers`."
        ) from exc

    try:
        summarization_pipeline = pipeline(
            "summarization",
            model=settings.hf_model,
            use_auth_token=settings.hf_api_token,
        )
    except Exception as exc:  # pragma: no cover - requires external model
        if _is_authentication_error(exc):
            _raise_model_access_error(settings.hf_model, exc)
        logger.warning(
            "Could not initialise summarization pipeline, falling back to text "
            "generation: %s",
            exc,
        )
    else:
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

    try:
        text_generation = pipeline(
            "text-generation",
            model=settings.hf_model,
            use_auth_token=settings.hf_api_token,
            max_new_tokens=160,
            do_sample=False,
            temperature=0.0,
        )
    except Exception as inner:  # pragma: no cover - requires external model
        if _is_authentication_error(inner):
            _raise_model_access_error(settings.hf_model, inner)
        raise RuntimeError(
            "Unable to load Hugging Face model for summarization. Install a "
            "supported backend or set DAILYNEWS_SKIP_HF=1 for offline runs."
        ) from inner

    def _generate(_: str, bullet_text: str) -> str:
        prompt = _build_prompt(bullet_text)
        outputs = text_generation(prompt)
        generated = outputs[0].get("generated_text", "") if outputs else ""
        if generated.startswith(prompt):
            generated = generated[len(prompt) :]
        return generated.strip()

    _summarizer = _generate
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
