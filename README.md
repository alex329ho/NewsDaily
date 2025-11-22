# DailyNews

DailyNews fetches recent headlines from the [GDELT](https://www.gdeltproject.org/) API,
summarises them with the OpenRouter `x-ai/grok-4.1-fast` model, exposes a FastAPI
backend for mobile clients, and optionally emails the summary to you.
> **Requires Python 3.10+** for structural pattern matching and typing features used
> across the CLI, API service, and tests.

## Features

- Click-based CLI with optional backend integration (`--use-api`).
- FastAPI service exposing `/health` and `/summary` endpoints with CORS enabled
  for local development tooling and mobile simulators.
- Configurable OpenRouter model via `OPENROUTER_MODEL` and `OPENROUTER_API_KEY`
  environment variables with an offline testing stub (`DAILYNEWS_SKIP_SUMMARY=1`).
- Mobile clients:
  - Flutter application with topic chips, configurable filters, and tappable
    headlines.
  - React Native (Expo) application with multi-select topics and rich status
    handling.
- Email delivery using SMTP environment variables.

## Quick start

```bash
python3.10 -m venv .venv && source .venv/bin/activate
pip install -U pip
pip install -e .
```

Create a `.env` file (or export the variables in your shell) using
[`examples/.env.example`](examples/.env.example) as a template. At minimum set:

```bash
export OPENROUTER_API_KEY="<your OpenRouter token>"
export OPENROUTER_MODEL="x-ai/grok-4.1-fast"
export OPENROUTER_API_URL="https://openrouter.ai/x-ai/grok-4.1-fast/api"
export API_PORT=8000
# Optional: change if your backend runs elsewhere
export DAILYNEWS_API_URL="http://localhost:8000"
```

Never commit tokens to the repository—see [SECURITY.md](SECURITY.md).

> **Note:** DailyNews uses the OpenRouter chat-completions interface to call
> `x-ai/grok-4.1-fast` with a summarisation instruction. Set
> `DAILYNEWS_SKIP_SUMMARY=1` to bypass remote calls during offline testing.

### Run the backend API

```bash
# Requires the virtual environment above
uvicorn server.main:app --reload --port "${API_PORT:-8000}"
# or use the helper script
./scripts/run_server.sh
```

The API will be reachable at `http://localhost:${API_PORT}/summary`.

### Use the CLI

```bash
# See available options (note the new --use-api flag)
dailynews --help

# Fetch finance/economy/politics locally (no API)
dailynews -t "finance,economy,politics" -h 8

# Use the backend API instead of local summarisation
dailynews --use-api -t finance -h 4

# Include region and language filters
dailynews -t finance -r US -l en -h 24
```

When running tests or developing offline, disable the OpenRouter calls:

```bash
export DAILYNEWS_SKIP_SUMMARY=1
pytest -q
```

### Email summaries

Copy the sample file, fill in the SMTP settings, then source it before running
with `-e`:

```bash
cp examples/.env.example .env
# edit .env to add EMAIL_* settings
source .env
dailynews -e you@example.com
```

## Mobile clients

Both mobile apps expect the backend to be running. Adjust the base URL to point
at your machine from the simulator/emulator.

### Flutter (`mobile/flutter_app`)

1. Install Flutter 3.0+.
2. From `mobile/flutter_app`, run `flutter pub get`.
3. Launch the backend API and ensure it is accessible.
4. Start the app:

   ```bash
   flutter run --dart-define=DAILYNEWS_API_BASE="http://localhost:8000"
   ```

   - Android emulator: use `http://10.0.2.2:8000`.
   - iOS simulator: `http://127.0.0.1:8000`.
   - Physical device: replace with your machine's LAN IP.

See [`mobile/flutter_app/README.md`](mobile/flutter_app/README.md) for more
platform-specific notes.

### React Native / Expo (`mobile/react_native_app`)

1. Install Node.js 18+ and Expo CLI (`npm install -g expo-cli`).
2. From `mobile/react_native_app`, run `npm install`.
3. Copy `.env.example` to `.env` or export `EXPO_PUBLIC_BASE_URL`.
4. Start Expo:

   ```bash
   npm run start
   # then press a/i/w for Android/iOS/web respectively
   ```

   - Android emulator default: `http://10.0.2.2:8000`.
   - iOS simulator: `http://127.0.0.1:8000`.
   - Physical devices must share the same network as your machine.

Refer to [`mobile/react_native_app/README.md`](mobile/react_native_app/README.md)
for troubleshooting tips and network configuration guidance.

## Testing

```bash
export DAILYNEWS_SKIP_SUMMARY=1
pytest -q
```

All external network calls are monkeypatched in tests, ensuring deterministic
and offline-friendly behaviour.

## Troubleshooting

- `Backend API returned invalid JSON` – ensure the FastAPI server is running
  and reachable.
- `OPENROUTER_API_KEY must be set` – the CLI/backend attempted to call the
  OpenRouter API without credentials.
- `Access to the OpenRouter model ... is restricted` – confirm your token can
  reach `https://openrouter.ai/x-ai/grok-4.1-fast/api`.
- Mobile devices cannot reach the backend – confirm the correct base URL for
  your simulator/emulator and that the host firewall allows local connections.
- Summaries look stale – reduce the `--hours` window or adjust topics.

## Scheduling

Use `scripts/cron_example.sh` as a template for cron jobs that activate your
virtual environment before calling the CLI.

## Security

Environment variables contain all sensitive material (OpenRouter tokens,
SMTP credentials). Rotate tokens immediately if exposed and review
[SECURITY.md](SECURITY.md) for recommended practices.
