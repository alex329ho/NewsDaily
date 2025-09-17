import pytest

pytest.importorskip("httpx")

from fastapi.testclient import TestClient

from server.main import app


def test_health_endpoint():
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_summary_endpoint(monkeypatch):
    client = TestClient(app)

    def fake_run(topics, hours, region=None, language=None, maxrecords=75):
        assert topics == ["finance", "economy"]
        assert hours == 8
        assert region == "US"
        assert language == "en"
        return {
            "topics": topics,
            "hours": hours,
            "region": region,
            "language": language,
            "fetched_count": 1,
            "summary": "summary",
            "headlines": [
                {
                    "title": "Title",
                    "url": "http://example.com",
                    "source_domain": "example.com",
                    "seendate": "2023-01-01T00:00:00",
                }
            ],
        }

    monkeypatch.setattr("server.main.summarize_run", fake_run)

    response = client.get(
        "/summary",
        params={
            "topics": "finance,economy",
            "hours": 8,
            "region": "US",
            "language": "en",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["summary"] == "summary"
    assert data["topics"] == ["finance", "economy"]
