from __future__ import annotations

import csv
import io
import json
import os
import tempfile
import zipfile
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Iterable

import requests
from flask import current_app

from app.satellite.config import (
    AWS_STAC,
    COLLECTION,
    COPERNICUS_STAC,
    DEFAULT_AOI,
    DEFAULT_BANDS,
    OUTPUT_DIR,
    RAW_DIR,
)
from app.satellite.raster_pipeline import RasterPipelineError, SentinelRasterPipeline


REQUIRED_BANDS = ["B02", "B03", "B04", "B08", "B11", "B12", "QA60", "SCL"]

# Copernicus Data Space exposes Sentinel-2 assets with band names such as B03,
# while the AWS mirror uses descriptive names. Keep both providers usable with
# the same processing pipeline.
ASSET_ALIASES = {
    "B02": ["B02", "b02", "blue"],
    "B03": ["B03", "b03", "green"],
    "B04": ["B04", "b04", "red"],
    "B08": ["B08", "b08", "nir", "nir08"],
    "B11": ["B11", "b11", "swir16"],
    "B12": ["B12", "b12", "swir22"],
    "QA60": ["QA60", "qa60", "quality"],
    "SCL": ["SCL", "scl", "scene-classification"],
}

MODULES = [
    {
        "name": "Real Satellite Images",
        "status": "implemented",
        "items": [
            "Copernicus Data Space STAC search",
            "AWS Earth Search fallback",
            "Automatic date window",
            "AOI bbox selection",
            "Optional real band download with MOZZIESPOT_REAL_DOWNLOAD=1",
        ],
    },
    {
        "name": "Image Processing",
        "status": "implemented",
        "items": ["QA60 cloud mask", "SCL mask", "B02/B03/B04/B08/B11/B12 extraction", "NDWI", "MNDWI", "NDVI"],
    },
    {
        "name": "Deep Learning",
        "status": "model-ready",
        "items": ["U-Net scaffold", "DeepLabV3+ scaffold", "SegFormer scaffold", "Ensemble interface"],
    },
    {
        "name": "GIS Dashboard",
        "status": "implemented",
        "items": ["OpenStreetMap", "satellite imagery layer", "risk dots", "heat rings", "place search", "coordinate search"],
    },
    {
        "name": "Exports and Alerts",
        "status": "implemented",
        "items": ["CSV", "Excel", "PDF", "GeoJSON", "Shapefile zip", "Telegram", "WhatsApp", "Email-ready alerts"],
    },
]


def clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


def automatic_date_range(days_back: int = 90) -> tuple[str, str]:
    end = date.today()
    start = end - timedelta(days=days_back)
    return start.isoformat(), end.isoformat()


def default_bbox() -> list[float]:
    return [
        DEFAULT_AOI["min_lon"],
        DEFAULT_AOI["min_lat"],
        DEFAULT_AOI["max_lon"],
        DEFAULT_AOI["max_lat"],
    ]


def bbox_from_payload(payload: dict[str, Any] | None) -> list[float]:
    payload = payload or {}
    bbox = payload.get("bbox")
    if isinstance(bbox, list) and len(bbox) == 4:
        return [float(value) for value in bbox]
    latitude = payload.get("latitude")
    longitude = payload.get("longitude")
    if latitude is not None and longitude is not None:
        lat = float(latitude)
        lon = float(longitude)
        pad = float(payload.get("padding", 0.05))
        return [lon - pad, lat - pad, lon + pad, lat + pad]
    return default_bbox()


def stac_sources() -> list[dict[str, str]]:
    return [
        {"name": "Copernicus Data Space", "url": COPERNICUS_STAC.rstrip("/") + "/search"},
        {"name": "AWS Earth Search", "url": AWS_STAC.rstrip("/") + "/search"},
    ]


def _normalize_scene(feature: dict[str, Any], source: str) -> dict[str, Any]:
    properties = feature.get("properties", {})
    assets = feature.get("assets", {})
    normalized_assets: dict[str, str] = {}
    for band in REQUIRED_BANDS:
        candidates = ASSET_ALIASES[band]
        for key in candidates:
            href = assets.get(key, {}).get("href") if isinstance(assets.get(key), dict) else None
            if href:
                normalized_assets[band] = href
                break
    return {
        "id": feature.get("id", "unknown-scene"),
        "source": source,
        "collection": feature.get("collection", COLLECTION),
        "datetime": properties.get("datetime") or feature.get("datetime"),
        "cloud_cover": round(float(properties.get("eo:cloud_cover", 0)), 2),
        "bbox": feature.get("bbox"),
        "assets": normalized_assets,
        "asset_count": len(normalized_assets),
    }


def fallback_scenes(bbox: list[float]) -> list[dict[str, Any]]:
    start, end = automatic_date_range()
    return [
        {
            "id": "DEMO-S2-L2A-AP-TS-LATEST",
            "source": "offline demo fallback",
            "collection": COLLECTION,
            "datetime": end + "T05:20:00Z",
            "cloud_cover": 7.4,
            "bbox": bbox,
            "assets": {band: f"demo://sentinel-2/{band}.tif" for band in REQUIRED_BANDS},
            "asset_count": len(REQUIRED_BANDS),
            "note": "Online STAC search was unavailable, so the app returned a demo scene manifest.",
            "date_window": {"start_date": start, "end_date": end},
        }
    ]


def search_sentinel_scenes(
    bbox: list[float],
    start_date: str | None = None,
    end_date: str | None = None,
    cloud_cover: int = 15,
    limit: int = 6,
) -> dict[str, Any]:
    if not start_date or not end_date:
        start_date, end_date = automatic_date_range()

    payload = {
        "collections": [COLLECTION],
        "bbox": bbox,
        "datetime": f"{start_date}T00:00:00Z/{end_date}T23:59:59Z",
        "query": {"eo:cloud_cover": {"lt": cloud_cover}},
        "limit": limit,
    }

    errors: list[str] = []
    for source in stac_sources():
        try:
            response = requests.post(source["url"], json=payload, timeout=8)
            response.raise_for_status()
            features = response.json().get("features", [])
            scenes = [_normalize_scene(feature, source["name"]) for feature in features]
            if scenes:
                scenes.sort(key=lambda scene: scene.get("datetime") or "", reverse=True)
                return {
                    "status": "completed",
                    "online": True,
                    "source": source["name"],
                    "bbox": bbox,
                    "date_window": {"start_date": start_date, "end_date": end_date},
                    "scenes": scenes,
                    "selected_scene": scenes[0],
                }
        except Exception as exc:
            errors.append(f"{source['name']}: {exc}")

    scenes = fallback_scenes(bbox)
    return {
        "status": "fallback",
        "online": False,
        "source": "offline demo fallback",
        "bbox": bbox,
        "date_window": {"start_date": start_date, "end_date": end_date},
        "scenes": scenes,
        "selected_scene": scenes[0],
        "errors": errors,
    }


def download_scene_manifest(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    bbox = bbox_from_payload(payload)
    search = search_sentinel_scenes(
        bbox=bbox,
        start_date=payload.get("start_date"),
        end_date=payload.get("end_date"),
        cloud_cover=int(payload.get("cloud_cover", 15)),
        limit=int(payload.get("limit", 6)),
    )
    selected = search["selected_scene"]
    folder = RAW_DIR / selected["id"]
    folder.mkdir(parents=True, exist_ok=True)
    manifest_path = folder / "scene-manifest.json"
    manifest_path.write_text(json.dumps(search, indent=2), encoding="utf-8")

    real_download = os.getenv("MOZZIESPOT_REAL_DOWNLOAD", "0") == "1"
    downloaded: list[str] = []
    if real_download and search["online"]:
        for band, href in selected.get("assets", {}).items():
            output = folder / f"{band}.tif"
            if output.exists():
                downloaded.append(str(output))
                continue
            try:
                with requests.get(href, stream=True, timeout=120) as response:
                    response.raise_for_status()
                    with output.open("wb") as handle:
                        for chunk in response.iter_content(chunk_size=1024 * 1024):
                            if chunk:
                                handle.write(chunk)
                downloaded.append(str(output))
            except Exception as exc:
                return {
                    "status": "partial",
                    "folder": str(folder),
                    "manifest": str(manifest_path),
                    "selected_scene": selected,
                    "downloaded": downloaded,
                    "message": f"Stopped while downloading {band}: {exc}",
                }

    return {
        "status": "success",
        "folder": str(folder),
        "manifest": str(manifest_path),
        "selected_scene": selected,
        "downloaded": downloaded,
        "real_download_enabled": real_download,
        "message": "Scene manifest is ready. Set MOZZIESPOT_REAL_DOWNLOAD=1 to download full Sentinel-2 band files.",
    }


def spectral_formulas() -> dict[str, str]:
    return {
        "NDWI": "(B03 - B08) / (B03 + B08)",
        "MNDWI": "(B03 - B11) / (B03 + B11)",
        "NDVI": "(B08 - B04) / (B08 + B04)",
    }


def classify_water_type(values: dict[str, float]) -> str:
    persistence_days = values.get("days_persistent", 0)
    ndwi = values.get("ndwi", 0)
    mndwi = values.get("mndwi", ndwi)
    rainfall = values.get("rainfall", 0)
    urban = values.get("urban_factor", 0)
    vegetation = values.get("vegetation", 0)

    if persistence_days >= 180 and ndwi >= 0.45:
        return "Permanent lake"
    if rainfall >= 85 and persistence_days <= 14 and mndwi >= 0.35:
        return "Flood water"
    if persistence_days >= 10 and ndwi >= 0.35 and urban >= 0.55:
        return "Stagnant water"
    if urban >= 0.72 and persistence_days <= 20:
        return "Construction pit or artificial pond"
    if mndwi >= 0.28 and vegetation < 0.35:
        return "Drainage blockage"
    if persistence_days >= 30:
        return "Temporary waterbody"
    return "Monitoring water trace"


def mosquito_risk_score(values: dict[str, float]) -> float:
    temp = values.get("temperature", 28)
    temp_score = 1.0 if 24 <= temp <= 34 else 0.55
    humidity_score = clamp(values.get("humidity", 60) / 100)
    rainfall_score = clamp(values.get("rainfall", 0) / 120)
    score = (
        0.24 * clamp(values.get("water_persistence", 0))
        + 0.18 * clamp(values.get("ndwi", 0))
        + 0.12 * rainfall_score
        + 0.12 * temp_score
        + 0.10 * humidity_score
        + 0.08 * clamp(values.get("vegetation", 0))
        + 0.10 * clamp(values.get("population_density", 0))
        + 0.06 * clamp(values.get("previous_outbreaks", 0))
    )
    return round(score * 100, 2)


def mosquito_risk_level(score: float) -> str:
    if score >= 80:
        return "Severe"
    if score >= 60:
        return "High"
    if score >= 40:
        return "Moderate"
    if score >= 20:
        return "Low"
    return "Very Low"


def disease_probabilities(values: dict[str, float], risk_score: float) -> dict[str, float]:
    base = clamp(risk_score / 100)
    temp = values.get("temperature", 28)
    humidity = clamp(values.get("humidity", 60) / 100)
    rainfall = clamp(values.get("rainfall", 0) / 120)
    urban = clamp(values.get("urban_factor", 0))
    vegetation = clamp(values.get("vegetation", 0))
    water = clamp(values.get("water_persistence", 0))
    warm = 1.0 if 24 <= temp <= 34 else 0.55
    return {
        "dengue": round(100 * base * (0.35 + 0.35 * urban + 0.30 * humidity), 1),
        "malaria": round(100 * base * (0.30 + 0.35 * water + 0.35 * warm), 1),
        "chikungunya": round(100 * base * (0.40 + 0.35 * urban + 0.25 * rainfall), 1),
        "japanese_encephalitis": round(100 * base * (0.35 + 0.35 * water + 0.30 * vegetation), 1),
    }


def advanced_features_from_detection(detection: dict[str, Any]) -> dict[str, float]:
    water_persistence = clamp(float(detection.get("days_persistent", 0)) / 21)
    ndwi = clamp(float(detection.get("ndwi", 0)))
    population = clamp(float(detection.get("population_density", 0)))
    vegetation = clamp(float(detection.get("vegetation", 0.42)))
    temperature = float(detection.get("temperature", 28))
    urban_factor = clamp(0.45 + population * 0.45)
    rainfall = round(35 + ndwi * 55 + water_persistence * 35, 1)
    humidity = round(48 + water_persistence * 28 + ndwi * 16, 1)
    previous_outbreaks = clamp((population + water_persistence) / 2)
    return {
        "water_persistence": water_persistence,
        "ndwi": ndwi,
        "mndwi": clamp(ndwi * 0.92 + 0.05),
        "temperature": temperature,
        "rainfall": rainfall,
        "humidity": humidity,
        "vegetation": vegetation,
        "population_density": population,
        "urban_factor": urban_factor,
        "previous_outbreaks": previous_outbreaks,
        "days_persistent": float(detection.get("days_persistent", 0)),
    }


def enhance_detection(detection: dict[str, Any]) -> dict[str, Any]:
    values = advanced_features_from_detection(detection)
    is_search_marker = bool(detection.get("search_match") or detection.get("zoom_to_place"))
    is_waterbody = bool(
        detection.get("is_waterbody", values["ndwi"] >= 0.28 and values["days_persistent"] >= 3)
    )
    score = mosquito_risk_score(values)
    if not is_waterbody:
        score = min(score, 19.99)
    contributions = {
        "water_persistence": round(24 * clamp(values["water_persistence"]), 2),
        "ndwi": round(18 * clamp(values["ndwi"]), 2),
        "rainfall": round(12 * clamp(values["rainfall"] / 120), 2),
        "temperature": round(12 * (1.0 if 24 <= values["temperature"] <= 34 else 0.55), 2),
        "humidity": round(10 * clamp(values["humidity"] / 100), 2),
        "vegetation": round(8 * clamp(values["vegetation"]), 2),
        "population_density": round(10 * clamp(values["population_density"]), 2),
        "previous_outbreaks": round(6 * clamp(values["previous_outbreaks"]), 2),
    }
    output = dict(detection)
    output.update(
        {
            "mosquito_risk_score": score,
            "mosquito_risk_level": mosquito_risk_level(score),
            "water_type": classify_water_type(values) if is_waterbody else "No waterbody evidence",
            "is_waterbody": is_waterbody,
            "marker_type": "search" if is_search_marker else ("waterbody-risk" if is_waterbody else "non-water"),
            "evidence_status": "probable-waterbody" if is_waterbody else "no-waterbody-evidence",
            "advanced_disease_index": disease_probabilities(values, score) if is_waterbody else {
                "dengue": 0.0,
                "malaria": 0.0,
                "chikungunya": 0.0,
                "japanese_encephalitis": 0.0,
            },
            "advanced_factors": values,
            "explainability": {
                "formula": "weighted sum of water persistence, NDWI, rainfall, temperature, humidity, vegetation, population density, and previous outbreaks",
                "contributions": contributions,
                "top_factors": sorted(contributions.items(), key=lambda item: item[1], reverse=True)[:4],
            },
        }
    )
    return output


def analytics_summary(detections: Iterable[dict[str, Any]]) -> dict[str, Any]:
    enhanced = [enhance_detection(detection) for detection in detections]
    high = [item for item in enhanced if item["mosquito_risk_level"] in {"High", "Severe"}]
    stagnant = [item for item in enhanced if "Stagnant" in item["water_type"] or "Drainage" in item["water_type"]]
    disease_keys = ["dengue", "malaria", "chikungunya", "japanese_encephalitis"]
    disease_trend = [
        {
            "disease": disease,
            "average": round(sum(item["advanced_disease_index"][disease] for item in enhanced) / max(len(enhanced), 1), 1),
        }
        for disease in disease_keys
    ]
    water_type_counts: dict[str, int] = {}
    for item in enhanced:
        water_type_counts[item["water_type"]] = water_type_counts.get(item["water_type"], 0) + 1
    monthly_trend = []
    for index, month in enumerate(["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"], start=1):
        seasonal = 0.75 + (0.45 if month in {"Jun", "Jul", "Aug", "Sep", "Oct"} else 0.0)
        monthly_trend.append(
            {
                "month": month,
                "water_bodies": round(len(enhanced) * seasonal * (0.72 + index / 36)),
                "severe_risk": round(len(high) * seasonal * (0.62 + index / 48)),
            }
        )
    return {
        "total_water_bodies": len(enhanced),
        "total_stagnant_water": len(stagnant),
        "high_risk_villages": len({item.get("village") for item in high}),
        "severe_zones": len([item for item in enhanced if item["mosquito_risk_level"] == "Severe"]),
        "water_type_counts": water_type_counts,
        "disease_trend": disease_trend,
        "monthly_trend": monthly_trend,
        "top_priority": sorted(enhanced, key=lambda item: item["mosquito_risk_score"], reverse=True)[:15],
    }


def satellite_layers_payload() -> dict[str, Any]:
    return {
        "status": "completed",
        "layers": {
            "openstreetmap": "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
            "satellite": "Esri World Imagery tile layer enabled in frontend",
            "google_satellite": "optional: configure Google Maps API key before production use",
            "heatmap": "/api/satellite/heatmap",
            "risk_zones": "/api/state-risk",
            "village_boundary": "planned: connect official village boundary GeoJSON",
            "mandal_boundary": "planned: connect official mandal boundary GeoJSON",
            "district_boundary": "planned: connect official district boundary GeoJSON",
        },
    }


def _output_download_urls(scene_id: str, output_paths: dict[str, str]) -> dict[str, str]:
    """Build browser URLs only for files written by the local raster pipeline."""
    return {
        name: f"/api/satellite/output/{scene_id}/{Path(path).name}"
        for name, path in output_paths.items()
    }


def process_satellite_pipeline(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    manifest = download_scene_manifest(payload)
    selected = manifest.get("selected_scene", {})
    scene_id = selected.get("id", "demo-scene")
    output_folder = OUTPUT_DIR / scene_id
    output_folder.mkdir(parents=True, exist_ok=True)
    outputs = {
        "rgb": str(output_folder / "rgb_preview.tif"),
        "preview": str(output_folder / "rgb_preview.png"),
        "ndwi": str(output_folder / "ndwi.tif"),
        "mndwi": str(output_folder / "mndwi.tif"),
        "ndvi": str(output_folder / "ndvi.tif"),
        "water": str(output_folder / "water_mask.tif"),
        "water_mask": str(output_folder / "water_mask.tif"),
    }
    source_folder = Path(manifest["folder"])
    missing_bands = [band for band in REQUIRED_BANDS if not (source_folder / f"{band}.tif").exists()]

    raster_result: dict[str, Any] | None = None
    raster_error: str | None = None
    if not missing_bands:
        try:
            raster_result = SentinelRasterPipeline().process(source_folder, output_folder)
            outputs = raster_result["outputs"]
        except RasterPipelineError as exc:
            raster_error = str(exc)

    mode = "raster" if raster_result else "manifest"
    if raster_result:
        message = "Real Sentinel-2 bands were processed into RGB, cloud-masked indices, a water mask, and waterbody GeoJSON."
    elif missing_bands:
        message = (
            "Scene manifest is ready. Download all Sentinel-2 bands to enable real raster processing. "
            f"Missing: {', '.join(missing_bands)}."
        )
    else:
        message = f"Satellite files were found but raster processing could not finish: {raster_error}"

    result = {
        "status": "completed",
        "mode": mode,
        "scene": selected,
        "folder": manifest["folder"],
        "outputs": outputs,
        "download_urls": _output_download_urls(scene_id, outputs) if raster_result else {},
        "indices": spectral_formulas(),
        "cloud_mask": {"QA60": "bits 10 and 11 removed", "SCL": "clear classes 4, 5, and 6 retained"},
        "water_analysis": {
            "classes": [
                "Permanent lake",
                "Temporary waterbody",
                "Flood water",
                "Stagnant water",
                "Artificial pond",
                "Construction pit",
                "Drainage blockage",
            ]
        },
        "missing_bands": missing_bands,
        "statistics": raster_result.get("statistics") if raster_result else None,
        "waterbody_geojson": raster_result.get("waterbody_geojson") if raster_result else None,
        "waterbody_download_url": (
            f"/api/satellite/output/{scene_id}/{Path(raster_result['waterbody_geojson']).name}"
            if raster_result
            else None
        ),
        "message": message,
    }
    (output_folder / "processing-summary.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result


def detections_geojson(detections: Iterable[dict[str, Any]]) -> dict[str, Any]:
    return {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [item["longitude"], item["latitude"]]},
                "properties": {key: value for key, value in enhance_detection(item).items() if key not in {"latitude", "longitude"}},
            }
            for item in detections
        ],
    }


def detections_csv(detections: Iterable[dict[str, Any]]) -> str:
    rows = [enhance_detection(item) for item in detections]
    output = io.StringIO()
    fieldnames = [
        "id",
        "name",
        "state",
        "district",
        "village",
        "latitude",
        "longitude",
        "risk_score",
        "risk_level",
        "mosquito_risk_score",
        "mosquito_risk_level",
        "water_type",
        "breeding_likelihood",
        "mosquito_activity_index",
    ]
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    for row in rows:
        writer.writerow({field: row.get(field, "") for field in fieldnames})
    return output.getvalue()


def detections_excel(detections: Iterable[dict[str, Any]]) -> bytes:
    import pandas as pd

    rows = [enhance_detection(item) for item in detections]
    frame = pd.DataFrame(
        [
            {
                "id": item["id"],
                "name": item["name"],
                "state": item.get("state"),
                "district": item.get("district"),
                "village": item.get("village"),
                "latitude": item["latitude"],
                "longitude": item["longitude"],
                "risk_score": item["risk_score"],
                "risk_level": item["risk_level"],
                "mosquito_risk_score": item["mosquito_risk_score"],
                "mosquito_risk_level": item["mosquito_risk_level"],
                "water_type": item["water_type"],
                "dengue": item["advanced_disease_index"]["dengue"],
                "malaria": item["advanced_disease_index"]["malaria"],
                "chikungunya": item["advanced_disease_index"]["chikungunya"],
                "japanese_encephalitis": item["advanced_disease_index"]["japanese_encephalitis"],
            }
            for item in rows
        ]
    )
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        frame.to_excel(writer, index=False, sheet_name="risk_zones")
    return output.getvalue()


def detections_shapefile_zip(detections: Iterable[dict[str, Any]]) -> bytes:
    import shapefile

    with tempfile.TemporaryDirectory() as temp_dir:
        base = Path(temp_dir) / "mozziespot-risk-zones"
        writer = shapefile.Writer(str(base), shapeType=shapefile.POINT)
        writer.field("ID", "C", size=40)
        writer.field("NAME", "C", size=80)
        writer.field("STATE", "C", size=40)
        writer.field("DISTRICT", "C", size=40)
        writer.field("RISK", "C", size=20)
        writer.field("SCORE", "N", decimal=2)
        for item in detections:
            enhanced = enhance_detection(item)
            writer.point(float(enhanced["longitude"]), float(enhanced["latitude"]))
            writer.record(
                enhanced.get("id", ""),
                enhanced.get("name", "")[:80],
                enhanced.get("state", "")[:40],
                enhanced.get("district", "")[:40],
                enhanced.get("mosquito_risk_level", "")[:20],
                float(enhanced.get("mosquito_risk_score", 0)),
            )
        writer.close()
        prj = base.with_suffix(".prj")
        prj.write_text(
            'GEOGCS["WGS 84",DATUM["WGS_1984",SPHEROID["WGS 84",6378137,298.257223563]],'
            'PRIMEM["Greenwich",0],UNIT["degree",0.0174532925199433]]',
            encoding="utf-8",
        )
        output = io.BytesIO()
        with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
            for suffix in [".shp", ".shx", ".dbf", ".prj"]:
                path = base.with_suffix(suffix)
                archive.write(path, path.name)
        return output.getvalue()


def telegram_status() -> dict[str, Any]:
    token = current_app.config.get("TELEGRAM_BOT_TOKEN", "")
    chat_id = current_app.config.get("TELEGRAM_CHAT_ID", "")
    return {
        "status": "configured" if token and chat_id else "not_configured",
        "sent": False,
        "message": "Telegram Bot API credentials are configured." if token and chat_id else "Add TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in docker-compose.yml or .env.",
    }


def admin_roles() -> dict[str, Any]:
    return {
        "roles": [
            {"role": "Admin", "dashboard": "Full system, users, satellite processing, exports"},
            {"role": "Health Officer", "dashboard": "Disease risk, alerts, reports, field verification"},
            {"role": "Municipality", "dashboard": "Drain cleaning, stagnant water removal, action status"},
            {"role": "Panchayat", "dashboard": "Village-level waterbody monitoring and local alerts"},
        ],
        "demo_login": {"email": "officer@mozziespot.ai", "password": "demo123"},
    }
