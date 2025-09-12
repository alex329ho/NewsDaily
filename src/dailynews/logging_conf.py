"""Logging configuration for DailyNews."""
from __future__ import annotations

import logging


def configure_logging(verbose: bool) -> None:
    """Configure root logging.

    Parameters
    ----------
    verbose: bool
        If ``True`` sets logging level to DEBUG, otherwise INFO.
    """
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
