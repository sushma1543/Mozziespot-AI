"""
NDWI Calculator
"""

import numpy as np
import rasterio


class NDWI:

    def read(self,path):

        with rasterio.open(path) as src:

            image = src.read(1).astype(np.float32)

            profile = src.profile

        return image, profile

    def calculate(

        self,

        green,

        nir

    ):

        ndwi = (green-nir)/(green+nir+1e-6)

        return ndwi

    def save(

        self,

        ndwi,

        profile,

        output

    ):

        profile.update(

            dtype=rasterio.float32,

            compress="LZW"

        )

        with rasterio.open(

            output,

            "w",

            **profile

        ) as dst:

            dst.write(

                ndwi.astype(np.float32),

                1

            )

    def process(

        self,

        green_file,

        nir_file,

        output

    ):

        green, profile = self.read(

            green_file

        )

        nir,_ = self.read(

            nir_file

        )

        ndwi = self.calculate(

            green,

            nir

        )

        self.save(

            ndwi,

            profile,

            output

        )

        return output