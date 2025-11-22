"""Configuration helpers for DailyNews."""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class Settings:
    """Simple settings loaded from environment variables."""

    openrouter_api_key: Optional[str]
    openrouter_model: str
    openrouter_api_url: str
    api_port: int
    api_base_url: str

    @property
    def has_openrouter_credentials(self) -> bool:
        return bool(self.openrouter_api_key)


_settings_cache: Optional[Settings] = None


def _load_settings() -> Settings:
    token = os.getenv("OPENROUTER_API_KEY")
    model = os.getenv("OPENROUTER_MODEL") or "x-ai/grok-4.1-fast"
    api_url = (
        os.getenv("OPENROUTER_API_URL")
        or "https://openrouter.ai/x-ai/grok-4.1-fast/api"
    )
    base_url = (os.getenv("DAILYNEWS_API_URL") or "http://localhost:8000").rstrip("/")
    port_raw = os.getenv("API_PORT", "8000")
    try:
        port = int(port_raw)
    except ValueError:
        raise ValueError("API_PORT must be an integer") from None

    return Settings(
        openrouter_api_key=token,
        openrouter_model=model,
        openrouter_api_url=api_url,
        api_port=port,
        api_base_url=base_url,
    )


def get_settings() -> Settings:
    """Return cached settings loaded from the environment."""
    global _settings_cache
    if _settings_cache is None:
        _settings_cache = _load_settings()
    return _settings_cache


def reset_settings() -> None:
    """Reset cached settings (mainly for tests)."""
    global _settings_cache
    _settings_cache = None
