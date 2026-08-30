# MozzieSpot AI Advanced

An M.Tech-level AI, Remote Sensing, GIS, and Public Health decision-support project for identifying high-probability mosquito breeding habitats from satellite-derived environmental indicators.

Important scientific note: the system does not claim to detect mosquito eggs directly. It detects stagnant-water habitat risk using water persistence, NDWI, population exposure, temperature, vegetation, and building proximity.

## Features

- FastAPI entrypoint with the existing Flask REST API mounted for stable compatibility
- React + TypeScript dashboard
- Sentinel-2 STAC search using Copernicus Data Space with AWS Earth Search fallback
- Optional full Sentinel band download using `MOZZIESPOT_REAL_DOWNLOAD=1`
- QA60/SCL cloud-mask modules and automatic B02/B03/B04/B08/B11/B12 band handling
- NDWI, MNDWI, NDVI spectral-index formulas
- U-Net, DeepLabV3+, SegFormer, and ensemble segmentation scaffolds
- Water classification: permanent lake, temporary water, flood water, stagnant water, artificial pond, construction pit, drainage blockage
- Mosquito Risk Score 0-100 with Very Low, Low, Moderate, High, and Severe categories
- Disease suitability for Dengue, Malaria, Chikungunya, and Japanese Encephalitis
- Analytics dashboard with waterbody totals, stagnant water, high-risk villages, monthly trends, and disease trends
- GIS dashboard with OpenStreetMap, satellite imagery layer, risk dots, search, coordinate prediction, and live walking location
- GIS-ready GeoJSON output
- Explainable AI reasons for every flagged location
- Alert center for WhatsApp, Telegram Bot API, and email/SMTP integration
- PDF, CSV, Excel, GeoJSON, and Shapefile export endpoints
- Admin role definitions for Panchayat, Health Officer, Municipality, and Admin dashboards
- Docker and docker-compose deployment
- Sample data for immediate demo

## Current Build Status

The current build is an advanced M.Tech-level AI-GIS decision-support prototype.
The following workflows are implemented and runnable:

- Sidebar navigation to State Risk, Water Bodies, Mosquito Risk, Alerts, and Tracking.
- Exact place search with state, district, village/ward, coordinates, and Google Maps links.
- Browser GPS tracking with nearby-risk refresh while walking.
- Sentinel-2 STAC search through Copernicus Data Space with AWS Earth Search fallback.
- Optional real Sentinel-2 band download and local raster processing.
- QA60 and SCL cloud masking, band alignment, RGB preview, NDWI, MNDWI, NDVI, water mask, and GeoJSON waterbody output.
- Downloadable processed products from the dashboard when raster processing completes.

The deep-learning files for U-Net, DeepLabV3+, and SegFormer are model-ready scaffolds. Trained weights and labelled field data are not included, so the default demo uses the deterministic spectral/risk engines. Disease values are environmental suitability scores, not confirmed clinical cases.

## Deep-Learning Readiness

The repository includes research-ready implementations of:

- U-Net for semantic water segmentation.
- A lightweight DeepLabV3+-style model with atrous spatial pyramid pooling.
- A lightweight SegFormer-style transformer model.
- Weighted ensemble fusion of probability masks produced by multiple segmentation models.

These models are training and evaluation scaffolds. They are not used for operational inference unless compatible labelled imagery and trained weight files are supplied. The live operational workflow uses Sentinel-2 spectral indices and deterministic environmental-risk rules, and it does not report unvalidated neural-network accuracy.

## Future Dataset Integration

When a suitable labelled dataset becomes available, the project can pair six-band Sentinel-2 image chips with binary water masks. The existing training pipeline supports augmentation, geographic event-level training/validation/test separation, BCE-Dice optimization, trained-weight export, and comparative evaluation of U-Net, lightweight DeepLabV3+-style, lightweight SegFormer-style, and ensemble outputs.

Available evaluation measures include precision, recall, specificity, accuracy, F1 score, intersection over union, Dice coefficient, ROC and precision-recall curves, expected calibration error, and Brier score. Performance values must be reported only after training and evaluation on documented ground-truth labels.

## Novelty and Contribution

The principal contribution of MozzieSpot AI is an integrated, extensible, and claim-aware decision-support framework that combines:

1. Sentinel-2 scene discovery and multispectral water analysis.
2. Operational spectral-index mapping that remains usable without trained models.
3. A modular pathway for comparing convolutional, atrous-convolution, transformer, and ensemble segmentation approaches when labelled data becomes available.
4. Environmental mosquito-risk scoring linked to mapped waterbody evidence.
5. Explainable factors, disease-suitability indicators, GIS visualization, location tracking, authority alerts, and exportable geospatial products.
6. Explicit separation between operational rule-based results, experimental deep-learning readiness, and claims that require future validation.

The novelty lies in this integrated framework, not in presenting U-Net, DeepLabV3+, or SegFormer as newly invented architectures.

## Quick Start With Docker

```powershell
docker compose down
docker compose up --build --force-recreate
```

Open:

- Frontend: http://localhost:5173
- Backend API: http://localhost:8000/api/health

## Local Development

Backend:

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn fastapi_run:app --host 0.0.0.0 --port 8000
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

## Demo Login

The current demo build uses a mock token endpoint:

- email: `officer@mozziespot.ai`
- password: `demo123`

## Project Structure

```text
backend/      FastAPI/Flask APIs, AI/GIS/risk modules, services, tests
frontend/     React TypeScript dashboard
sample-data/  Demo detections and synthetic satellite metadata
docs/         Architecture, deployment, dissertation outline
deploy/       Render/Vercel deployment notes
```

## Main API Endpoints

- `GET /api/health`
- `GET /api/dashboard`
- `GET /api/detections`
- `GET /api/state-risk`
- `POST /api/satellite/search`
- `GET or POST /api/satellite/download`
- `POST /api/satellite/process`
- `GET /api/satellite/output/<scene_id>/<filename>`
- `GET /api/analytics`
- `GET /api/export/csv`
- `GET /api/export/excel`
- `GET /api/export/geojson`
- `GET /api/export/shapefile`
- `POST /api/analyze`
- `POST /api/alerts/send`
- `GET /api/reports/weekly`
- `GET /api/reports/daily`
- `POST /api/auth/login`

## Academic Modules

- Deep learning water segmentation scaffold: `backend/app/ai/unet.py`
- DeepLabV3+ scaffold: `backend/app/ai/deeplabv3plus.py`
- SegFormer scaffold: `backend/app/ai/segformer.py`
- Ensemble mask fusion: `backend/app/ai/ensemble.py`
- Sentinel STAC and processing service: `backend/app/services/satellite_service.py`
- Advanced scoring/analytics/export layer: `backend/app/services/advanced_service.py`
- NDWI processing: `backend/app/ai/ndwi.py`
- Temporal persistence: `backend/app/ai/temporal.py`
- Risk scoring: `backend/app/services/risk_engine.py`
- Disease suitability: `backend/app/services/disease_engine.py`
- Explainability: `backend/app/services/explainability.py`
- Real raster pipeline: `backend/app/satellite/raster_pipeline.py`

## Deployment Notes

This project is deployment-ready as a structured full-stack application. For real satellite production use, add trained model weights, PostGIS connection settings, official village/mandal/district boundary files, validated field labels, and verified local health authority contact configuration.

## Satellite Workflow

1. Select a probable waterbody dot or enter coordinates.
2. Click `Search Latest Scene` to query Sentinel-2 metadata.
3. Set `MOZZIESPOT_REAL_DOWNLOAD=1` for full band files; the default `0` creates only a scene manifest.
4. Click `Run AI Processing`.
5. Download the RGB preview, NDWI, MNDWI, NDVI, water mask, or waterbody GeoJSON from the generated outputs panel.

Sentinel-2 is periodic Earth-observation imagery, not a live camera feed. The application has a live clock and browser GPS tracking, while satellite results update when a new scene is searched and processed.

## Data Availability

This project uses open-access Sentinel-2 satellite imagery obtained through the Copernicus Data Space Ecosystem and its STAC API. No separate labelled dataset was used in the operational workflow.

- [Copernicus Data Space Ecosystem](https://dataspace.copernicus.eu/)
- [Copernicus Data Space STAC API documentation](https://documentation.dataspace.copernicus.eu/APIs/STAC.html)

## Troubleshooting A Stale Docker Build

If the browser still shows old controls after source changes, stop the running stack, rebuild the images, and hard-refresh the browser:

```powershell
docker compose down
docker compose build --no-cache
docker compose up
```

If `npm run build` reports missing `is_waterbody` or satellite method arguments, make sure `frontend/src/pages/App.tsx` and `frontend/src/lib/api.ts` came from the same project version.



## Advanced AP + Telangana Risk Map

This build includes:

- Red/yellow/green statewide probable mosquito breeding waterbody dots for Andhra Pradesh and Telangana.
- Dropdown filtering by state, district, and village/ward.
- Place-name search plus latitude/longitude spot prediction.
- Disease suitability scores for malaria, dengue, chikungunya, diarrhea, cholera, and typhoid.
- Browser location tracking for nearby risk zones while walking.
- Authority alert message generation for GHMC, municipalities, and panchayats.
- WhatsApp message link generation and Telegram sending when bot credentials are configured.

Scientific note: satellite/map evidence estimates probable breeding habitats and mosquito activity risk. It cannot directly see mosquito eggs or adult mosquitoes.

## Alert buttons

- WhatsApp Alert opens a WhatsApp message with the selected risk location.
- Telegram Alert button opens Telegram share with the same alert message. If TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID are configured in .env, the backend also sends automatically to that Telegram chat.
- Open in Google Maps shows the exact latitude/longitude used by the selected searched place or clicked spot.
