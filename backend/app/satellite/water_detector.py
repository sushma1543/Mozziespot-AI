"""
MozzieSpot AI v2.0
Water Detection Module
"""

import rasterio
import numpy as np


class WaterDetector:

    def __init__(self, threshold=0.2):

        self.threshold = threshold

    def read_band(self, path):

        with rasterio.open(path) as src:

            image = src.read(1).astype(np.float32)

            profile = src.profile

        return image, profile

    def calculate_ndwi(self, green, nir):

        return (green - nir) / (green + nir + 1e-6)

    def detect(self, ndwi):

        return (ndwi > self.threshold).astype(np.uint8)

    def save(self, mask, profile, output):

        profile.update(

            dtype=rasterio.uint8,

            compress="LZW"

        )

        with rasterio.open(

            output,

            "w",

            **profile

        ) as dst:

            dst.write(mask, 1)

    def process(

        self,

        green_band,

        nir_band,

        output

    ):

        green, profile = self.read_band(

            green_band

        )

        nir, _ = self.read_band(

            nir_band

        )

        ndwi = self.calculate_ndwi(

            green,

            nir

        )

        mask = self.detect(

            ndwi

        )

        self.save(

            mask,

            profile,

            output

        )

        return output