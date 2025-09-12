"""Email utilities for DailyNews."""
from __future__ import annotations

import logging
import os
import smtplib
from email.mime.text import MIMEText

logger = logging.getLogger(__name__)

REQUIRED_VARS = [
    "EMAIL_HOST",
    "EMAIL_PORT",
    "EMAIL_USERNAME",
    "EMAIL_PASSWORD",
]


def _load_settings() -> dict:
    env = {var: os.getenv(var) for var in REQUIRED_VARS}
    missing = [k for k, v in env.items() if not v]
    if missing:
        raise ValueError(
            f"Missing required email environment variables: {', '.join(missing)}"
        )
    env["EMAIL_FROM"] = os.getenv("EMAIL_FROM", env["EMAIL_USERNAME"])
    env["EMAIL_USE_SSL"] = os.getenv("EMAIL_USE_SSL", "true").lower() in (
        "1",
        "true",
        "yes",
    )
    return env


def send_email_summary(summary: str, recipient: str) -> None:
    """Send a summary email to ``recipient``.

    SMTP settings are read from environment variables documented in
    ``examples/.env.example``.
    """
    settings = _load_settings()

    msg = MIMEText(summary)
    msg["Subject"] = "DailyNews summary"
    msg["From"] = settings["EMAIL_FROM"]
    msg["To"] = recipient

    try:
        host = settings["EMAIL_HOST"]
        port = int(settings["EMAIL_PORT"])
        if settings["EMAIL_USE_SSL"]:
            with smtplib.SMTP_SSL(host, port) as smtp:
                smtp.login(settings["EMAIL_USERNAME"], settings["EMAIL_PASSWORD"])
                smtp.send_message(msg)
        else:
            with smtplib.SMTP(host, port) as smtp:
                smtp.starttls()
                smtp.login(settings["EMAIL_USERNAME"], settings["EMAIL_PASSWORD"])
                smtp.send_message(msg)
    except Exception as exc:  # pragma: no cover - network errors
        logger.warning("Could not send email: %s", exc)
        raise
