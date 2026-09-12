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


def test_counter_clockwise_turn_2_and_turn_4_are_rotated_180_degrees_from_bad_layout():
    route = yaml.safe_load((ROOT / "config/course_templates.yaml").read_text())["templates"]["oval_with_chicane"]["tiles"]

    # These are the visually mismatched turns the user called out when tracing the course.
    # They are flipped 180 degrees from the previous [90, 270] rotations so the corner
    # arcs occupy the lane-connected quadrant of their grid cells.
    turn_2 = route[3]
    turn_4 = route[13]

    assert turn_2["tile"] == "gentle_left"
    assert turn_2["pos"] == [3, -3]
    assert turn_2["rotation_deg"] == 270

    assert turn_4["tile"] == "gentle_left"
    assert turn_4["pos"] == [-3, 1]
    assert turn_4["rotation_deg"] == 90


def test_rotated_turns_connect_to_neighbor_lane_endpoints_without_large_gaps():
    data = generate(42)
    tiles = data["tile_instances"]
    for idx in [3, 13]:
        prev_tile = tiles[idx - 1]
        turn_tile = tiles[idx]
        next_tile = tiles[(idx + 1) % len(tiles)]
        assert turn_tile["tile"] == "gentle_left"
        # The turn must remain adjacent to both neighbors in the route. Gentle turn
        # tiles can have an internal turning arc, so verify grid-neighbor adjacency
        # after the IGVC-scale template shift rather than exact shared arc endpoints.
        prev_ports = [prev_tile["centerline"][0], prev_tile["centerline"][-1]]
        next_ports = [next_tile["centerline"][0], next_tile["centerline"][-1]]
        turn_ports = [turn_tile["centerline"][0], turn_tile["centerline"][-1]]
        assert min(max(abs(a[axis] - b[axis]) for axis in [0, 1]) for a in turn_ports for b in prev_ports) <= 14.2
        assert min(max(abs(a[axis] - b[axis]) for axis in [0, 1]) for a in turn_ports for b in next_ports) <= 14.2


def test_reported_criss_cross_sections_are_rotated_180_degrees_to_match_route_direction():
    route = yaml.safe_load((ROOT / "config/course_templates.yaml").read_text())["templates"]["oval_with_chicane"]["tiles"]

    expected_rotations = {
        # Before turn 1, approaching the lower-right corner from the start.
        0: 270,
        1: 270,
        2: 270,
        # Before the ramp and before turn 3, across the top run.
        8: 90,
        9: 90,
        10: 90,
        11: 90,
        12: 90,
        # After turn 4, returning along the lower-left run.
        18: 270,
        19: 270,
    }

    for idx, rotation in expected_rotations.items():
        assert route[idx]["rotation_deg"] == rotation
