# Advanced API Reference

Base URL: `/api`

## Satellite

`POST /satellite/search`

Searches Copernicus STAC first and AWS Earth Search second.

```json
{
  "bbox": [80.52, 16.25, 80.72, 16.45],
  "start_date": "2026-04-01",
  "end_date": "2026-07-19",
  "cloud_cover": 15
}
```

`GET or POST /satellite/download`

Creates a Sentinel-2 scene manifest and optionally downloads required bands. Full band download requires `MOZZIESPOT_REAL_DOWNLOAD=1`.

`POST /satellite/process`

Runs the satellite processing service. It returns `mode: manifest` when required bands are unavailable and `mode: raster` after real bands are processed. Raster mode returns output paths and browser download URLs for RGB, NDWI, MNDWI, NDVI, water mask, and probable waterbody GeoJSON.

Example request:

```json
{
  "latitude": 16.5062,
  "longitude": 80.648,
  "padding": 0.03,
  "cloud_cover": 20
}
```

`GET /satellite/output/<scene_id>/<filename>`

Serves only generated files with these names: `rgb_preview.png`, `rgb_preview.tif`, `ndwi.tif`, `mndwi.tif`, `ndvi.tif`, `water_mask.tif`, and `probable_waterbodies.geojson`.

`GET /satellite/layers`

Returns GIS layer metadata.

## Risk and Analytics

`GET /state-risk`

Query parameters:

- `state`
- `district`
- `village`
- `q`
- `minimum`

`POST /analyze/spot`

```json
{
  "latitude": 16.5062,
  "longitude": 80.648,
  "name": "Vijayawada"
}
```

`GET /analytics`

Returns totals, stagnant water count, high-risk villages, disease trend, monthly trend, and top priority locations.

## Alerts

`POST /alerts/send`

```json
{
  "detection": {},
  "whatsapp_number": "919999999999",
  "email": "officer@example.gov"
}
```

Response includes:

- Telegram status.
- WhatsApp URL.
- Telegram share URL.
- Message text.

Telegram bot delivery requires both `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID`. Without them, the frontend opens a Telegram share link for manual sending.

## Exports

- `GET /export/csv`
- `GET /export/excel`
- `GET /export/geojson`
- `GET /export/shapefile`
- `GET /reports/daily`
- `GET /reports/weekly`

## Admin

`POST /auth/login`

Demo:

```json
{
  "email": "officer@mozziespot.ai",
  "password": "demo123"
}
```

`GET /admin/roles`

Returns Admin, Health Officer, Municipality, and Panchayat role definitions.
