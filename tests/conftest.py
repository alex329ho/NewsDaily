import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests" / "stubs"))
sys.path.insert(0, str(ROOT / "src"))

from dailynews import config as config_module, summarizer


@pytest.fixture(autouse=True)
def _test_env(monkeypatch):
    monkeypatch.setenv("DAILYNEWS_SKIP_SUMMARY", "1")
    config_module.reset_settings()
    summarizer._summarizer = None
    yield
    config_module.reset_settings()
    summarizer._summarizer = None
