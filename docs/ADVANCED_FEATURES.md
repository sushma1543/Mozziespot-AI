# Advanced Feature Specification

## Module 1: Real Satellite Images

- Sentinel-2 scene search is implemented through STAC APIs.
- Primary source: Copernicus Data Space STAC endpoint configured by `COPERNICUS_STAC_URL`.
- Fallback source: AWS Earth Search configured by `AWS_SENTINEL_STAC_URL`.
- Automatic date selection searches the latest 90 days when the user does not provide dates.
- AOI selection accepts either a bbox or a latitude/longitude point with padding.
- Full band download is optional because Sentinel-2 bands are large. Enable it with `MOZZIESPOT_REAL_DOWNLOAD=1`.
- `POST /api/satellite/process` runs the raster pipeline after all required bands are present.
- Generated products are served through `/api/satellite/output/<scene_id>/<filename>`.
- Default Docker mode is manifest-only (`MOZZIESPOT_REAL_DOWNLOAD=0`); this does not mean the STAC metadata is fake. It means the large band assets are not fetched until enabled.

## Module 2: Image Processing

Implemented modules:

- QA60 cloud masking.
- SCL scene-classification masking.
- Band extraction for B02, B03, B04, B08, B11, B12, QA60, and SCL.
- NDWI: `(B03 - B08) / (B03 + B08)`.
- MNDWI: `(B03 - B11) / (B03 + B11)`.
- NDVI: `(B08 - B04) / (B08 + B04)`.
- The raster pipeline aligns 10 m and 20 m source grids to a common reference grid before calculating indices.
- QA60 cloud/cirrus bits 10 and 11 are removed, and SCL clear classes 4, 5, and 6 are retained.
- The threshold water mask uses NDWI >= 0.30 after cloud masking and is vectorised into probable waterbody GeoJSON features.

## Module 3: Deep Learning

Implemented model-ready files:

- U-Net: `backend/app/ai/unet.py`.
- DeepLabV3+ Lite: `backend/app/ai/deeplabv3plus.py`.
- SegFormer Lite: `backend/app/ai/segformer.py`.
- Ensemble fusion: `backend/app/ai/ensemble.py`.

These files are ready for training/inference when PyTorch and model weights are added. The dashboard remains runnable without GPU dependencies. The default waterbody raster workflow is image-processing based; it does not pretend that untrained deep-learning models are producing the displayed risk dots.

## Module 4: Water Analysis

The advanced service classifies water evidence as:

- Permanent lake.
- Temporary waterbody.
- Flood water.
- Stagnant water.
- Construction pit or artificial pond.
- Drainage blockage.
- Monitoring water trace.

## Module 5: Risk Assessment

Mosquito Risk Score uses a 0-100 scale:

- 0-20: Very Low.
- 20-40: Low.
- 40-60: Moderate.
- 60-80: High.
- 80-100: Severe.

Factors:

- Water persistence.
- NDWI.
- Rainfall.
- Temperature.
- Humidity.
- Vegetation.
- Nearby population.
- Previous outbreak indicator.

## Module 6: Disease Prediction

The system estimates environmental suitability for:

- Dengue.
- Malaria.
- Chikungunya.
- Japanese Encephalitis.

These are risk suitability scores, not clinical case predictions.

## Module 7: GIS Dashboard

Implemented:

- OpenStreetMap layer.
- Satellite imagery layer.
- Risk dots.
- Heat rings around probable breeding/mosquito activity zones.
- Search by state, district, village, town, and coordinates.
- Live walking location marker.
- Sidebar buttons navigate to the corresponding dashboard sections.
- Selecting a waterbody opens a satellite preview centered on its coordinates.

Official village, mandal, and district boundary GeoJSON files can be added to the map layer service for production deployment.

## Module 8: Analytics Dashboard

Implemented:

- Total water bodies.
- Total stagnant water.
- High-risk villages.
- Severe zones.
- Disease trend.
- Monthly water trend.
- Priority list.

## Module 9: Alerts

Implemented:

- WhatsApp authority message.
- Telegram Bot API send when credentials are configured.
- Telegram share link fallback.
- Email/SMTP send when credentials are configured.
- Daily and weekly PDF report endpoints.

## Module 10: Export

Implemented endpoints:

- CSV: `/api/export/csv`.
- Excel: `/api/export/excel`.
- PDF: `/api/reports/weekly` and `/api/reports/daily`.
- GeoJSON: `/api/export/geojson`.
- Shapefile zip: `/api/export/shapefile`.

## Module 11: AI Explainability

Each selected point shows factor contributions:

- Water persistence.
- NDWI.
- Rainfall.
- Temperature.
- Humidity.
- Vegetation.
- Population density.
- Previous outbreaks.

## Module 12: Admin Panel Foundation

Implemented role definitions:

- Admin.
- Health Officer.
- Municipality.
- Panchayat.

Demo login:

- Email: `officer@mozziespot.ai`.
- Password: `demo123`.

## Real-Time Scope

Live behavior currently includes the dashboard clock, browser GPS watch, nearby-risk API refresh, manual map refresh, and on-demand satellite scene search. Continuous WebSocket streaming, scheduled satellite ingestion, live weather polling, PostGIS persistence, and automatic daily jobs are production extensions rather than current defaults.
