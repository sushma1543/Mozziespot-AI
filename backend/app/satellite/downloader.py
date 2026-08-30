"""
MozzieSpot AI v2.0
Sentinel-2 Downloader

Downloads Sentinel-2 Level-2A imagery using the STAC API.
"""

import logging
import time
from pathlib import Path
from typing import List, Optional

import requests
from pystac_client import Client

from .config import (
    STAC_URL,
    COLLECTION,
    RAW_DIR,
    DEFAULT_BANDS,
    MAX_CLOUD_COVER,
)

# ---------------------------------------------------
# Logging
# ---------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------
# Sentinel Downloader
# ---------------------------------------------------

class SentinelDownloader:

    def __init__(self):

        logger.info("Connecting to STAC Catalog...")

        self.catalog = Client.open(STAC_URL)

        logger.info("Connected Successfully")

    # ------------------------------------------------

    def search_images(
        self,
        bbox: list,
        start_date: str,
        end_date: str,
        cloud_cover: int = MAX_CLOUD_COVER
    ):

        logger.info("Searching Sentinel-2 Images...")

        search = self.catalog.search(

            collections=[COLLECTION],

            bbox=bbox,

            datetime=f"{start_date}/{end_date}",

            query={
                "eo:cloud_cover": {
                    "lt": cloud_cover
                }
            }

        )

        items = list(search.items())

        logger.info("Found %d images", len(items))

        return items

    # ------------------------------------------------

    def print_results(self, items):

        print("\n" + "=" * 70)
        print("Available Sentinel Images")
        print("=" * 70)

        for index, item in enumerate(items, start=1):

            print(f"\nImage {index}")

            print(f"ID           : {item.id}")

            print(f"Date         : {item.datetime}")

            print(
                f"Cloud Cover  : {item.properties.get('eo:cloud_cover')} %"
            )

    # ------------------------------------------------

    def choose_latest(self, items):

        if len(items) == 0:
            return None

        items.sort(
            key=lambda x: x.datetime,
            reverse=True
        )

        latest = items[0]

        logger.info("Latest image selected : %s", latest.id)

        return latest
        # ------------------------------------------------
    # Download a single band
    # ------------------------------------------------

    def download_band(
        self,
        asset,
        output_path: Path,
        retries: int = 3
    ):

        url = asset.href

        logger.info("Downloading %s", output_path.name)

        for attempt in range(1, retries + 1):

            try:

                response = requests.get(
                    url,
                    stream=True,
                    timeout=120
                )

                response.raise_for_status()

                total_size = int(
                    response.headers.get("content-length", 0)
                )

                downloaded = 0

                with open(output_path, "wb") as file:

                    for chunk in response.iter_content(
                        chunk_size=8192
                    ):

                        if not chunk:
                            continue

                        file.write(chunk)

                        downloaded += len(chunk)

                        if total_size > 0:

                            percent = (
                                downloaded / total_size
                            ) * 100

                            print(
                                f"\r{output_path.name}: "
                                f"{percent:5.1f}%",
                                end=""
                            )

                print()

                logger.info(
                    "%s downloaded successfully.",
                    output_path.name
                )

                return output_path

            except Exception as error:

                logger.warning(
                    "Attempt %d failed for %s",
                    attempt,
                    output_path.name
                )

                logger.warning(str(error))

                time.sleep(2)

        raise RuntimeError(
            f"Unable to download {output_path.name}"
        )

    # ------------------------------------------------
    # Download all required bands
    # ------------------------------------------------

    def download_all_bands(self, item):

        folder = RAW_DIR / item.id

        folder.mkdir(
            parents=True,
            exist_ok=True
        )

        bands = DEFAULT_BANDS + [
            "SCL",
            "QA60"
        ]

        logger.info(
            "Downloading %d bands...",
            len(bands)
        )

        for band in bands:

            if band not in item.assets:

                logger.warning(
                    "Band %s not found.",
                    band
                )

                continue

            asset = item.assets[band]

            output_file = folder / f"{band}.tif"

            self.download_band(
                asset,
                output_file
            )

        logger.info("All downloads completed.")

        return folder
        # ------------------------------------------------
    # Save image metadata
    # ------------------------------------------------

    def save_metadata(self, item, folder):

        metadata_file = folder / "metadata.txt"

        with open(metadata_file, "w") as f:

            f.write("MozzieSpot AI v2.0\n")
            f.write("=============================\n\n")

            f.write(f"Image ID: {item.id}\n")
            f.write(f"Date: {item.datetime}\n")
            f.write(
                f"Cloud Cover: {item.properties.get('eo:cloud_cover')}%\n"
            )

            f.write("\nDownloaded Bands:\n")

            for asset in item.assets.keys():

                f.write(f"- {asset}\n")

        logger.info("Metadata saved.")

    # ------------------------------------------------
    # Main Pipeline
    # ------------------------------------------------

    def run(
        self,
        bbox,
        start_date,
        end_date
    ):

        logger.info("Starting Download Pipeline")

        images = self.search_images(

            bbox,

            start_date,

            end_date,

            MAX_CLOUD_COVER

        )

        if len(images) == 0:

            logger.warning("No Sentinel-2 Images Found")

            return None

        self.print_results(images)

        latest = self.choose_latest(images)

        if latest is None:

            logger.error("Unable to select image")

            return None

        folder = self.download_all_bands(latest)

        self.save_metadata(

            latest,

            folder

        )

        logger.info("Pipeline Finished Successfully")

        logger.info("Files saved in %s", folder)

        return folder
    # ---------------------------------------------------
# Run Standalone
# ---------------------------------------------------

if __name__ == "__main__":

    from .config import DEFAULT_AOI

    downloader = SentinelDownloader()

    bbox = [

        DEFAULT_AOI["min_lon"],

        DEFAULT_AOI["min_lat"],

        DEFAULT_AOI["max_lon"],

        DEFAULT_AOI["max_lat"]

    ]

    downloader.run(

        bbox=bbox,

        start_date="2025-01-01",

        end_date="2025-12-31"

    )