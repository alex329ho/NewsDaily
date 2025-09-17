"""Configuration helpers for DailyNews."""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class Settings:
    """Simple settings loaded from environment variables."""

    hf_api_token: Optional[str]
    hf_model: Optional[str]
    api_port: int
    api_base_url: str

    @property
    def has_hf_credentials(self) -> bool:
        return bool(self.hf_api_token and self.hf_model)


_settings_cache: Optional[Settings] = None


def _load_settings() -> Settings:
    token = os.getenv("HF_API_TOKEN")
    model = os.getenv("HF_MODEL")
    base_url = (os.getenv("DAILYNEWS_API_URL") or "http://localhost:8000").rstrip("/")
    port_raw = os.getenv("API_PORT", "8000")
    try:
        port = int(port_raw)
    except ValueError:
        raise ValueError("API_PORT must be an integer") from None

    return Settings(
        hf_api_token=token,
        hf_model=model,
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
