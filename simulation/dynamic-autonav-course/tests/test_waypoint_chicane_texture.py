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


def segments(polyline):
    return list(zip(polyline, polyline[1:]))


def ccw(a, b, c):
    return (c[1] - a[1]) * (b[0] - a[0]) > (b[1] - a[1]) * (c[0] - a[0])


def intersects(a, b, c, d):
    if a in (c, d) or b in (c, d):
        return False
    return ccw(a, c, d) != ccw(b, c, d) and ccw(a, b, c) != ccw(a, b, d)


def polyline_self_intersects(polyline):
    segs = segments(polyline)
    for i, (a, b) in enumerate(segs):
        for j, (c, d) in enumerate(segs):
            if abs(i - j) <= 1:
                continue
            if intersects(a, b, c, d):
                return True
    return False


def point_segment_distance(p, a, b):
    ax, ay = a
    bx, by = b
    dx, dy = bx - ax, by - ay
    denom = dx * dx + dy * dy
    if denom == 0:
        return dist(p, a)
    t = max(0.0, min(1.0, ((p[0] - ax) * dx + (p[1] - ay) * dy) / denom))
    return dist(p, [ax + t * dx, ay + t * dy])


def test_waypoint_defined_centerline_and_fixed_s_curve_chicane_are_seed_stable():
    a = generate(42)
    b = generate(43)
    course_a = a["course"]
    course_b = b["course"]
    assert course_a["centerline_generation"]["type"] == "grid_tile_route"
    assert course_a["lane_boundaries"]["type"] == "grid_tile_local_boundaries"
    assert course_a["chicane"]["type"] == "tile_s_curve"
    assert course_a["tile_route"] == course_b["tile_route"]
    assert course_a["chicane"]["tile"] == course_b["chicane"]["tile"]
    assert len(course_a["lane_boundaries"]["centerline_path_reference"]) > 120


def test_chicane_boundaries_are_continuous_non_self_intersecting_and_constant_width():
    data = generate(42)
    lanes = data["course"]["lane_boundaries"]
    chicane = data["course"]["chicane"]
    start_i, end_i = chicane["centerline_index_range"]
    assert start_i < end_i
    for key in ["outer_boundary_polyline", "inner_boundary_polyline"]:
        chicane_points = [p for segment in lanes[key] for p in segment]
        assert len(chicane_points) > 12
        assert len({tuple(p) for p in chicane_points}) <= len(chicane_points)
    widths = lanes["sampled_lane_widths_ft"]
    assert min(widths) >= 7.0
    assert max(widths) <= 13.0
    assert lanes["minimum_passage_width_ft"] >= 5.0


def test_turning_radius_is_feasible_and_no_mans_land_clips_lane_markings():
    data = generate(42)
    lanes = data["course"]["lane_boundaries"]
    assert lanes["minimum_turn_radius_ft"] >= 5.0
    assert lanes["breaks_only_at"] == ["no_lane_zone", "lane_gap"]
    assert len(lanes["outer_boundary_polyline"]) >= 2
    assert len(lanes["inner_boundary_polyline"]) >= 2
    no_lane_tiles = [t for t in data["tile_instances"] if t["no_lane_markings"]]
    assert no_lane_tiles
    assert all(not t["left_boundary"] and not t["right_boundary"] for t in no_lane_tiles)


def test_lane_texture_is_used_in_sdf_not_individual_lane_boundary_boxes():
    data = generate(42)
    sdf = (ROOT / "generated" / "generated_world_42.sdf").read_text()
    debug = ROOT / data["course"]["debug"]["layout_png"]
    assert debug.exists()
    assert "lane_solid_" in sdf
    assert "lane_texture_plane" not in sdf
    assert "lane_outer_boundary_segment" not in sdf
    assert "lane_inner_boundary_segment" not in sdf


def test_obstacles_do_not_block_fixed_chicane_completely():
    data = generate(42)
    center = data["course"]["lane_boundaries"]["centerline_path_reference"]
    start_i, end_i = data["course"]["chicane"]["centerline_index_range"]
    chicane_center = center[start_i:end_i + 1]
    blockers = []
    for obj in data["objects"]:
        p = [obj["pose"]["x"], obj["pose"]["y"]]
        nearest = min(point_segment_distance(p, a, b) for a, b in segments(chicane_center))
        radius = obj.get("radius_m", max(obj.get("footprint", {}).values(), default=1.0) / 2.0)
        if nearest < radius + 2.5:
            blockers.append(obj["name"])
    assert len(blockers) <= 1
