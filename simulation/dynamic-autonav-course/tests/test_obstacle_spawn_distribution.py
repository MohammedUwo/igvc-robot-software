import math
import pathlib
import subprocess
import sys

import yaml

ROOT = pathlib.Path(__file__).resolve().parents[1]


def generate(seed=42):
    subprocess.run(
        [sys.executable, "scripts/generate_course.py", "--seed", str(seed), "--scenario", "normal", "--template", "oval_with_chicane"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return yaml.safe_load((ROOT / f"generated/generated_course_{seed}.yaml").read_text())


def nearest_tile(obj, tiles):
    x, y = obj["pose"]["x"], obj["pose"]["y"]
    return min(tiles, key=lambda t: (t["origin"][0] - x) ** 2 + (t["origin"][1] - y) ** 2)


def test_obstacles_do_not_spawn_in_no_mans_land_no_lane_or_ramp_tiles():
    data = generate(42)
    forbidden = []
    for obj in data["objects"]:
        tile = nearest_tile(obj, data["tile_instances"])
        if tile["tile"].startswith("no_mans_land") or tile["tile"] == "no_lane_zone" or tile["allowed"].get("ramp"):
            forbidden.append((obj["name"], obj["type"], tile["tile"], obj["pose"]))

    assert forbidden == []


def test_obstacles_keep_five_foot_clearance_from_lane_lines_without_fallback_cluster():
    data = generate(42)
    assert data["objects"]
    for obj in data["objects"]:
        assert obj["line_clearance_ft"] >= 5.0
        assert obj.get("spawn_mode") != "fallback_display_row"

    xs = [obj["pose"]["x"] for obj in data["objects"]]
    ys = [obj["pose"]["y"] for obj in data["objects"]]
    # Distribution should use real course tiles, not collapse into the old no-lane/fallback row.
    assert max(xs) - min(xs) > 20.0
    assert max(ys) - min(ys) > 20.0
