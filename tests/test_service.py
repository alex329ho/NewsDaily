from dailynews import service


def test_summarize_run(monkeypatch):
    def fake_fetch(topics, hours, region=None, language=None, maxrecords=75):
        assert topics == ["finance"]
        assert hours == 8
        assert region == "US"
        assert language == "en"
        return [
            {
                "title": "Title",
                "url": "http://example.com",
                "source_domain": "example.com",
                "seendate": "2023-01-01T00:00:00",
                "desc": "desc",
            }
        ]

    def fake_summary(articles):
        return "summary"

    monkeypatch.setattr(service, "fetch_news", fake_fetch)
    monkeypatch.setattr(service, "summarize_articles", fake_summary)

    result = service.summarize_run(["finance"], 8, region="US", language="en")
    assert result["fetched_count"] == 1
    assert result["summary"] == "summary"
    assert result["headlines"][0]["title"] == "Title"
