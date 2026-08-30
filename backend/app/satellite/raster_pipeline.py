"""Production-style Sentinel-2 raster processing for a downloaded scene.

The pipeline aligns 10 m and 20 m Sentinel-2 bands, masks QA60/SCL cloud
pixels, writes RGB and spectral-index GeoTIFFs, and vectorises connected water
pixels to a GeoJSON file for the GIS dashboard.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import rasterio
from PIL import Image
from rasterio.enums import Resampling
from rasterio.features import shapes
from rasterio.warp import reproject, transform_geom
from skimage.morphology import remove_small_objects

from app.satellite.spectral_indices import mndwi, ndvi, ndwi, water_mask


class RasterPipelineError(RuntimeError):
    """Raised when a downloaded Sentinel scene cannot be processed safely."""


class SentinelRasterPipeline:
    required_bands = ("B02", "B03", "B04", "B08", "B11", "B12", "QA60", "SCL")
    clear_scl_classes = (4, 5, 6)

    def _read_aligned(self, path: Path, reference: dict[str, Any], categorical: bool = False) -> np.ndarray:
        with rasterio.open(path) as source:
            source_data = source.read(1)
            same_grid = (
                source.width == reference["width"]
                and source.height == reference["height"]
                and source.transform == reference["transform"]
                and source.crs == reference["crs"]
            )
            if same_grid:
                return source_data

            destination = np.zeros((reference["height"], reference["width"]), dtype=source_data.dtype)
            reproject(
                source=source_data,
                destination=destination,
                src_transform=source.transform,
                src_crs=source.crs,
                dst_transform=reference["transform"],
                dst_crs=reference["crs"],
                resampling=Resampling.nearest if categorical else Resampling.bilinear,
            )
            return destination

    @staticmethod
    def _safe_index(index: np.ndarray, clear_mask: np.ndarray) -> np.ndarray:
        result = index.astype("float32", copy=True)
        result[~clear_mask] = np.nan
        return result

    @staticmethod
    def _rgb_channel(array: np.ndarray, clear_mask: np.ndarray) -> np.ndarray:
        values = array.astype("float32", copy=True)
        valid = values[clear_mask]
        if valid.size == 0:
            return np.zeros(values.shape, dtype="uint8")
        low, high = np.percentile(valid, (2, 98))
        scaled = (np.clip(values, low, high) - low) / max(high - low, 1e-6)
        scaled[~clear_mask] = 0
        return (scaled * 255).astype("uint8")

    @staticmethod
    def _write_single(path: Path, image: np.ndarray, profile: dict[str, Any], dtype: str, nodata: float | int | None = None) -> None:
        output_profile = dict(profile)
        output_profile.update(count=1, dtype=dtype, compress="LZW", nodata=nodata)
        with rasterio.open(path, "w", **output_profile) as destination:
            destination.write(image.astype(dtype), 1)

    def _write_rgb(self, path: Path, red: np.ndarray, green: np.ndarray, blue: np.ndarray, profile: dict[str, Any]) -> None:
        output_profile = dict(profile)
        output_profile.update(count=3, dtype="uint8", compress="LZW", nodata=0)
        with rasterio.open(path, "w", **output_profile) as destination:
            destination.write(red, 1)
            destination.write(green, 2)
            destination.write(blue, 3)

    def _waterbody_geojson(self, mask: np.ndarray, profile: dict[str, Any], output_path: Path) -> int:
        features: list[dict[str, Any]] = []
        labelled = remove_small_objects(mask.astype(bool), min_size=9)
        pixel_area_m2 = abs(profile["transform"].a * profile["transform"].e)
        for geometry, value in shapes(labelled.astype("uint8"), mask=labelled, transform=profile["transform"]):
            if not value:
                continue
            if profile.get("crs"):
                geometry = transform_geom(profile["crs"], "EPSG:4326", geometry, precision=7)
            features.append(
                {
                    "type": "Feature",
                    "geometry": geometry,
                    "properties": {
                        "class": "probable_waterbody",
                        "minimum_area_m2": round(pixel_area_m2 * 9, 2),
                    },
                }
            )
        import json

        output_path.write_text(
            json.dumps({"type": "FeatureCollection", "features": features}),
            encoding="utf-8",
        )
        return len(features)

    def process(self, source_folder: Path, output_folder: Path) -> dict[str, Any]:
        missing = [band for band in self.required_bands if not (source_folder / f"{band}.tif").is_file()]
        if missing:
            raise RasterPipelineError(f"Required Sentinel-2 bands are missing: {', '.join(missing)}")

        with rasterio.open(source_folder / "B03.tif") as reference_source:
            profile = reference_source.profile.copy()
            profile.update(width=reference_source.width, height=reference_source.height, transform=reference_source.transform, crs=reference_source.crs)

        bands = {
            band: self._read_aligned(source_folder / f"{band}.tif", profile, categorical=band in {"QA60", "SCL"})
            for band in self.required_bands
        }
        qa60_clear = ((bands["QA60"].astype("uint16") & (1 << 10)) == 0) & ((bands["QA60"].astype("uint16") & (1 << 11)) == 0)
        scl_clear = np.isin(bands["SCL"], self.clear_scl_classes)
        clear_mask = qa60_clear & scl_clear

        ndwi_image = self._safe_index(ndwi(bands["B03"], bands["B08"]), clear_mask)
        mndwi_image = self._safe_index(mndwi(bands["B03"], bands["B11"]), clear_mask)
        ndvi_image = self._safe_index(ndvi(bands["B08"], bands["B04"]), clear_mask)
        mask = water_mask(np.nan_to_num(ndwi_image, nan=-1.0), threshold=0.30)
        mask[~clear_mask] = 0

        output_folder.mkdir(parents=True, exist_ok=True)
        output_paths = {
            "rgb": str(output_folder / "rgb_preview.tif"),
            "preview": str(output_folder / "rgb_preview.png"),
            "ndwi": str(output_folder / "ndwi.tif"),
            "mndwi": str(output_folder / "mndwi.tif"),
            "ndvi": str(output_folder / "ndvi.tif"),
            "water": str(output_folder / "water_mask.tif"),
            "water_mask": str(output_folder / "water_mask.tif"),
        }
        red_preview = self._rgb_channel(bands["B04"], clear_mask)
        green_preview = self._rgb_channel(bands["B03"], clear_mask)
        blue_preview = self._rgb_channel(bands["B02"], clear_mask)
        self._write_rgb(
            Path(output_paths["rgb"]),
            red_preview,
            green_preview,
            blue_preview,
            profile,
        )
        preview = np.dstack((red_preview, green_preview, blue_preview))
        preview_image = Image.fromarray(preview, mode="RGB")
        preview_image.thumbnail((1200, 1200))
        preview_image.save(output_paths["preview"], format="PNG", optimize=True)
        self._write_single(Path(output_paths["ndwi"]), ndwi_image, profile, "float32", nodata=np.nan)
        self._write_single(Path(output_paths["mndwi"]), mndwi_image, profile, "float32", nodata=np.nan)
        self._write_single(Path(output_paths["ndvi"]), ndvi_image, profile, "float32", nodata=np.nan)
        self._write_single(Path(output_paths["water"]), mask, profile, "uint8", nodata=0)
        waterbody_path = output_folder / "probable_waterbodies.geojson"
        waterbody_count = self._waterbody_geojson(mask, profile, waterbody_path)

        valid_pixels = int(clear_mask.sum())
        return {
            "outputs": output_paths,
            "waterbody_geojson": str(waterbody_path),
            "statistics": {
                "total_pixels": int(clear_mask.size),
                "clear_pixels": valid_pixels,
                "cloud_or_invalid_pixels": int(clear_mask.size - valid_pixels),
                "probable_water_pixels": int(mask.sum()),
                "probable_water_percent": round(100 * float(mask.sum()) / max(valid_pixels, 1), 2),
                "probable_waterbodies": waterbody_count,
            },
        }
