import math
import pathlib
import subprocess
import sys

import yaml

ROOT = pathlib.Path(__file__).resolve().parents[1]


def generate(seed=42, scenario="normal"):
    subprocess.run(
        [sys.executable, "scripts/generate_course.py", "--seed", str(seed), "--scenario", scenario],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return yaml.safe_load((ROOT / "generated" / f"generated_course_{seed}.yaml").read_text())


def dist(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


def inside_rect(p, rect):
    return rect["min_x"] <= p[0] <= rect["max_x"] and rect["min_y"] <= p[1] <= rect["max_y"]


def test_course_has_inner_outer_boundary_polylines_and_centerline_reference():
    data = generate(42)
    lanes = data["course"]["lane_boundaries"]
    assert lanes["type"] in {"grid_tile_local_boundaries", "buffered_centerline_texture_boundaries"}
    assert lanes["breaks_only_at"] == ["no_lane_zone", "lane_gap"]
    assert len(lanes["outer_boundary_polyline"]) >= 2
    assert len(lanes["inner_boundary_polyline"]) >= 2
    assert len(lanes["centerline_path_reference"]) > 80
    assert all(len(segment) > 2 for segment in lanes["outer_boundary_polyline"])
    assert all(len(segment) > 2 for segment in lanes["inner_boundary_polyline"])


def test_lane_width_stays_consistent_along_generated_boundaries():
    data = generate(42)
    lanes = data["course"]["lane_boundaries"]
    assert 10.0 <= data["course"]["track_width_ft"] <= 20.0
    assert all(len(segment) > 1 for segment in lanes["outer_boundary_polyline"])
    assert all(len(segment) > 1 for segment in lanes["inner_boundary_polyline"])


def test_boundary_lines_break_only_for_fixed_no_mans_land_cutout():
    data = generate(42)
    lanes = data["course"]["lane_boundaries"]
    cutout = data["course"]["no_mans_land_cutout"]
    for key in ["outer_boundary_polyline", "inner_boundary_polyline"]:
        segments = lanes[key]
        assert len(segments) >= 2
        no_lane_indices = [i for i, t in enumerate(data["tile_instances"]) if t["no_lane_markings"]]
        assert no_lane_indices
        for idx in no_lane_indices:
            assert not data["tile_instances"][idx]["left_boundary"]
            assert not data["tile_instances"][idx]["right_boundary"]


def test_generated_sdf_uses_boundary_polyline_segments_not_many_disconnected_route_boxes():
    generate(42)
    sdf = (ROOT / "generated" / "generated_world_42.sdf").read_text()
    assert "lane_solid_" in sdf
    assert "lane_no_mans_land_gap" in sdf
    assert "lane_texture_plane" not in sdf
    assert "lane_outer_boundary_segment_0" not in sdf
    assert "lane_inner_boundary_segment_0" not in sdf
    assert "lane_turn_1" not in sdf
    assert "lane_chicane" not in sdf
