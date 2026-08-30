# Project Proposal

## Project Title

MozzieSpot AI: An Explainable AI-GIS Platform for Mosquito Breeding Waterbody Risk Mapping Using Sentinel-2 Remote-Sensing Indicators

## Problem Statement

Mosquito-borne diseases such as Dengue, Malaria, Chikungunya, and Japanese Encephalitis are strongly influenced by stagnant water, rainfall, temperature, humidity, vegetation, population exposure, and local sanitation conditions. Manual inspection of all waterbodies is slow and difficult, especially across large districts and villages.

## Objective

To develop a web-based AI-GIS system that identifies probable mosquito breeding waterbody risk zones, classifies water evidence, estimates disease suitability, explains the risk score, and sends alerts to public health or sanitation authorities.

## Scope

- Andhra Pradesh and Telangana risk mapping.
- Sentinel-2 STAC scene discovery.
- NDWI/MNDWI/NDVI image-processing pipeline.
- Deep-learning segmentation model scaffolds.
- Explainable mosquito risk score.
- GIS dashboard with search and tracking.
- Telegram, WhatsApp, email, PDF, and export support.

## Methodology

1. Select AOI from district, village, map click, or coordinates.
2. Search Sentinel-2 scenes using Copernicus Data Space and AWS fallback.
3. Extract spectral bands and cloud masks.
4. Generate NDWI, MNDWI, and NDVI.
5. Estimate water persistence and water type.
6. Calculate mosquito risk score.
7. Estimate disease suitability.
8. Display colored risk dots and analytics.
9. Generate reports and authority alerts.

## Expected Outcome

- A fully working dashboard.
- Searchable AP/Telangana risk map.
- Explainable risk prediction per location.
- Exportable reports and GIS data.
- IEEE-ready methodology and dissertation documentation.

## Future Enhancement

- Trained U-Net/DeepLabV3+/SegFormer weights.
- PostGIS database.
- Official village/mandal/district boundaries.
- Field-validation mobile app.
- Integration with municipal cleaning-ticket systems.
