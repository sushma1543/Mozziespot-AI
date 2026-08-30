# Architecture

MozzieSpot AI is organized as a full-stack decision-support platform.

## Data Flow

1. User selects AOI by search, dropdown, map click, coordinate input, or live walking location.
2. Sentinel-2 scenes are searched through Copernicus Data Space STAC with AWS Earth Search fallback.
3. Bands B02, B03, B04, B08, B11, B12, QA60, and SCL are selected for processing.
4. QA60 and SCL masks remove cloud/cloud-shadow evidence.
5. NDWI, MNDWI, and NDVI are generated.
6. Water evidence is classified into permanent, temporary, flood, stagnant, artificial, construction pit, or drainage blockage categories.
7. Mosquito Risk Score is calculated on a 0-100 scale.
8. Disease suitability scores are estimated.
9. GeoJSON detections are displayed on an interactive GIS dashboard.
10. High-risk detections can trigger public-health alerts and exports.

## Backend Modules

- `fastapi_run.py`: FastAPI entrypoint
- `api/routes.py`: Flask-compatible REST API layer mounted under FastAPI
- `ai/unet.py`: U-Net segmentation scaffold
- `ai/deeplabv3plus.py`: DeepLabV3+ segmentation scaffold
- `ai/segformer.py`: SegFormer segmentation scaffold
- `ai/ensemble.py`: model probability fusion
- `satellite/`: STAC, cloud mask, band, spectral-index, and water-detection modules
- `services/advanced_service.py`: advanced scoring, analytics, exports, module status
- `ai/ndwi.py`: NDWI computation
- `ai/temporal.py`: persistence analysis
- `services/risk_engine.py`: weighted risk scoring
- `services/disease_engine.py`: disease suitability model
- `services/explainability.py`: human-readable evidence
- `services/alert_service.py`: Telegram and email alerts
- `services/report_service.py`: PDF report generation

## Frontend Modules

- `MapPanel`: Leaflet GIS map and risk markers
- `MetricCard`: operational KPIs
- `DiseaseChart`: disease suitability visualization
- `RiskBadge`: risk labeling
- `App`: command-center dashboard

## Production Additions

- Store detections in PostgreSQL/PostGIS
- Add trained model weights for U-Net, DeepLabV3+, and SegFormer
- Add official village, mandal, and district boundary layers
- Train U-Net on validated labelled water-body masks
- Add RBAC with persistent users
- Add audit logs for public health interventions
