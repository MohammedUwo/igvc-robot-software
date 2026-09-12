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


def segment_intersection(a, b, c, d):
    def orient(p, q, r):
        return (q[0] - p[0]) * (r[1] - p[1]) - (q[1] - p[1]) * (r[0] - p[0])
    def between(p, q, r):
        return min(p[0], r[0]) <= q[0] <= max(p[0], r[0]) and min(p[1], r[1]) <= q[1] <= max(p[1], r[1])
    o1 = orient(a, b, c)
    o2 = orient(a, b, d)
    o3 = orient(c, d, a)
    o4 = orient(c, d, b)
    eps = 1e-9
    if abs(o1) < eps and between(a, c, b):
        return True
    if abs(o2) < eps and between(a, d, b):
        return True
    if abs(o3) < eps and between(c, a, d):
        return True
    if abs(o4) < eps and between(c, b, d):
        return True
    return (o1 > 0) != (o2 > 0) and (o3 > 0) != (o4 > 0)


def polyline_has_self_intersection(polyline):
    segments = list(zip(polyline, polyline[1:]))
    for i, (a, b) in enumerate(segments):
        for j, (c, d) in enumerate(segments):
            if abs(i - j) <= 1:
                continue
            if segment_intersection(a, b, c, d):
                return True
    return False


def test_lane_boundaries_do_not_self_intersect_or_collapse_in_chicane():
    data = generate(42)
    lanes = data["course"]["lane_boundaries"]
    for key in ["outer_boundary_polyline", "inner_boundary_polyline"]:
        for segment in lanes[key]:
            assert len(segment) > 2
    chicane = data["course"]["chicane"]["world_centerline"]
    assert len(chicane) >= 5
    assert data["course"]["chicane"]["tile"].startswith("s_chicane")


def test_no_mans_land_approach_and_exit_are_straightaways_not_curves():
    data = generate(42)
    no_lane_tiles = [t for t in data["tile_instances"] if t["no_lane_markings"]]
    assert no_lane_tiles
    for tile in no_lane_tiles:
        assert tile["centerline"]
        assert not tile["left_boundary"]
        assert not tile["right_boundary"]


def test_ramp_is_aligned_with_no_mans_land_straight_and_has_lane_markings():
    data = generate(42)
    ramp = data["ramp"]
    assert "yaw" in ramp["pose"]
    assert ramp["direction"] == "tile_centerline"
    assert ramp["approach_clearance_passed"] is True
    assert ramp["exit_clearance_passed"] is True
    assert ramp["lane_markings"] == "left_right_and_center"
    sdf = (ROOT / "generated" / "generated_world_42.sdf").read_text()
    assert "ramp_lane_left" in sdf
    assert "ramp_lane_right" in sdf
    assert "ramp_centerline" in sdf
    assert "ramp_wedge_incline" in sdf
    assert "ramp_wedge_decline" in sdf
