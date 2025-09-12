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


def test_summarize_by_topic_produces_summaries(monkeypatch):
    """Each topic should map to a summary or a default message."""

    def fake_sum(text, **kwargs):
        if "sports" in text.lower():
            return [{"summary_text": ""}]
        return [{"summary_text": text[:50]}]

    monkeypatch.setattr(summarizer, "summarizer", fake_sum)

    topics = ["economy", "sports"]
    articles = [
        {"title": "Economy on the rise", "desc": "GDP grows 3% this quarter"},
        {
            "title": "Local sports team wins",
            "desc": "Sports fans celebrate victory",
        },
    ]

    summaries = summarizer.summarize_by_topic(topics, articles)
    assert set(summaries) == set(topics)
    for topic in topics:
        summary = summaries[topic]
        assert summary == "No news available." or summary
