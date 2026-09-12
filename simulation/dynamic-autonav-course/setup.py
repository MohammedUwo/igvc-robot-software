from glob import glob
from pathlib import Path

from setuptools import setup

package_name = "igvc_sim"


def model_files():
    files = []
    for path in Path("models").glob("*/*"):
        if path.is_file():
            files.append(str(path))
    return files


setup(
    name=package_name,
    version="0.1.0",
    packages=[],
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/igvc_sim"]),
        ("share/" + package_name, ["package.xml", "README.md"]),
        ("share/" + package_name + "/launch", glob("launch/*.launch.py")),
        ("share/" + package_name + "/config", glob("config/*.yaml")),
        ("share/" + package_name + "/scripts", glob("scripts/*.py")),
        ("share/" + package_name + "/worlds", glob("worlds/*.sdf")),
        *[("share/" + package_name + "/" + str(Path(f).parent), [f]) for f in model_files()],
    ],
)
