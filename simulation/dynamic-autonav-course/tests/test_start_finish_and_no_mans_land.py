import math
import pathlib
import re
import subprocess
import sys

import yaml

ROOT = pathlib.Path(__file__).resolve().parents[1]


def generate(seed=42):
    subprocess.run(
        [
            sys.executable,
            "scripts/generate_course.py",
            "--seed",
            str(seed),
            "--scenario",
            "normal",
            "--template",
            "oval_with_chicane",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return yaml.safe_load((ROOT / f"generated/generated_course_{seed}.yaml").read_text())


def _model_block(sdf, model_name):
    marker = f'<model name="{model_name}">'
    assert marker in sdf
    start = sdf.index(marker)
    end = sdf.index("</model>", start)
    return sdf[start:end]


def _pose(block):
    match = re.search(r"<pose>([^<]+)</pose>", block)
    assert match
    return [float(v) for v in match.group(1).split()]


def _box_size(block):
    match = re.search(r"<box><size>([^<]+)</size></box>", block)
    assert match
    return [float(v) for v in match.group(1).split()]


def test_grid_tile_sdf_contains_visible_start_finish_line_at_course_start():
    data = generate(42)
    sdf = (ROOT / "generated/generated_world_42.sdf").read_text()

    block = _model_block(sdf, "lane_start_finish")
    pose = _pose(block)
    size = _box_size(block)
    start = data["course"]["start_finish"]

    assert abs(pose[0] - start["x_m"]) < 0.01
    assert abs(pose[1] - start["y_m"]) < 0.01
    assert abs(abs(pose[5]) - math.pi / 2.0) < 0.01
    assert size[0] >= data["course"]["lane_width_m"]
    assert size[1] >= 0.4
    assert "1 1 0 1" in block


def test_no_mans_land_marker_is_shrunk_25_percent_from_generated_cutout():
    data = generate(42)
    sdf = (ROOT / "generated/generated_world_42.sdf").read_text()
    cutout = data["course"]["no_mans_land_cutout"]
    block = _model_block(sdf, "no_mans_land_marker")
    pose = _pose(block)
    size = _box_size(block)

    expected_width = cutout["max_x"] - cutout["min_x"]
    expected_length = cutout["max_y"] - cutout["min_y"]
    expected_x = (cutout["min_x"] + cutout["max_x"]) / 2
    expected_y = (cutout["min_y"] + cutout["max_y"]) / 2

    assert abs(size[0] - expected_width * 0.75) < 0.01
    assert abs(size[1] - expected_length * 0.75) < 0.01
    assert expected_width > 36.0
    assert abs(pose[0] - expected_x) < 0.01
    assert abs(pose[1] - expected_y) < 0.01


def test_no_mans_land_gap_stops_only_inside_no_lane_zone_not_one_tile_early():
    data = generate(42)

    tiles_by_name = {tile["tile"]: tile for tile in data["tile_instances"]}

    for name in ["no_mans_land_entry", "no_mans_land_exit", "ramp_straight"]:
        assert len(tiles_by_name[name]["left_boundary"]) > 2
        assert len(tiles_by_name[name]["right_boundary"]) > 2

    assert tiles_by_name["no_lane_zone"]["left_boundary"] == []
    assert tiles_by_name["no_lane_zone"]["right_boundary"] == []
