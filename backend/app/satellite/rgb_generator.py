"""
MozzieSpot AI v2.0
RGB Image Generator
"""

import rasterio
import numpy as np


class RGBGenerator:

    def read(self, path):

        with rasterio.open(path) as src:

            img = src.read(1)

            profile = src.profile

        return img, profile

    def normalize(self, img):

        img = img.astype(np.float32)

        p2 = np.percentile(img, 2)

        p98 = np.percentile(img, 98)

        img = np.clip(img, p2, p98)

        img = (img - p2) / (p98 - p2 + 1e-6)

        img *= 255

        return img.astype(np.uint8)

    def generate(

        self,

        red_file,

        green_file,

        blue_file,

        output

    ):

        red, profile = self.read(red_file)

        green, _ = self.read(green_file)

        blue, _ = self.read(blue_file)

        red = self.normalize(red)

        green = self.normalize(green)

        blue = self.normalize(blue)

        profile.update(

            dtype=rasterio.uint8,

            count=3,

            compress="LZW"

        )

        with rasterio.open(

            output,

            "w",

            **profile

        ) as dst:

            dst.write(red,1)

            dst.write(green,2)

            dst.write(blue,3)

        return output