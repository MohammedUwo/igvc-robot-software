import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from lane_features import (
    MASKS,
    LaneSegmentAdapter,
    build_lane_gates,
    column_centers,
    generate_virtual_progress_gates,
    has_crossed_gate,
    mask_has_required_clearance,
    mask_to_lateral_offset,
    obstacle_pose_for_tile,
    place_legal_obstacles,
    tile_lane_segments,
)


def straight_segment(width_ft=10.0, length_ft=30.0):
    return {
        "id": "straight_00",
        "type": "straight",
        "width_ft": width_ft,
        "length_ft": length_ft,
        "centerline_points": [[0.0, 0.0], [length_ft, 0.0]],
        "left_boundary_points": [[0.0, width_ft / 2], [length_ft, width_ft / 2]],
        "right_boundary_points": [[0.0, -width_ft / 2], [length_ft, -width_ft / 2]],
    }


def test_lane_tiler_splits_segments_into_5ft_lane_relative_tiles():
    tiles = tile_lane_segments([straight_segment()], tile_length_ft=5, obstacle_columns=6)

    assert len(tiles) == 6
    assert tiles[0] == {
        "id": "tile_000",
        "segment_id": "straight_00",
        "s_start_ft": 0.0,
        "s_end_ft": 5.0,
        "s_center_ft": 2.5,
        "width_ft": 10.0,
        "obstacle_columns": 6,
        "obstacle_mask": "000000",
        "obstacle_type": None,
    }
    assert tiles[-1]["s_start_ft"] == 25.0
    assert tiles[-1]["s_end_ft"] == 30.0


def test_mask_columns_offsets_and_dynamic_clearance_validation():
    assert MASKS["left_2"] == "110000"
    assert [round(v, 3) for v in column_centers(10.0, 6)] == [4.167, 2.5, 0.833, -0.833, -2.5, -4.167]
    assert round(mask_to_lateral_offset("110000", 10.0), 3) == 3.333

    assert mask_has_required_clearance("110000", 10.0)
    assert mask_has_required_clearance("000111", 10.0)
    assert not mask_has_required_clearance("001100", 10.0)
    assert not mask_has_required_clearance("011110", 10.0)
    assert not mask_has_required_clearance("111111", 10.0)
    assert mask_has_required_clearance("001100", 20.0)
    assert not mask_has_required_clearance("011110", 20.0)


def test_obstacle_world_pose_uses_segment_pose_normal_and_tile_center():
    seg = straight_segment(width_ft=10.0)
    adapter = LaneSegmentAdapter([seg])
    tile = tile_lane_segments([seg])[0]

    pose = obstacle_pose_for_tile(tile, "110000", adapter)

    assert pose["s_ft"] == 2.5
    assert round(pose["lane_relative"]["d_ft"], 3) == 3.333
    assert pose["world_pose_ft"] == {"x": 2.5, "y": 3.333, "heading_deg": 0.0}


def test_random_legal_obstacle_placement_rejects_center_and_full_masks_for_10ft_lane():
    seg = straight_segment(width_ft=10.0, length_ft=120.0)
    tiles = tile_lane_segments([seg])
    obstacles = place_legal_obstacles(
        tiles,
        LaneSegmentAdapter([seg]),
        seed=7,
        probability_per_tile=1.0,
        min_spacing_ft=25.0,
        avoid_start_distance_ft=0.0,
        avoid_finish_distance_ft=0.0,
        avoid_ramp_distance_ft=0.0,
    )

    assert obstacles
    for obs in obstacles:
        assert obs["mask"] in {"110000", "000011", "111000", "000111"}
        assert obs["mask"] not in {"001100", "011110", "111111"}
        assert obs["footprint"]["type"] in {"circle", "rectangle"}
        assert "world_pose_ft" in obs
        assert "lane_relative" in obs


def test_lane_gates_and_crossing_helper_use_gate_normal_not_tiny_thresholds():
    seg = straight_segment(width_ft=10.0, length_ft=60.0)
    adapter = LaneSegmentAdapter([seg])
    gates = build_lane_gates(adapter, [{"id": "gate_001", "segment_id": "straight_00", "s_ft": 25.0, "next_mode": "lane_follow"}])

    gate = gates[0]
    assert gate["type"] == "lane_gate"
    assert gate["center_ft"] == [25.0, 0.0]
    assert gate["left_post_ft"] == [25.0, 5.0]
    assert gate["right_post_ft"] == [25.0, -5.0]
    assert gate["normal_ft"] == [1.0, 0.0]
    assert has_crossed_gate([24.0, 4.5], [25.2, 4.5], gate)
    assert not has_crossed_gate([25.2, 4.5], [24.0, 4.5], gate)


def test_virtual_progress_gates_are_spaced_and_avoid_obstacle_tiles():
    seg = straight_segment(width_ft=10.0, length_ft=80.0)
    adapter = LaneSegmentAdapter([seg])
    tiles = tile_lane_segments([seg])
    tiles[4]["obstacle_mask"] = "110000"  # centered at s=22.5; gate at 20 would intersect/overlap this tile

    gates = generate_virtual_progress_gates(adapter, tiles, spacing_ft=20.0)

    s_values = [g["s_ft"] for g in gates]
    assert 20.0 not in s_values
    assert 40.0 in s_values
    assert all(g["next_mode"] == "lane_follow" for g in gates)
