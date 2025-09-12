import requests
from dailynews import fetcher


def test_fetch_news_monkeypatch(monkeypatch):
    class DummyResp:
        def raise_for_status(self):
            pass

        def json(self):
            return {
                "articles": [
                    {
                        "title": "Title",
                        "url": "http://example.com",
                        "description": "Description",
                        "seendate": "202304071230",
                    }
                ]
            }

    def fake_get(*args, **kwargs):
        return DummyResp()

    monkeypatch.setattr(fetcher.requests, "get", fake_get)
    articles = fetcher.fetch_news(["test"], 8)
    assert len(articles) == 1
    art = articles[0]
    assert art["title"] == "Title"
    assert art["url"] == "http://example.com"
    assert art["desc"] == "Description"
    assert art["source_domain"] == "example.com"
    assert art["seendate"].startswith("2023-04-07")


def test_fetch_news_handles_error(monkeypatch):
    def fake_get(*args, **kwargs):
        raise requests.exceptions.ConnectionError("no connection")

    monkeypatch.setattr(fetcher.requests, "get", fake_get)
    articles = fetcher.fetch_news(["test"], 8)
    assert articles == []


def test_fetch_news_region_language(monkeypatch):
    captured = {}

    class DummyResp:
        def raise_for_status(self):
            pass

        def json(self):  # no articles needed
            return {"articles": []}

    def fake_get(url, params=None, timeout=10):
        captured["query"] = params.get("query")
        return DummyResp()

    monkeypatch.setattr(fetcher.requests, "get", fake_get)
    fetcher.fetch_news(["finance"], 8, region="US", language="en")
    assert "sourceCountry:US" in captured["query"]
    assert "sourceLang:en" in captured["query"]
