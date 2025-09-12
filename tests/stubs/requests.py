"""Minimal stub of the requests module for offline testing."""

class RequestException(Exception):
    pass


class exceptions:
    ConnectionError = type("ConnectionError", (RequestException,), {})


def get(*args, **kwargs):  # pragma: no cover - should be patched in tests
    raise RequestException("Network not available")
