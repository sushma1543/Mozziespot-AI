# MozzieSpot AI Paper Figure Provenance

The manuscript uses no AI-generated photographs or satellite images.

- `real_world_imagery_vijayawada.png`: real ArcGIS World Imagery export capture for the Vijayawada/Amaravati-area bounding box `80.40,16.35,80.70,16.60`; source service: `https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/export`; captured 21 July 2026.
- `real_world_imagery_vijayawada_cropped.png`: cropped copy of the same real imagery for document layout.
- `project_dashboard_top.png`: screenshot of the running MozzieSpot AI application at `http://localhost:5173/`.
- `project_map_panel.png`: screenshot of the running Leaflet map and selected risk-zone panel.
- `project_alert_panel.png`: screenshot of the running alert controls and risk-priority list.
- `paper_architecture.png`: code-generated flowchart based on the project modules.
- `paper_alert_workflow.png`: code-generated alert workflow diagram.
- `paper_risk_weights.png`: code-generated bar chart of the implemented risk-score weights.

The ArcGIS image is a real satellite basemap and is intentionally not described as a Sentinel-2 product. A Sentinel-2 figure should be added only after `MOZZIESPOT_REAL_DOWNLOAD=1` is enabled, the scene bands are downloaded, and the processing summary records the scene ID, date, cloud cover, missing bands, and output statistics.
