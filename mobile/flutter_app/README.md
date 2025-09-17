# DailyNews Flutter App

A lightweight Flutter client that talks to the DailyNews FastAPI backend.

## Prerequisites

- Flutter SDK 3.0+
- Backend running locally (see repository README)

## Getting started

```bash
flutter pub get
flutter run --dart-define=DAILYNEWS_API_BASE="http://localhost:8000"
```

If you are running on an emulator/device update the base URL:

- Android emulator: `--dart-define=DAILYNEWS_API_BASE="http://10.0.2.2:8000"`
- iOS simulator: `--dart-define=DAILYNEWS_API_BASE="http://127.0.0.1:8000"`
- Physical device: use your machine's LAN IP (ensure both devices share a
  network).

## Features

- Topic chips for finance, economy, and politics plus a custom topic input
- Hours dropdown (4/8/12/24) and optional region/language filters
- Loading, error, and empty states
- Scrollable summary with tappable headlines

## Troubleshooting

- `Backend returned XXX` – verify the API server is reachable from the device.
- Nothing happens on tap – confirm the device/emulator has a default browser and
  permissions to open external URLs.
