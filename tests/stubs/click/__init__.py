"""Tiny subset of the click API for testing."""
from __future__ import annotations


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
