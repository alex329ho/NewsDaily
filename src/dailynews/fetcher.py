"""Fetch news articles from the GDELT API."""
from __future__ import annotations

import logging
from datetime import datetime
from urllib.parse import urlparse

import requests

logger = logging.getLogger(__name__)
API_URL = "https://api.gdeltproject.org/api/v2/doc/doc"


def normalize_article(article: dict) -> dict:
    """Return a normalized article dict with safe defaults."""
    title = str(article.get("title") or "")
    url = str(article.get("url") or "")
    desc = str(
        article.get("seendescription")
        or article.get("description")
        or ""
    )
    domain = urlparse(url).netloc
    raw_date = str(article.get("seendate") or "")
    seendate = ""
    if raw_date:
        try:
            seendate = datetime.strptime(raw_date, "%Y%m%d%H%M").isoformat()
        except ValueError:
            seendate = raw_date
    return {
        "title": title,
        "url": url,
        "desc": desc,
        "source_domain": domain,
        "seendate": seendate,
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

    Returns a list of dictionaries with at least ``title``, ``url``, ``desc``,
    ``source_domain`` and ``seendate`` keys. In case of network errors or
    unexpected responses an empty list is returned and a warning is logged.
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

    return [normalize_article(a) for a in articles]
