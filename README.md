# DailyNews

DailyNews fetches recent headlines from the [GDELT](https://www.gdeltproject.org/) API,
summarises them with a Hugging Face model, exposes a FastAPI backend for mobile
clients, and optionally emails the summary to you.

## Features

- Click-based CLI with optional backend integration (`--use-api`).
- FastAPI service exposing `/health` and `/summary` endpoints with CORS enabled
  for local development tooling and mobile simulators.
- Configurable Hugging Face model via `HF_MODEL` and `HF_API_TOKEN` environment
  variables with an offline testing stub (`DAILYNEWS_SKIP_HF=1`).
- Mobile clients:
  - Flutter application with topic chips, configurable filters, and tappable
    headlines.
  - React Native (Expo) application with multi-select topics and rich status
    handling.
- Email delivery using SMTP environment variables.

## Quick start

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -U pip
pip install -e .
```

Create a `.env` file (or export the variables in your shell) using
[`examples/.env.example`](examples/.env.example) as a template. At minimum set:

```bash
export HF_API_TOKEN="<your HF token>"
export HF_MODEL="HuggingFaceTB/SmolLM2-1.7B-Instruct"
export API_PORT=8000
# Optional: change if your backend runs elsewhere
export DAILYNEWS_API_URL="http://localhost:8000"
```

Never commit tokens to the repository—see [SECURITY.md](SECURITY.md).

> **Note:** `HuggingFaceTB/SmolLM2-1.7B-Instruct` is an instruction-tuned text
> generation model. DailyNews applies a summarisation prompt using the
> Transformers text-generation pipeline. Ensure your `HF_API_TOKEN` grants
> access to the model at
> <https://huggingface.co/HuggingFaceTB/SmolLM2-1.7B-Instruct?library=transformers>,
> and install a deep-learning backend (e.g. `pip install torch`) or enable
> `DAILYNEWS_SKIP_HF=1` for offline tests.

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

When running tests or developing offline, disable the Hugging Face model:

```bash
export DAILYNEWS_SKIP_HF=1
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
export DAILYNEWS_SKIP_HF=1
pytest -q
```

All external network calls are monkeypatched in tests, ensuring deterministic
and offline-friendly behaviour.

## Troubleshooting

- `Backend API returned invalid JSON` – ensure the FastAPI server is running
  and reachable.
- `HF_MODEL and HF_API_TOKEN must be set` – the CLI/backend attempted to load a
  model without credentials.
- `Access to the Hugging Face model ... is restricted` – confirm your token can
  reach the configured model at
  <https://huggingface.co/HuggingFaceTB/SmolLM2-1.7B-Instruct?library=transformers>.
- `Cannot load Hugging Face model ... because no deep learning backend is available`
  – install PyTorch/TensorFlow/Flax so Transformers can execute, or enable
  `DAILYNEWS_SKIP_HF=1` for offline use.
- Mobile devices cannot reach the backend – confirm the correct base URL for
  your simulator/emulator and that the host firewall allows local connections.
- Summaries look stale – reduce the `--hours` window or adjust topics.

## Scheduling

Use `scripts/cron_example.sh` as a template for cron jobs that activate your
virtual environment before calling the CLI.

## Security

Environment variables contain all sensitive material (Hugging Face tokens,
SMTP credentials). Rotate tokens immediately if exposed and review
[SECURITY.md](SECURITY.md) for recommended practices.
