"""
MozzieSpot AI v2.0
Band Extraction Module
"""

from pathlib import Path
import shutil
import rasterio
import numpy as np


class BandExtractor:

    REQUIRED_BANDS = [
        "B02",
        "B03",
        "B04",
        "B08",
        "B11",
        "B12",
        "QA60",
        "SCL"
    ]

    def __init__(self):
        pass

    def find_band(self, folder: Path, band: str):

        file = folder / f"{band}.tif"

        if file.exists():
            return file

        return None

    def validate(self, folder: Path):

        missing = []

        for band in self.REQUIRED_BANDS:

            if self.find_band(folder, band) is None:
                missing.append(band)

        return missing

    def read_band(self, path):

        with rasterio.open(path) as src:

            image = src.read(1)

            profile = src.profile

        return image, profile

    def save_band(self, image, profile, output):

        profile.update(

            compress="LZW",

            count=1

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

    def copy_required_bands(

        self,

        source,

        destination

    ):

        destination.mkdir(

            parents=True,

            exist_ok=True

        )

        for band in self.REQUIRED_BANDS:

            src = self.find_band(

                source,

                band

            )

            if src is None:

                continue

            shutil.copy(

                src,

                destination / src.name

            )

    def stack_rgb(

        self,

        folder,

        output

    ):

        red, profile = self.read_band(

            folder / "B04.tif"

        )

        green, _ = self.read_band(

            folder / "B03.tif"

        )

        blue, _ = self.read_band(

            folder / "B02.tif"

        )

        profile.update(

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

    def stack_false_color(

        self,

        folder,

        output

    ):

        nir, profile = self.read_band(

            folder/"B08.tif"

        )

        red,_ = self.read_band(

            folder/"B04.tif"

        )

        green,_ = self.read_band(

            folder/"B03.tif"

        )

        profile.update(

            count=3,

            compress="LZW"

        )

        with rasterio.open(

            output,

            "w",

            **profile

        ) as dst:

            dst.write(nir,1)

            dst.write(red,2)

            dst.write(green,3)

        return output

    def statistics(

        self,

        folder

    ):

        stats = {}

        for band in self.REQUIRED_BANDS:

            path = folder/f"{band}.tif"

            if not path.exists():

                continue

            image,_ = self.read_band(path)

            stats[band] = {

                "min": float(np.min(image)),

                "max": float(np.max(image)),

                "mean": float(np.mean(image)),

                "std": float(np.std(image))

            }

        return stats


if __name__ == "__main__":

    extractor = BandExtractor()

    folder = Path("sample")

    print(

        extractor.validate(folder)

    )