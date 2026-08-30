# Dissertation Draft

## Chapter 1: Introduction

Mosquito-borne diseases remain a major public-health challenge in tropical regions. Stagnant water and temporary water accumulation create favorable habitats for mosquito breeding. Traditional field surveys are valuable but time-consuming. Remote sensing, GIS, and AI can support early identification of probable breeding waterbody risk areas.

MozzieSpot AI is proposed as an explainable AI-GIS platform for AP and Telangana. The system combines Sentinel-2 scene discovery, spectral indices, water persistence, environmental indicators, population exposure, disease suitability, and public-health alerting.

## Chapter 2: Literature Review

Previous research shows that remote sensing can identify water, vegetation, and land-cover conditions related to vector habitats. NDWI and MNDWI are widely used for water extraction. Deep-learning segmentation models such as U-Net, DeepLabV3+, and transformer-based approaches can improve waterbody mapping. GIS dashboards help convert technical outputs into decisions for public-health officers.

The research gap is the integration of satellite scene discovery, image-processing indicators, explainable risk scoring, disease suitability, field-search support, authority alerts, and exportable reports in one operational platform.

## Chapter 3: System Design

The system contains:

- React + TypeScript frontend.
- Leaflet GIS map.
- FastAPI entrypoint.
- Flask-compatible API routes.
- Satellite service layer.
- Risk and disease scoring services.
- Alert and report services.
- Docker deployment.

## Chapter 4: Methodology

The methodology follows six stages:

1. AOI selection.
2. Sentinel-2 scene search.
3. Cloud masking and band extraction.
4. Spectral-index generation.
5. Water and risk classification.
6. Dashboard visualization, reports, and alerts.

## Chapter 5: Algorithms

NDWI:

```text
NDWI = (B03 - B08) / (B03 + B08)
```

MNDWI:

```text
MNDWI = (B03 - B11) / (B03 + B11)
```

NDVI:

```text
NDVI = (B08 - B04) / (B08 + B04)
```

Mosquito Risk Score:

```text
score = 100 * (
  0.24 * water_persistence
+ 0.18 * NDWI
+ 0.12 * rainfall_score
+ 0.12 * temperature_score
+ 0.10 * humidity_score
+ 0.08 * vegetation
+ 0.10 * population_density
+ 0.06 * previous_outbreaks
)
```

## Chapter 6: Implementation

The backend exposes APIs for satellite search, risk mapping, analytics, alerts, and exports. The frontend displays risk dots, satellite/OSM layers, selected-location details, disease charts, analytics, module status, and export buttons.

## Chapter 7: Results

The prototype demonstrates:

- Searchable AP/Telangana risk map.
- Sentinel scene search and fallback manifest generation.
- Waterbody risk classification.
- Disease suitability estimation.
- Explainable factor contribution bars.
- PDF, CSV, Excel, GeoJSON, and Shapefile exports.
- WhatsApp and Telegram alert flows.

## Chapter 8: Conclusion

MozzieSpot AI shows how AI, remote sensing, GIS, and public-health workflows can be combined into a decision-support system. The system is suitable as an M.Tech capstone prototype and can be extended into a production platform using trained model weights, official boundary datasets, PostGIS, and field validation.
