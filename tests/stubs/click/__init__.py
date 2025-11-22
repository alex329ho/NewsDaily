"""Tiny subset of the click API for testing."""
from __future__ import annotations


class ClickException(Exception):
    """Minimal stand-in for click.ClickException."""

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message

    def format_message(self) -> str:
        return self.message

    def __str__(self) -> str:  # pragma: no cover - parity with click
        return self.message


def command(*args, **kwargs):
    def decorator(f):
        return f
    if args and callable(args[0]):
        return args[0]
    return decorator


def option(*args, **kwargs):
    def decorator(f):
        return f
    return decorator


def echo(message: str = "") -> None:
    print(message)
