from click.testing import CliRunner

from dailynews import cli, summarizer


def test_cli_basic(monkeypatch):
    runner = CliRunner()

    def fake_fetch(topics, hours, maxrecords=75):
        return [
            {"title": "Title1", "url": "http://example.com/1", "desc": "Desc"},
            {"title": "Title2", "url": "http://example.com/2", "desc": "Desc"},
        ]

    monkeypatch.setattr(cli, "fetch_news", fake_fetch)
    monkeypatch.setattr(summarizer, "summarizer", lambda text, **kw: [{"summary_text": "Summary"}])

    result = runner.invoke(cli.main, ["-t", "finance", "-h", "8"])
    assert result.exit_code == 0
    assert "DailyNews summary for finance (last 8h):" in result.output
    assert "Summary" in result.output


def test_cli_handles_no_articles(monkeypatch):
    runner = CliRunner()

    monkeypatch.setattr(cli, "fetch_news", lambda topics, hours, maxrecords=75: [])
    result = runner.invoke(cli.main, [])
    assert result.exit_code == 0
    assert "No articles found" in result.output
