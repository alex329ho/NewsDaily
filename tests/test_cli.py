from click.testing import CliRunner

from dailynews import cli


def test_cli_local_flow(monkeypatch):
    runner = CliRunner()
    called = {}

    def fake_service(topics, hours, region=None, language=None, maxrecords=75):
        called["topics"] = topics
        called["region"] = region
        called["language"] = language
        return {
            "topics": topics,
            "hours": hours,
            "region": region,
            "language": language,
            "fetched_count": 2,
            "summary": "Summary",
            "headlines": [
                {"title": "Title1", "url": "http://example.com/1", "source_domain": "example.com", "seendate": ""},
                {"title": "Title2", "url": "http://example.com/2", "source_domain": "example.com", "seendate": ""},
            ],
        }

    monkeypatch.setattr(cli, "summarize_run", fake_service)

    result = runner.invoke(cli.main, ["-t", "finance", "-r", "US", "-l", "en"])
    assert result.exit_code == 0
    assert called["topics"] == ["finance"]
    assert called["region"] == "US"
    assert called["language"] == "en"
    assert "Summary" in result.output


def test_cli_use_api(monkeypatch):
    runner = CliRunner()

    class DummyResp:
        def raise_for_status(self):
            pass

        def json(self):
            return {
                "topics": ["finance"],
                "hours": 4,
                "region": None,
                "language": None,
                "fetched_count": 1,
                "summary": "API Summary",
                "headlines": [
                    {"title": "Title", "url": "http://example.com", "source_domain": "example.com", "seendate": ""}
                ],
            }

    def fake_get(url, params=None, timeout=20):
        assert "/summary" in url
        return DummyResp()

    monkeypatch.setattr(cli.requests, "get", fake_get)

    result = runner.invoke(cli.main, ["--use-api", "-t", "finance", "-h", "4"])
    assert result.exit_code == 0
    assert "API Summary" in result.output


def test_cli_handles_no_articles(monkeypatch):
    runner = CliRunner()

    def fake_service(topics, hours, region=None, language=None, maxrecords=75):
        return {
            "topics": topics,
            "hours": hours,
            "region": region,
            "language": language,
            "fetched_count": 0,
            "summary": "No news available.",
            "headlines": [],
        }

    monkeypatch.setattr(cli, "summarize_run", fake_service)
    result = runner.invoke(cli.main, [])
    assert result.exit_code == 0
    assert "No articles found" in result.output


def test_cli_rejects_old_python(monkeypatch):
    runner = CliRunner()

    class DummySys:
        version_info = (3, 9, 0)

    monkeypatch.setattr(cli, "sys", DummySys())
    result = runner.invoke(cli.main, [])
    assert result.exit_code != 0
    assert "Python 3.10+ is required" in result.output
