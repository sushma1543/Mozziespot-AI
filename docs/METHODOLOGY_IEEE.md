# IEEE Paper Methodology

## Title

An Explainable AI-GIS Framework for Mosquito Breeding Waterbody Risk Mapping Using Sentinel-2 Remote-Sensing Indicators

## Study Area

The prototype focuses on Andhra Pradesh and Telangana, India. The system supports district, village, ward, and coordinate-level risk exploration.

## Data Sources

Prototype/demo data:

- Sample GeoJSON detections.
- Generated AP/Telangana district risk points.
- OpenStreetMap/Nominatim place lookup.
- Sentinel-2 scene metadata through STAC search.

Recommended production data:

- Sentinel-2 Level-2A imagery.
- Rainfall from CHIRPS, IMD, or GPM.
- Weather from IMD or Open-Meteo.
- Population from WorldPop or census layers.
- Official village, mandal, and district boundaries.
- Municipal cleaning logs and outbreak records.
- Field validation points collected by health workers.

## Satellite Image Preprocessing

1. Select AOI from bbox or user-selected coordinate.
2. Search Sentinel-2 Level-2A scenes using STAC.
3. Select lowest-cloud or latest scene in the date window.
4. Extract bands B02, B03, B04, B08, B11, B12, QA60, and SCL.
5. Apply QA60 cloud/cirrus mask.
6. Apply SCL mask to remove cloud shadow, cloud, cirrus, and snow classes.
7. Generate cloud-free spectral bands.

## Spectral Indices

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

## Waterbody Detection

The image-processing baseline detects water pixels using:

```text
water_mask = 1 if NDWI >= 0.30 else 0
```

Deep-learning extension:

- U-Net predicts a water probability mask.
- DeepLabV3+ predicts a multiscale contextual water mask.
- SegFormer predicts transformer-based water segmentation.
- Ensemble output combines model probability maps by weighted averaging.

## Water-Type Classification

The water evidence is classified using persistence, NDWI, MNDWI, rainfall, urban factor, and vegetation:

- Permanent lake: high NDWI and long persistence.
- Flood water: high rainfall, high MNDWI, short persistence.
- Stagnant water: persistent water in urban/populated context.
- Construction pit/artificial pond: urban water with shorter persistence.
- Drainage blockage: MNDWI evidence with low vegetation.

## Mosquito Risk Score

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

Risk classes:

- 0-20: Very Low.
- 20-40: Low.
- 40-60: Moderate.
- 60-80: High.
- 80-100: Severe.

## Disease Suitability

The system estimates environmental suitability, not confirmed disease cases.

```text
base = mosquito_risk_score / 100
dengue = 100 * base * (0.35 + 0.35 * urban + 0.30 * humidity)
malaria = 100 * base * (0.30 + 0.35 * water + 0.35 * warm_temperature)
chikungunya = 100 * base * (0.40 + 0.35 * urban + 0.25 * rainfall)
japanese_encephalitis = 100 * base * (0.35 + 0.35 * water + 0.30 * vegetation)
```

## Explainability

The dashboard displays factor contributions from the weighted risk formula. The highest contributing factors are shown as bars for each selected location.

## Evaluation Plan

For publication, evaluate using:

- Water segmentation: IoU, Dice score, precision, recall, F1.
- Risk-zone classification: confusion matrix, accuracy, precision, recall, F1, ROC-AUC.
- Field validation: compare predicted high-risk points against public health inspections.
- Ablation study: remove rainfall, population, NDWI, and persistence features one by one.
- Usability: officer workflow time and alert completion rate.

## Expected Contribution

The contribution is an integrated AI-GIS decision-support framework combining satellite scene discovery, spectral-index processing, deep-learning model scaffolds, explainable risk scoring, disease suitability estimation, map visualization, alerts, and exportable public-health reports.
