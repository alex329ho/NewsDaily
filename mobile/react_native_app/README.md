# DailyNews React Native App

Expo-based mobile client that consumes the DailyNews backend API.

## Prerequisites

- Node.js 18+
- Expo CLI (`npm install -g expo-cli`)
- Backend API running locally or on your network

## Getting started

```bash
cp .env.example .env # optional, or export EXPO_PUBLIC_BASE_URL
npm install
npm run start
```

Use the Expo CLI prompts to launch on Android (`a`), iOS (`i`), or web (`w`).

### Base URL tips

- Android emulator: `EXPO_PUBLIC_BASE_URL=http://10.0.2.2:8000`
- iOS simulator: `EXPO_PUBLIC_BASE_URL=http://127.0.0.1:8000`
- Physical device: replace with your machine's LAN IP and ensure both devices are
  on the same network.

## Features

- Toggleable topic chips plus custom topic entry
- Hour presets (4/8/12/24) and optional region/language inputs
- Loading, error, and empty states for robust UX
- Headlines list opens URLs using the native browser

## Troubleshooting

- `Backend returned 404/500` – confirm the FastAPI server is running and
  accessible from the device.
- Expo tunnel/firewall issues – try switching to LAN mode in Expo (`s` key) and
  ensure the port is accessible.
