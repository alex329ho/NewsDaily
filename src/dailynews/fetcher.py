"""Fetch news articles from the GDELT API."""
from __future__ import annotations

import logging
from typing import List, Dict

import requests

logger = logging.getLogger(__name__)
API_URL = "https://api.gdeltproject.org/api/v2/doc/doc"


def _normalize(article: dict) -> dict:
    """Ensure required keys exist and are strings."""
    return {
        "title": str(article.get("title", "")),
        "url": str(article.get("url", "")),
        "desc": str(
            article.get("seendescription")
            or article.get("description")
            or ""
        ),
    }


def fetch_news(
    topics: list[str],
    hours: int,
    region: str | None = None,
    language: str | None = None,
    maxrecords: int = 75,
) -> list[dict]:
    """Fetch articles about ``topics`` in the last ``hours`` hours.

    ``region`` and ``language`` may be used to filter results using the GDELT
    ``sourceCountry`` and ``sourceLang`` fields respectively.

    Returns a list of dictionaries with at least ``title``, ``url`` and ``desc``
    keys. In case of network errors or unexpected responses an empty list is
    returned and a warning is logged.
    """
    query = " OR ".join(topics)
    if region:
        query += f" sourceCountry:{region}"
        logger.info("Filtering by region: %s", region)
    if language:
        query += f" sourceLang:{language}"
        logger.info("Filtering by language: %s", language)
    params = {
        "query": query,
        "mode": "artlist",
        "format": "json",
        "maxrecords": maxrecords,
        "timespan": f"{hours}h",
    }
    try:
        resp = requests.get(API_URL, params=params, timeout=10)
        resp.raise_for_status()
    except requests.RequestException as exc:  # network issues
        logger.warning("Failed to fetch news: %s", exc)
        return []

    try:
        data = resp.json()
    except ValueError:  # not json
        logger.warning("Could not decode JSON response")
        return []

    articles = data.get("articles")
    if not isinstance(articles, list):
        logger.warning("Unexpected response shape: missing articles list")
        return []

    normalized = [_normalize(a) for a in articles]
    return normalized
