"""
Satellite Processing Service.

The service is safe for classroom demos: it searches real STAC catalogs and
creates a scene manifest by default. Full Sentinel-2 band downloads can be
enabled with MOZZIESPOT_REAL_DOWNLOAD=1 because raw scenes are large.
"""

from app.services.advanced_service import (
    bbox_from_payload,
    download_scene_manifest,
    process_satellite_pipeline,
    search_sentinel_scenes,
)


class SatelliteService:
    def search(self, payload=None):
        payload = payload or {}
        return search_sentinel_scenes(
            bbox=bbox_from_payload(payload),
            start_date=payload.get("start_date"),
            end_date=payload.get("end_date"),
            cloud_cover=int(payload.get("cloud_cover", 15)),
            limit=int(payload.get("limit", 6)),
        )

    def download(self, payload=None):
        return download_scene_manifest(payload or {})

    def process(self, bbox=None, start_date=None, end_date=None, payload=None):
        merged = dict(payload or {})
        if bbox:
            merged["bbox"] = bbox
        if start_date:
            merged["start_date"] = start_date
        if end_date:
            merged["end_date"] = end_date
        return process_satellite_pipeline(merged)
