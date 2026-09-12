import json
import pathlib
import subprocess
import sys

import yaml

ROOT = pathlib.Path(__file__).resolve().parents[1]


def test_tile_library_contains_minimum_useful_tile_set():
    data = yaml.safe_load((ROOT / "config" / "tile_library.yaml").read_text())
    required = {
        "straight",
        "gentle_left",
        "gentle_right",
        "hard_left",
        "hard_right",
        "s_chicane_left_right",
        "s_chicane_right_left",
        "lane_gap",
        "no_mans_land_entry",
        "no_mans_land_exit",
        "no_lane_zone",
        "ramp_zone",
        "obstacle_zone",
    }
    assert required <= set(data["tiles"])
    for name, tile in data["tiles"].items():
        assert "entry_side" in tile
        assert "exit_side" in tile
        assert "entry_heading" in tile
        assert "exit_heading" in tile
        assert "centerline" in tile
        assert "allowed" in tile


def test_template_route_uses_grid_tiles_and_fixed_chicane():
    data = yaml.safe_load((ROOT / "config" / "course_templates.yaml").read_text())
    route = data["templates"]["oval_with_chicane"]["tiles"]
    assert any(t["tile"] == "s_chicane_left_right" for t in route)
    assert any(t["tile"] == "no_lane_zone" for t in route)
    assert any(t["tile"] == "ramp_straight" for t in route)
    positions = [tuple(t["pos"]) for t in route]
    assert len(positions) == len(set(positions))


def test_generator_exports_tile_debug_artifacts_and_lane_segment_sdf():
    subprocess.run(
        [sys.executable, "scripts/generate_course.py", "--seed", "42", "--scenario", "normal", "--template", "oval_with_chicane"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    meta = yaml.safe_load((ROOT / "generated" / "generated_course_42.yaml").read_text())
    debug = json.loads((ROOT / "generated" / "debug" / "generated_layout.json").read_text())
    sdf = (ROOT / "generated" / "generated_world_42.sdf").read_text()
    assert meta["course"]["generation_mode"] == "grid_tiles"
    assert meta["course"]["template"] == "oval_with_chicane"
    assert meta["course"]["chicane"]["tile"] == "s_chicane_left_right"
    assert debug["template"] == "oval_with_chicane"
    assert (ROOT / "generated" / "debug" / "generated_layout.png").exists()
    assert "lane_solid_" in sdf
    assert "lane_texture_plane" not in sdf


def test_seed_stability_keeps_tile_route_and_changes_obstacles_only():
    for seed in [42, 43]:
        subprocess.run(
            [sys.executable, "scripts/generate_course.py", "--seed", str(seed), "--scenario", "normal", "--template", "oval_with_chicane"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
    a = yaml.safe_load((ROOT / "generated" / "generated_course_42.yaml").read_text())
    b = yaml.safe_load((ROOT / "generated" / "generated_course_43.yaml").read_text())
    assert a["course"]["tile_route"] == b["course"]["tile_route"]
    assert a["course"]["chicane"]["world_centerline"] == b["course"]["chicane"]["world_centerline"]
    assert a["objects"] != b["objects"]


def test_no_mans_land_has_no_lane_markings_and_obstacles_keep_5ft_passage():
    subprocess.run(
        [sys.executable, "scripts/generate_course.py", "--seed", "42", "--scenario", "normal", "--template", "oval_with_chicane"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    meta = yaml.safe_load((ROOT / "generated" / "generated_course_42.yaml").read_text())
    lanes = meta["course"]["lane_boundaries"]
    assert lanes["minimum_passage_width_ft"] >= 5.0
    assert meta["course"]["validation"]["no_lane_zone_has_no_markings"] is True
    assert meta["course"]["validation"]["obstacles_do_not_block_chicane"] is True
    assert meta["course"]["validation"]["ramp_not_inside_chicane"] is True
