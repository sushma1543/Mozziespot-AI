from pathlib import Path
import os

# ===============================
# Project Directories
# ===============================

BASE_DIR = Path(__file__).resolve().parent

DATA_DIR = BASE_DIR / "data"

RAW_DIR = DATA_DIR / "raw"

PROCESSED_DIR = DATA_DIR / "processed"

OUTPUT_DIR = DATA_DIR / "output"

LOG_DIR = DATA_DIR / "logs"

CACHE_DIR = DATA_DIR / "cache"

for folder in [
    RAW_DIR,
    PROCESSED_DIR,
    OUTPUT_DIR,
    LOG_DIR,
    CACHE_DIR,
]:
    folder.mkdir(parents=True, exist_ok=True)

# ===============================
# Sentinel-2 Configuration
# ===============================

COLLECTION = "sentinel-2-l2a"

MAX_CLOUD_COVER = 15

DEFAULT_BANDS = [
    "B02",
    "B03",
    "B04",
    "B08",
    "B11",
    "B12",
]

RGB_BANDS = [
    "B04",
    "B03",
    "B02",
]

NDWI_BANDS = {
    "GREEN": "B03",
    "NIR": "B08",
}

PIXEL_SIZE = 10

DEFAULT_TIMEOUT = 120

# ===============================
# AOI Defaults
# ===============================

DEFAULT_AOI = {
    "min_lon": 80.52,
    "min_lat": 16.25,
    "max_lon": 80.72,
    "max_lat": 16.45,
}

# ===============================
# API
# ===============================

COPERNICUS_STAC = os.getenv(
    "COPERNICUS_STAC_URL",
    "https://stac.dataspace.copernicus.eu/v1",
)

AWS_STAC = os.getenv(
    "AWS_SENTINEL_STAC_URL",
    "https://earth-search.aws.element84.com/v1",
)

STAC_URL = os.getenv("STAC_URL", COPERNICUS_STAC)

# ===============================
# Logging
# ===============================

LOG_LEVEL = "INFO"

LOG_FILE = LOG_DIR / "satellite.log"

# ===============================
# Image Formats
# ===============================

OUTPUT_FORMAT = "GTiff"

COMPRESS = "LZW"

# ===============================
# Cloud Mask
# ===============================

USE_QA60 = True

USE_SCL = True

# ===============================
# RGB Stretch
# ===============================

RGB_MIN = 0

RGB_MAX = 3000

# ===============================
# Export
# ===============================

EXPORT_RGB = True

EXPORT_NDWI = True

EXPORT_BANDS = True

EXPORT_MASK = True
