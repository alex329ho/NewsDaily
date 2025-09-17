from dailynews import summarizer


def test_summarize_empty_returns_message():
    assert summarizer.summarize_articles([]) == "No news available."


def test_summarize_basic_text_contains_keywords(monkeypatch):
    def fake_sum(text: str, bullet_text: str) -> str:
        assert "Economy" in text
        return "Summary about economy"

    monkeypatch.setattr(summarizer, "get_summarizer", lambda: fake_sum)
    articles = [{"title": "Economy", "desc": "The economy is booming"}]
    result = summarizer.summarize_articles(articles)
    assert "economy" in result.lower()


def test_summarize_by_topic(monkeypatch):
    def fake_sum(text: str, bullet_text: str) -> str:
        return "summary"

    monkeypatch.setattr(summarizer, "get_summarizer", lambda: fake_sum)
    articles = [
        {"title": "Economy today", "desc": "great"},
        {"title": "Politics", "desc": "meh"},
    ]
    result = summarizer.summarize_by_topic(["economy", "politics"], articles)
    assert set(result) == {"economy", "politics"}


def test_stub_used_when_skip_env(monkeypatch):
    monkeypatch.setenv("DAILYNEWS_SKIP_HF", "1")
    summarizer._summarizer = None
    summary_fn = summarizer.get_summarizer()
    result = summary_fn("text", "- bullet")
    assert "DAILYNEWS_SKIP_HF" in result
