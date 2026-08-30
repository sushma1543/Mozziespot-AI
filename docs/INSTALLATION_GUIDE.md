# Installation Guide

## Docker Run

From the project root:

```powershell
docker compose down
docker compose up --build --force-recreate
```

Open:

- Frontend: `http://localhost:5173`
- Backend health: `http://localhost:8000/api/health`

## Local Backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
uvicorn fastapi_run:app --host 0.0.0.0 --port 8000
```

## Local Frontend

```powershell
cd frontend
npm install
npm run dev
```

## Telegram Setup

1. Create a Telegram bot using BotFather.
2. Copy the bot token into `TELEGRAM_BOT_TOKEN`.
3. Add the bot to your authority group/chat.
4. Put the chat id into `TELEGRAM_CHAT_ID`.
5. Restart Docker.

## Email Setup

Set:

```text
SMTP_HOST=
SMTP_PORT=587
SMTP_USER=
SMTP_PASSWORD=
ALERT_FROM_EMAIL=alerts@mozziespot.ai
```

## Real Sentinel-2 Download

By default, the app searches real STAC catalogs and writes a scene manifest. Full Sentinel-2 band download is disabled because files are large. This default keeps the classroom demo fast and avoids unexpected downloads.

Enable full download:

```text
MOZZIESPOT_REAL_DOWNLOAD=1
```

Then restart:

```powershell
docker compose down
docker compose up --build --force-recreate
```

In the dashboard, use `Search Latest Scene`, then `Download Sentinel-2`, and finally `Run AI Processing`. When all required bands are available, the result is returned with `mode: raster` and produces an RGB PNG preview, RGB GeoTIFF, NDWI, MNDWI, NDVI, water mask, and probable-waterbodies GeoJSON. If bands are not downloaded, the result is `mode: manifest` and lists the missing bands.

Generated files are kept in the Docker volume `satellite-data` and are available through the dashboard download buttons or `/api/satellite/output/<scene_id>/<filename>`.

## Verify The Installation

Open these URLs after the containers start:

```text
http://localhost:5173
http://localhost:8000/api/health
```

The dashboard status should show map data instead of `Backend unavailable`. If the frontend still looks old, run the no-cache rebuild above and press `Ctrl + Shift + R` in the browser.

## Important Notes

- The app estimates probable mosquito breeding habitat risk.
- It does not directly detect mosquito eggs or adult mosquitoes.
- Official production deployment should add trained model weights, PostGIS, official administrative boundaries, and field validation.
- The current project does not claim direct detection of mosquito eggs, adult mosquitoes, or confirmed disease cases.
