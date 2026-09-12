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


def tile_boundary_length(tile, side):
    pts = tile[side]
    return sum(math.dist(a, b) for a, b in zip(pts, pts[1:]))


def test_lane_boundaries_render_as_solid_tile_polylines_not_sample_dashes():
    data = generate(42)
    rendering = data["course"]["lane_rendering"]

    assert rendering["style"] == "solid"
    assert rendering["mode"] == "batched_solid_tile_polylines"
    assert rendering["visual_count"] == rendering["solid_polyline_count"]
    painted_runs = (
        len(data["course"]["lane_boundaries"]["outer_boundary_polyline"])
        + len(data["course"]["lane_boundaries"]["inner_boundary_polyline"])
    )
    assert rendering["visual_count"] == painted_runs
    assert rendering["visual_count"] < rendering["input_segment_count"] / 20


def test_solid_lane_visuals_cover_each_continuous_boundary_run_without_gaps():
    data = generate(42)
    sdf = (ROOT / "generated/generated_world_42.sdf").read_text()
    lanes = data["course"]["lane_boundaries"]

    for prefix, runs in [("outer", lanes["outer_boundary_polyline"]), ("inner", lanes["inner_boundary_polyline"])]:
        for i, points in enumerate(runs):
            name = f"lane_solid_{prefix}_{i:02d}"
            marker = f'<link name="{name}">'
            assert marker in sdf
            snippet = sdf[sdf.index(marker): sdf.index(f'</link>', sdf.index(marker))]
            assert snippet.count('<visual name="visual_') == len(points) - 1
            for a, b in zip(points, points[1:]):
                assert f"<size>{math.dist(a, b):.3f}" in snippet

