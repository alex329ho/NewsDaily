"""Command line interface for DailyNews."""
from __future__ import annotations

import logging
from typing import List

import click

from .fetcher import fetch_news
from .logging_conf import configure_logging
from .summarizer import summarize_articles


@click.command()
@click.option(
    "--topics",
    "-t",
    default="finance,economy,politics",
    help="Comma-separated topics to search for",
)
@click.option("--hours", "-h", default=8, type=int, help="Lookback period in hours")
@click.option("--email", "-e", default=None, help="Email address to send summary to")
@click.option("--maxrecords", default=75, type=int, show_default=True)
@click.option("--verbose", "-v", is_flag=True, help="Enable debug logging")
def main(
    topics: str,
    hours: int,
    email: str | None,
    maxrecords: int,
    verbose: bool,
) -> None:
    """Entry point for the dailynews command."""
    configure_logging(verbose)
    logger = logging.getLogger("dailynews.cli")

    topic_list = [t.strip() for t in topics.split(",") if t.strip()]
    logger.info("Fetching news for topics: %s", ", ".join(topic_list))

    articles = fetch_news(topic_list, hours, maxrecords=maxrecords)
    if not articles:
        click.echo(
            "No articles found. Check your internet connection or try different topics."
        )
        raise SystemExit(0)

    summary = summarize_articles(articles)
    header = f"DailyNews summary for {', '.join(topic_list)} (last {hours}h):"
    click.echo(header)
    click.echo(summary)

    headlines = articles[:3]
    if headlines:
        click.echo("\nTop headlines:")
        for art in headlines:
            domain = art.get("url", "").split("//")[-1].split("/")[0]
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
