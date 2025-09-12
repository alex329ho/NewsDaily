from dailynews import summarizer


def test_summarize_empty_returns_message():
    assert summarizer.summarize_articles([]) == "No news available."


def test_summarize_basic_text_contains_keywords(monkeypatch):
    def fake_sum(text, **kwargs):
        return [{"summary_text": text[:50]}]

    monkeypatch.setattr(summarizer, "summarizer", fake_sum)
    articles = [{"title": "Economy", "desc": "The economy is booming"}]
    result = summarizer.summarize_articles(articles)
    assert "economy" in result.lower()
