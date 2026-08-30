"""
Utilities
"""

from pathlib import Path
import json


def ensure_directory(path):

    Path(path).mkdir(

        parents=True,

        exist_ok=True

    )


def save_json(data,output):

    with open(output,"w") as f:

        json.dump(

            data,

            f,

            indent=4

        )


def read_json(path):

    with open(path) as f:

        return json.load(f)


def image_exists(path):

    return Path(path).exists()