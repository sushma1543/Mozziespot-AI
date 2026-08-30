"""
MozzieSpot AI v2.0
Image Preprocessing
"""

import numpy as np
import rasterio


class ImagePreprocessor:

    def normalize(self, image):

        image = image.astype(np.float32)

        image = (image-image.min())/(image.max()-image.min()+1e-6)

        return image

    def clip(self, image, minimum=0, maximum=3000):

        return np.clip(

            image,

            minimum,

            maximum

        )

    def stretch(self, image):

        image=self.normalize(image)

        image*=255

        return image.astype(np.uint8)

    def preprocess(self, input_file, output_file):

        with rasterio.open(input_file) as src:

            image=src.read(1)

            profile=src.profile

        image=self.clip(image)

        image=self.stretch(image)

        profile.update(

            dtype=rasterio.uint8,

            compress="LZW"

        )

        with rasterio.open(

            output_file,

            "w",

            **profile

        ) as dst:

            dst.write(image,1)

        return output_file