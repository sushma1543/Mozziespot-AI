# API Reference

Base URL: `/api`

## Health

`GET /health`

Returns service status.

## Dashboard

`GET /dashboard`

Returns operational metrics.

## Detections

`GET /detections`

Returns scored habitat detections with explainability and disease suitability values.

## Analyze

`POST /analyze`

Demo endpoint for running a synthetic analysis. In production, send a scene id or raster files.

## Alerts

`POST /alerts/send`

Body:

```json
{
  "detection": {},
  "email": "health-officer@example.gov"
}
```

## Reports

`GET /reports/weekly`

Downloads a PDF summary report.

`GET /reports/daily`

Downloads a daily PDF summary report.

## Satellite

`POST /satellite/search`

Searches Sentinel-2 scenes through Copernicus Data Space STAC and AWS Earth Search fallback.

`GET /satellite/download`

Creates a Sentinel-2 scene manifest. Full download is optional through `MOZZIESPOT_REAL_DOWNLOAD=1`.

`POST /satellite/process`

Returns RGB, NDWI, MNDWI, NDVI, and water-mask output paths.

## Analytics

`GET /analytics`

Returns total water bodies, stagnant water, high-risk villages, severe zones, disease trend, and monthly trend.

## Exports

- `GET /export/csv`
- `GET /export/excel`
- `GET /export/geojson`
- `GET /export/shapefile`
