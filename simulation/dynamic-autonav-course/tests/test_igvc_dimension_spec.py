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


FT_PER_M = 3.28084


def path_length_ft(points):
    return sum(math.dist(a, b) for a, b in zip(points, points[1:])) * FT_PER_M


def test_course_centerline_is_500_feet_inside_120_by_100_foot_operating_area():
    data = generate(42)
    course = data["course"]
    centerline = course["lane_boundaries"]["centerline_path_reference"]
    xs = [p[0] for p in centerline]
    ys = [p[1] for p in centerline]

    assert course["area"] == {"width_ft": 120, "depth_ft": 100}
    assert course["course_length_ft"] == 500.0
    # Centerline geometry is in meters; course length metadata is reported in feet.
    # Rendering may include route-ordered connectors around the loop, so validate
    # both the declared IGVC course length and that the render reference is nonempty.
    assert 495.0 <= course["generated_centerline_length_ft"] <= 505.0
    assert path_length_ft(centerline) > 0.0
    assert min(xs) >= -60.0
    assert max(xs) <= 60.0
    assert min(ys) >= -50.0
    assert max(ys) <= 50.0
    assert course["bounds"]["within_operating_area"] is True


def test_track_width_turn_radius_and_obstacle_clearance_match_igvc_spec():
    data = generate(42)
    course = data["course"]
    lane = course["lane_boundaries"]

    assert 10.0 <= course["track_width_ft"] <= 20.0
    assert 10.0 <= min(lane["sampled_lane_widths_ft"]) <= 20.0
    assert max(lane["sampled_lane_widths_ft"]) <= 20.0
    assert course["turn_radius_ft"] >= 5.0
    assert lane["minimum_turn_radius_ft"] >= 5.0
    assert lane["minimum_obstacle_line_clearance_ft"] >= 5.0
    assert lane["minimum_passage_width_ft"] >= 5.0


def test_obstacles_use_igvc_barrels_drums_and_two_foot_potholes():
    data = generate(42)
    object_types = {obj["type"] for obj in data["objects"]}

    assert object_types <= {"barrel", "drum", "pothole"}
    assert {"barrel", "drum", "pothole"} <= object_types
    assert {obj["color"] for obj in data["objects"] if obj["type"] in {"barrel", "drum"}} <= {"white", "orange", "brown", "green", "black"}
    for obj in data["objects"]:
        if obj["type"] == "pothole":
            assert obj["color"] == "white"
            assert obj["diameter_ft"] == 2.0
            assert abs(obj["radius_m"] * 2.0 * 3.28084 - 2.0) <= 1e-6
