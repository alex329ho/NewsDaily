import sys
import types

import pytest

from dailynews import summarizer
from dailynews.config import reset_settings


MODEL_NAME = "HuggingFaceTB/SmolLM2-1.7B-Instruct"
MODEL_URL = "https://huggingface.co/HuggingFaceTB/SmolLM2-1.7B-Instruct?library=transformers"


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
    monkeypatch.setenv("DAILYNEWS_SKIP_HF", "1")
    summarizer._summarizer = None
    summary_fn = summarizer.get_summarizer()
    result = summary_fn("text", "- bullet")
    assert "DAILYNEWS_SKIP_HF" in result


def test_get_summarizer_raises_for_missing_backend(monkeypatch):
    monkeypatch.delenv("DAILYNEWS_SKIP_HF", raising=False)
    monkeypatch.setenv("HF_API_TOKEN", "token")
    monkeypatch.setenv("HF_MODEL", MODEL_NAME)
    reset_settings()
    summarizer._summarizer = None

    fake_transformers = types.ModuleType("transformers")
    fake_utils = types.ModuleType("transformers.utils")
    fake_utils.is_torch_available = lambda: False
    fake_utils.is_tf_available = lambda: False
    fake_utils.is_flax_available = lambda: False

    def _unexpected_pipeline(*_: object, **__: object) -> None:
        raise AssertionError("pipeline should not run without a backend")

    fake_transformers.utils = fake_utils  # type: ignore[attr-defined]
    fake_transformers.pipeline = _unexpected_pipeline  # type: ignore[attr-defined]

    monkeypatch.setitem(sys.modules, "transformers", fake_transformers)
    monkeypatch.setitem(sys.modules, "transformers.utils", fake_utils)

    with pytest.raises(RuntimeError) as excinfo:
        summarizer.get_summarizer()

    assert "PyTorch" in str(excinfo.value)


def test_get_summarizer_auth_error_mentions_access_link(monkeypatch):
    monkeypatch.delenv("DAILYNEWS_SKIP_HF", raising=False)
    monkeypatch.setenv("HF_API_TOKEN", "token")
    monkeypatch.setenv("HF_MODEL", MODEL_NAME)
    reset_settings()
    summarizer._summarizer = None

    fake_transformers = types.ModuleType("transformers")
    fake_utils = types.ModuleType("transformers.utils")
    fake_utils.is_torch_available = lambda: True
    fake_utils.is_tf_available = lambda: False
    fake_utils.is_flax_available = lambda: False

    class DummyResponse:
        status_code = 401

    class DummyError(Exception):
        def __init__(self) -> None:
            super().__init__(
                f"401 Client Error. Access to model {MODEL_NAME} is restricted."
            )
            self.response = DummyResponse()

    def fake_pipeline(*_, **__):
        raise DummyError()

    fake_transformers.utils = fake_utils  # type: ignore[attr-defined]
    fake_transformers.pipeline = fake_pipeline  # type: ignore[attr-defined]

    monkeypatch.setitem(sys.modules, "transformers", fake_transformers)
    monkeypatch.setitem(sys.modules, "transformers.utils", fake_utils)

    with pytest.raises(RuntimeError) as excinfo:
        summarizer.get_summarizer()

    message = str(excinfo.value)
    assert MODEL_NAME in message
    assert MODEL_URL in message


def test_get_summarizer_prefers_token_kwarg(monkeypatch):
    monkeypatch.delenv("DAILYNEWS_SKIP_HF", raising=False)
    monkeypatch.setenv("HF_API_TOKEN", "secret-token")
    monkeypatch.setenv("HF_MODEL", MODEL_NAME)
    reset_settings()
    summarizer._summarizer = None

    fake_transformers = types.ModuleType("transformers")
    fake_utils = types.ModuleType("transformers.utils")
    fake_utils.is_torch_available = lambda: True
    fake_utils.is_tf_available = lambda: False
    fake_utils.is_flax_available = lambda: False

    captured: dict[str, object] = {}

    class DummyPipeline:
        def __call__(self, *_: object, **__: object) -> list[dict[str, str]]:
            return [{"summary_text": "ok"}]

    def fake_pipeline(task: str, model: str, **kwargs: object) -> DummyPipeline:
        captured["task"] = task
        captured["model"] = model
        captured["kwargs"] = kwargs
        return DummyPipeline()

    fake_transformers.utils = fake_utils  # type: ignore[attr-defined]
    fake_transformers.pipeline = fake_pipeline  # type: ignore[attr-defined]

    monkeypatch.setitem(sys.modules, "transformers", fake_transformers)
    monkeypatch.setitem(sys.modules, "transformers.utils", fake_utils)

    summary_fn = summarizer.get_summarizer()
    summary_fn("text", "- bullet")

    assert captured["task"] == "summarization"
    assert captured["model"] == MODEL_NAME
    assert captured["kwargs"].get("token") == "secret-token"
    assert "use_auth_token" not in captured["kwargs"]

    summarizer._summarizer = None
