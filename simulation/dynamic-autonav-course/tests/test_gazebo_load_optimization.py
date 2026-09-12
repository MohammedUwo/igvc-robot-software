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


def test_grid_tile_world_uses_compact_lane_rendering_for_fast_gazebo_loads():
    data = generate(42)
    sdf = (ROOT / "generated/generated_world_42.sdf").read_text()

    assert data["course"]["lane_rendering"]["mode"] == "batched_solid_tile_polylines"
    assert data["course"]["lane_rendering"]["style"] == "solid"
    assert data["course"]["lane_rendering"]["lane_model_count"] == 1
    assert data["course"]["lane_rendering"]["visual_count"] <= 8
    assert data["course"]["lane_rendering"]["input_segment_count"] > data["course"]["lane_rendering"]["visual_count"]

    assert '<model name="lane_markings">' in sdf
    assert '<model name="lane_segment_' not in sdf
    assert 'lane_solid_outer_00' in sdf  # visual names still expose continuous run identity for debugging
    assert sdf.count('<model name="') < 80
    assert sdf.count('<link name="') < 320
