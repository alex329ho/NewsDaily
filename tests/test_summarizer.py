import types

import pytest

from dailynews import summarizer
from dailynews.config import reset_settings

API_URL = "https://openrouter.ai/x-ai/grok-4.1-fast/api"
MODEL_NAME = "x-ai/grok-4.1-fast"


class DummyRequestException(Exception):
    pass


class DummyHTTPError(DummyRequestException):
    def __init__(self, response: object | None = None) -> None:
        super().__init__("http error")
        self.response = response


def test_summarize_empty_returns_message():
    assert summarizer.summarize_articles([]) == "No news available."


def test_summarize_basic_text_contains_keywords(monkeypatch):
    monkeypatch.setattr(
        summarizer,
        "_download_article_text",
        lambda url: "The global economy is booming thanks to innovation.",
    )

    def fake_sum(text: str, bullet_text: str) -> str:
        assert "booming" in text
        assert bullet_text.startswith("- Economy (https://example.com/economy)")
        return "Summary about economy"

    monkeypatch.setattr(summarizer, "get_summarizer", lambda: fake_sum)
    articles = [{"title": "Economy", "url": "https://example.com/economy"}]
    result = summarizer.summarize_articles(articles)
    assert result.startswith("- Economy (https://example.com/economy)")
    assert "summary about economy" in result.lower()


def test_summarize_by_topic(monkeypatch):
    monkeypatch.setattr(summarizer, "_download_article_text", lambda _: "")

    def fake_sum(text: str, bullet_text: str) -> str:
        assert bullet_text.startswith("-")
        return f"summary for {bullet_text}"

    monkeypatch.setattr(summarizer, "get_summarizer", lambda: fake_sum)
    articles = [
        {"title": "Economy today", "desc": "great"},
        {"title": "Politics", "desc": "meh"},
    ]
    result = summarizer.summarize_by_topic(["economy", "politics"], articles)
    assert set(result) == {"economy", "politics"}
    assert "summary for - Economy today" in result["economy"]
    assert "summary for - Politics" in result["politics"]


def test_stub_used_when_skip_env(monkeypatch):
    monkeypatch.setenv("DAILYNEWS_SKIP_SUMMARY", "1")
    summarizer._summarizer = None
    summary_fn = summarizer.get_summarizer()
    result = summary_fn("text", "- bullet")
    assert "DAILYNEWS_SKIP_SUMMARY" in result


def test_get_summarizer_raises_for_missing_key(monkeypatch):
    monkeypatch.delenv("DAILYNEWS_SKIP_SUMMARY", raising=False)
    monkeypatch.setenv("OPENROUTER_MODEL", MODEL_NAME)
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    reset_settings()
    summarizer._summarizer = None

    with pytest.raises(RuntimeError) as excinfo:
        summarizer.get_summarizer()

    assert "OPENROUTER_API_KEY" in str(excinfo.value)


def test_get_summarizer_auth_error_mentions_access_link(monkeypatch):
    monkeypatch.delenv("DAILYNEWS_SKIP_SUMMARY", raising=False)
    monkeypatch.setenv("OPENROUTER_API_KEY", "token")
    monkeypatch.setenv("OPENROUTER_MODEL", MODEL_NAME)
    reset_settings()
    summarizer._summarizer = None

    class DummyResponse:
        status_code = 401

        def raise_for_status(self) -> None:
            raise DummyHTTPError(response=self)

    def fake_post(*_: object, **__: object) -> DummyResponse:
        return DummyResponse()

    fake_requests = types.SimpleNamespace()
    fake_requests.HTTPError = DummyHTTPError
    fake_requests.RequestException = DummyRequestException
    fake_requests.post = fake_post  # type: ignore[attr-defined]
    monkeypatch.setattr(summarizer, "requests", fake_requests)

    with pytest.raises(RuntimeError) as excinfo:
        summary_fn = summarizer.get_summarizer()
        summary_fn("text", "- bullet")

    message = str(excinfo.value)
    assert MODEL_NAME in message
    assert API_URL in message


def test_get_summarizer_uses_configured_payload(monkeypatch):
    monkeypatch.delenv("DAILYNEWS_SKIP_SUMMARY", raising=False)
    monkeypatch.setenv("OPENROUTER_API_KEY", "secret-token")
    monkeypatch.setenv("OPENROUTER_MODEL", MODEL_NAME)
    monkeypatch.setenv("OPENROUTER_API_URL", API_URL)
    reset_settings()
    summarizer._summarizer = None

    captured: dict[str, object] = {}

    class DummyResponse:
        status_code = 200

        def json(self) -> dict:
            return {
                "choices": [
                    {"message": {"content": "Morning briefing summary."}},
                ]
            }

        def raise_for_status(self) -> None:
            return None

    def fake_post(url: str, json: dict, headers: dict, timeout: int) -> DummyResponse:
        captured["url"] = url
        captured["json"] = json
        captured["headers"] = headers
        captured["timeout"] = timeout
        return DummyResponse()

    fake_requests = types.SimpleNamespace()
    fake_requests.post = fake_post  # type: ignore[attr-defined]
    fake_requests.HTTPError = DummyHTTPError
    fake_requests.RequestException = DummyRequestException
    monkeypatch.setattr(summarizer, "requests", fake_requests)

    summary_fn = summarizer.get_summarizer()
    result = summary_fn("text", "- bullet")

    assert result == "Morning briefing summary."
    assert captured["url"] == API_URL
    assert captured["json"]["model"] == MODEL_NAME
    assert captured["json"]["messages"][0]["role"] == "system"
    assert captured["headers"]["Authorization"] == "Bearer secret-token"
    assert captured["timeout"] == 20

    summarizer._summarizer = None
