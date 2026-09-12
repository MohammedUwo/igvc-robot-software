import math
import pathlib
import subprocess
import sys

import yaml

from scripts.tile_geometry import segments_intersect

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


def segment_lengths(points):
    return [math.dist(a, b) for a, b in zip(points, points[1:])]


def test_solid_boundary_runs_are_ordered_without_tile_crossover_jumps():
    data = generate(42)
    lanes = data["course"]["lane_boundaries"]
    for side in ["outer_boundary_polyline", "inner_boundary_polyline"]:
        for run in lanes[side]:
            lengths = segment_lengths(run)
            assert lengths
            # Adjacent painted tiles should connect through the small tile-edge gap;
            # the old broken renderer jumped backward across entire tiles (14-26 m).
            assert max(lengths) < 8.0


def _non_adjacent_self_intersections(points):
    segs = list(zip(points, points[1:]))
    hits = []
    for i, (a, b) in enumerate(segs):
        for j, (c, d) in enumerate(segs):
            if j <= i + 1:
                continue
            if segments_intersect(a, b, c, d):
                hits.append((i, j))
    return hits


def _tile_side_intersections(tile):
    hits = []
    left = tile["left_boundary"]
    right = tile["right_boundary"]
    for i, (a, b) in enumerate(zip(left, left[1:])):
        for j, (c, d) in enumerate(zip(right, right[1:])):
            if segments_intersect(a, b, c, d):
                hits.append((i, j))
    return hits


def test_lane_boundaries_do_not_self_intersect_or_cross_each_other():
    data = generate(42)
    lanes = data["course"]["lane_boundaries"]
    for key in ["outer_boundary_polyline", "inner_boundary_polyline"]:
        for run in lanes[key]:
            assert _non_adjacent_self_intersections(run) == []
    for tile in data["tile_instances"]:
        if tile["left_boundary"] and tile["right_boundary"]:
            assert _tile_side_intersections(tile) == []


def test_turns_keep_curved_multi_segment_boundaries():
    data = generate(42)
    turn_tiles = [t for t in data["tile_instances"] if t["tile"] == "gentle_left"]
    assert len(turn_tiles) == 4
    for tile in turn_tiles:
        assert len(tile["left_boundary"]) > len(tile["left_boundary_solid"])
        assert len(tile["right_boundary"]) > len(tile["right_boundary_solid"])

    sdf = (ROOT / "generated/generated_world_42.sdf").read_text()
    # Curved turn paint should be rendered with several short visuals, not one
    # straight chord per turn.
    assert sdf.count('<visual name="visual_') > data["course"]["lane_rendering"]["visual_count"] * 10
