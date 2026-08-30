"""
MozzieSpot AI v2.0
Cloud Masking Module

Supports:
- QA60 cloud masking
- Scene Classification Layer (SCL)
"""

import numpy as np
import rasterio

from pathlib import Path

# ------------------------------------
# SCL Classes
# ------------------------------------

CLEAR_CLASSES = [

    4,   # Vegetation
    5,   # Bare Soil
    6,   # Water

]

CLOUD_CLASSES = [

    3,   # Cloud Shadow
    8,   # Medium Cloud
    9,   # High Cloud
    10,  # Thin Cirrus
    11   # Snow

]

# ------------------------------------
# Cloud Mask Class
# ------------------------------------


class CloudMask:

    def __init__(self):

        pass

    # -----------------------------

    def read_band(self, path):

        with rasterio.open(path) as src:

            image = src.read(1)

            profile = src.profile

        return image, profile

    # -----------------------------

    def qa60_mask(self, qa60):

        cloud = ((qa60 & (1 << 10)) != 0)

        cirrus = ((qa60 & (1 << 11)) != 0)

        mask = ~(cloud | cirrus)

        return mask.astype(np.uint8)

    # -----------------------------

    def scl_mask(self, scl):

        mask = np.isin(

            scl,

            CLEAR_CLASSES

        )

        return mask.astype(np.uint8)

    # -----------------------------

    def combine_masks(

        self,

        qa_mask,

        scl_mask

    ):

        return (

            qa_mask & scl_mask

        ).astype(np.uint8)

    # -----------------------------

    def apply_mask(

        self,

        image,

        mask

    ):

        result = image.copy()

        result[mask == 0] = 0

        return result

    # -----------------------------

    def save_image(

        self,

        image,

        profile,

        output

    ):

        profile.update(

            dtype=rasterio.uint16,

            count=1,

            compress="LZW"

        )

        with rasterio.open(

            output,

            "w",

            **profile

        ) as dst:

            dst.write(

                image,

                1

            )

    # -----------------------------

    def process(

        self,

        image_path,

        qa60_path,

        scl_path,

        output_path

    ):

        image, profile = self.read_band(

            image_path

        )

        qa60, _ = self.read_band(

            qa60_path

        )

        scl, _ = self.read_band(

            scl_path

        )

        qa_mask = self.qa60_mask(

            qa60

        )

        scl_mask = self.scl_mask(

            scl

        )

        final_mask = self.combine_masks(

            qa_mask,

            scl_mask

        )

        result = self.apply_mask(

            image,

            final_mask

        )

        self.save_image(

            result,

            profile,

            output_path

        )

        return output_path


# ------------------------------------
# Example
# ------------------------------------

if __name__ == "__main__":

    processor = CloudMask()

    processor.process(

        "B04.tif",

        "QA60.tif",

        "SCL.tif",

        "B04_cloudfree.tif"

    )