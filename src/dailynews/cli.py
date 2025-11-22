"""Command line interface for DailyNews."""
from __future__ import annotations

import logging
import sys
from typing import Any, Dict, List

import click
import requests

from .config import get_settings
from .logging_conf import configure_logging
from .service import summarize_run


def _parse_topics(topics: str) -> List[str]:
    parsed = [t.strip() for t in topics.split(",") if t.strip()]
    return [topic for topic in parsed if topic]


def _call_backend(params: Dict[str, Any]) -> Dict[str, Any]:
    settings = get_settings()
    base_url = settings.api_base_url.rstrip("/")
    url = f"{base_url}/summary"
    clean_params = {k: v for k, v in params.items() if v is not None}

    try:
        resp = requests.get(url, params=clean_params, timeout=20)
        resp.raise_for_status()
    except requests.RequestException as exc:
        raise click.ClickException(f"Failed to call backend API: {exc}") from exc

    try:
        data = resp.json()
    except ValueError as exc:  # pragma: no cover - unexpected backend response
        raise click.ClickException("Backend API returned invalid JSON") from exc

    return data


def _extract_topics(value: Any) -> List[str]:
    if isinstance(value, list):
        return [str(item) for item in value]
    if isinstance(value, str):
        return [part.strip() for part in value.split(",") if part.strip()]
    return []


@click.command()
@click.option(
    "--topics",
    "-t",
    default="finance,economy,politics",
    help="Comma-separated topics to search for",
)
@click.option("--hours", "-h", default=8, type=int, help="Lookback period in hours")
@click.option("--email", "-e", default=None, help="Email address to send summary to")
@click.option("--region", "-r", default=None, help="Source country code, e.g. 'US'")
@click.option(
    "--language",
    "-l",
    default=None,
    help="Source language code, e.g. 'en'",
)
@click.option("--maxrecords", default=75, type=int, show_default=True)
@click.option("--verbose", "-v", is_flag=True, help="Enable debug logging")
@click.option(
    "--use-api/--no-use-api",
    default=False,
    help="Fetch summaries from the running FastAPI backend",
)
def main(
    topics: str,
    hours: int,
    email: str | None,
    region: str | None,
    language: str | None,
    maxrecords: int,
    verbose: bool,
    use_api: bool,
) -> None:
    """Entry point for the dailynews command."""
    if sys.version_info < (3, 10):
        version = ".".join(map(str, sys.version_info[:3]))
        raise click.ClickException(
            f"Python 3.10+ is required to run DailyNews (found {version})."
        )

    configure_logging(verbose)
    logger = logging.getLogger("dailynews.cli")

    topic_list = _parse_topics(topics)
    if not topic_list:
        raise click.ClickException("Please provide at least one topic.")

    logger.info("Fetching news for topics: %s", ", ".join(topic_list))

    params = {
        "topics": ",".join(topic_list),
        "hours": hours,
        "region": region,
        "language": language,
        "maxrecords": maxrecords,
    }

    if use_api:
        data = _call_backend(params)
    else:
        data = summarize_run(
            topic_list,
            hours,
            region=region,
            language=language,
            maxrecords=maxrecords,
        )

    topics_display = _extract_topics(data.get("topics", topic_list)) or topic_list
    summary = str(data.get("summary") or "No news available.")
    fetched_count = int(data.get("fetched_count", 0))
    headlines = data.get("headlines") or []

    if use_api and fetched_count == 0 and summary.lower().startswith("no news"):
        click.echo("No articles found by backend API.")
    elif not use_api and fetched_count == 0:
        click.echo(
            "No articles found. Check your internet connection or try different topics."
        )
        raise SystemExit(0)

    header = (
        "DailyNews summary for "
        f"{', '.join(topics_display)} (last {hours}h, "
        f"region={region or 'All'}, lang={language or 'All'}):"
    )
    click.echo(header)
    click.echo(summary)

    top_headlines = headlines[:3]
    if top_headlines:
        click.echo("\nTop headlines:")
        for art in top_headlines:
            url = art.get("url", "")
            if isinstance(url, str) and url:
                domain = url.split("//")[-1].split("/")[0]
            else:
                domain = art.get("source_domain") or ""
            click.echo(f"- {art.get('title')} ({domain})")

    if email:
        try:
            from .emailer import send_email_summary

            send_email_summary(summary, email)
            click.echo(f"Email sent to {email}")
        except Exception as exc:  # pragma: no cover - network errors
            click.echo(f"Failed to send email: {exc}")


if __name__ == "__main__":
    main()
