import json
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
        text=True,
        capture_output=True,
    )
    return yaml.safe_load((ROOT / f"generated/generated_course_{seed}.yaml").read_text())


def test_ramp_feature_is_single_tile_feature_on_ramp_capable_straight_tile():
    data = generate(42)
    ramp = data["ramp"]
    features = [f for f in data["features"] if f["type"] == "ramp"]

    assert len(features) == 1
    assert ramp["feature_type"] == "ramp_tile_feature"
    assert ramp["tile"] == "ramp_straight"
    assert ramp["tile_allows_ramp"] is True
    assert ramp["tile_is_straight"] is True
    assert ramp["tile_index"] == features[0]["tile_index"]


def test_ramp_pose_inherits_tile_centerline_and_rotation():
    data = generate(42)
    ramp = data["ramp"]
    tile = next(t for t in data["tile_instances"] if t["index"] == ramp["tile_index"])

    assert ramp["pose"]["x"] == tile["origin"][0]
    assert ramp["pose"]["y"] == tile["origin"][1]
    assert ramp["pose"]["yaw"] == tile["rotation_rad"]
    assert ramp["alignment"] == "tile_centerline"
    assert ramp["inherits_tile_rotation"] is True


def test_ramp_clearance_zone_has_no_obstacles():
    data = generate(42)
    ramp = data["ramp"]
    clearance = ramp["clearance_zone"]
    assert ramp["clearance_obstacle_count"] == 0
    assert ramp["clearance_passed"] is True
    assert clearance["length_m"] > ramp["size_m"]["length"]
    assert clearance["width_m"] > ramp["size_m"]["width"]


def test_ramp_sdf_has_visible_lane_markings_on_both_sides():
    generate(42)
    sdf = (ROOT / "generated/generated_world_42.sdf").read_text()

    assert sdf.count('model name="ramp_tile_feature_') == 1
    assert 'visual name="ramp_lane_left_incline"' in sdf
    assert 'visual name="ramp_lane_left_decline"' in sdf
    assert 'visual name="ramp_lane_right_incline"' in sdf
    assert 'visual name="ramp_lane_right_decline"' in sdf
    assert 'visual name="ramp_centerline_incline"' in sdf
    assert 'visual name="ramp_centerline_decline"' in sdf
    assert 'ramp_tile_feature_' in sdf


def _visual_pose(sdf, visual_name):
    match = re.search(rf'<visual name="{visual_name}"><pose>([^<]+)</pose>', sdf)
    assert match, f"missing pose for {visual_name}"
    return [float(v) for v in match.group(1).split()]


def test_ramp_lane_markings_follow_incline_and_decline_surfaces():
    generate(42)
    sdf = (ROOT / "generated/generated_world_42.sdf").read_text()
    pitch = math.atan2(1.0, 8.0)

    for visual_name in [
        "ramp_lane_left_incline",
        "ramp_lane_right_incline",
        "ramp_centerline_incline",
    ]:
        pose = _visual_pose(sdf, visual_name)
        assert abs(pose[3] - pitch) < 1e-6
        assert pose[2] < 1.0

    for visual_name in [
        "ramp_lane_left_decline",
        "ramp_lane_right_decline",
        "ramp_centerline_decline",
    ]:
        pose = _visual_pose(sdf, visual_name)
        assert abs(pose[3] + pitch) < 1e-6
        assert pose[2] < 1.0

    assert 'visual name="ramp_lane_left"><pose>' not in sdf
    assert 'visual name="ramp_lane_right"><pose>' not in sdf
    assert 'visual name="ramp_centerline"><pose>' not in sdf


def test_debug_layout_exports_ramp_feature_metadata():
    data = generate(42)
    debug = json.loads((ROOT / data["course"]["debug"]["layout_json"]).read_text())
    ramp_features = [f for f in debug["features"] if f["type"] == "ramp"]
    assert len(ramp_features) == 1
    assert ramp_features[0]["tile"] == "ramp_straight"
    assert ramp_features[0]["clearance_passed"] is True
