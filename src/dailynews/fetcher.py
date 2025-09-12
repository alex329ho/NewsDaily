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

    Returns a list of dictionaries with at least ``title``, ``url`` and ``desc``
    keys. In case of network errors or unexpected responses an empty list is
    returned and a warning is logged.
    """
    query = " OR ".join(topics)
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
