# DailyNews

DailyNews fetches recent headlines from the [GDELT](https://www.gdeltproject.org/) API,
summarises them using a small transformer model and optionally emails the
summary to you.

## Quick start

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -U pip
pip install -e .

# See available options
dailynews --help

# Fetch finance, economy and politics news for the last 8 hours
dailynews -t "finance,economy,politics" -h 8

# Fetch US English finance news
# Specify region and language
dailynews -t finance -r US -l en -h 24
```

The first run may download the summarisation model which can take a minute.
Set ``DAILYNEWS_SKIP_HF=1`` to skip loading the model (useful for tests).

## Troubleshooting

- `ConnectionError`: check your internet connection.
- JSON shape changes: the GDELT API occasionally adds or removes fields.  The
  tool will log a warning and return no results.
- Token length warnings: summarisation input is truncated to ~1000 characters to
  avoid overflow.

## Scheduling on macOS

```bash
crontab -e
# Example line (adjust paths)
0 7 * * * /path/to/project/.venv/bin/dailynews -t "finance,economy,politics" -h 8 >> /path/to/project/dailynews.log 2>&1
```

An alternative is to use [`scripts/cron_example.sh`](scripts/cron_example.sh) to
activate the virtual environment before running the command.

## Optional email usage

```bash
cp examples/.env.example .env
# edit .env and export the variables
source .env
dailynews -e you@example.com
```

## Development

Run tests with:

```bash
export DAILYNEWS_SKIP_HF=1
pytest -q
```

Roadmap:

- Future mobile app (Kivy or small Flask API)
- Multi-language support
- Docker packaging
