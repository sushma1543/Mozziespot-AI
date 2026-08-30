from pathlib import Path

import numpy as np
import rasterio
from rasterio.transform import from_origin

from app.satellite.raster_pipeline import SentinelRasterPipeline


def _write_band(path: Path, data: np.ndarray, transform, crs="EPSG:32644") -> None:
    with rasterio.open(
        path,
        "w",
        driver="GTiff",
        height=data.shape[0],
        width=data.shape[1],
        count=1,
        dtype=data.dtype,
        transform=transform,
        crs=crs,
    ) as dataset:
        dataset.write(data, 1)


def test_pipeline_aligns_bands_masks_clouds_and_writes_products(tmp_path: Path):
    source = tmp_path / "scene"
    output = tmp_path / "output"
    source.mkdir()
    transform_10m = from_origin(500000, 1800040, 10, 10)
    transform_20m = from_origin(500000, 1800040, 20, 20)

    # A 3x3 water patch has high green and low NIR, which must survive the
    # minimum-size filter. QA60 and SCL each invalidate one different pixel.
    green = np.full((4, 4), 500, dtype="uint16")
    green[1:4, 1:4] = 2200
    red = np.full((4, 4), 600, dtype="uint16")
    blue = np.full((4, 4), 400, dtype="uint16")
    nir = np.full((4, 4), 1500, dtype="uint16")
    nir[1:4, 1:4] = 400
    qa60 = np.zeros((4, 4), dtype="uint16")
    qa60[0, 0] = 1 << 10
    scl = np.full((4, 4), 6, dtype="uint8")
    scl[0, 1] = 9
    swir = np.full((2, 2), 700, dtype="uint16")

    for name, data, transform in [
        ("B02", blue, transform_10m),
        ("B03", green, transform_10m),
        ("B04", red, transform_10m),
        ("B08", nir, transform_10m),
        ("B11", swir, transform_20m),
        ("B12", swir, transform_20m),
        ("QA60", qa60, transform_10m),
        ("SCL", scl, transform_10m),
    ]:
        _write_band(source / f"{name}.tif", data, transform)

    result = SentinelRasterPipeline().process(source, output)

    for path in result["outputs"].values():
        assert Path(path).is_file()
    assert Path(result["waterbody_geojson"]).is_file()
    assert result["statistics"]["clear_pixels"] == 14
    assert result["statistics"]["probable_water_pixels"] >= 7
    assert result["statistics"]["probable_waterbodies"] >= 1

