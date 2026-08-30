# PPT Slide Content

## Slide 1: Title

MozzieSpot AI Advanced  
Explainable AI-GIS Platform for Mosquito Breeding Waterbody Risk Mapping

## Slide 2: Problem

- Mosquito breeding is strongly linked to stagnant water and environmental conditions.
- Manual inspection is slow across villages, mandals, and districts.
- Public-health teams need searchable risk maps and fast authority alerts.

## Slide 3: Objectives

- Detect probable breeding waterbody risk zones.
- Use Sentinel-2 remote-sensing indicators.
- Predict mosquito risk and disease suitability.
- Provide explainable risk scores.
- Send alerts and generate reports.

## Slide 4: Proposed System

- React dashboard.
- Leaflet GIS map.
- FastAPI/Flask backend.
- Sentinel STAC integration.
- Image-processing pipeline.
- AI model scaffolds.
- Alerts and exports.

## Slide 5: Satellite Pipeline

- AOI selection.
- Copernicus STAC search.
- AWS Sentinel fallback.
- Band extraction.
- QA60 and SCL cloud masking.
- NDWI, MNDWI, NDVI generation.

## Slide 6: AI Models

- U-Net.
- DeepLabV3+.
- SegFormer.
- Ensemble mask fusion.

## Slide 7: Risk Formula

Mosquito Risk Score combines:

- Water persistence.
- NDWI.
- Rainfall.
- Temperature.
- Humidity.
- Vegetation.
- Population density.
- Previous outbreaks.

## Slide 8: Disease Suitability

Predicted environmental suitability:

- Dengue.
- Malaria.
- Chikungunya.
- Japanese Encephalitis.

## Slide 9: GIS Dashboard

- OpenStreetMap layer.
- Satellite imagery layer.
- Red/yellow/green risk dots.
- Search by village, district, state, or coordinates.
- Live walking/tracking location.

## Slide 10: Analytics

- Total water bodies.
- Stagnant water count.
- High-risk villages.
- Monthly trend.
- Disease trend.

## Slide 11: Alerts and Exports

- WhatsApp alert.
- Telegram Bot alert.
- Email alert.
- PDF report.
- CSV, Excel, GeoJSON, Shapefile exports.

## Slide 12: Conclusion

MozzieSpot AI converts remote-sensing and GIS evidence into explainable public-health actions for mosquito-risk monitoring and sanitation response.
