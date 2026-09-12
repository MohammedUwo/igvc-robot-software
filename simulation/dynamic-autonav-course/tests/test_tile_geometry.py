import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "scripts"))

from tile_geometry import (
    offset_centerline,
    polyline_self_intersects,
    polylines_intersect,
    rotate_point,
    sample_polyline,
    transform_point,
)


def test_rotate_and_transform_cardinal_points():
    assert rotate_point((1.0, 0.0), 90) == [0.0, 1.0]
    assert rotate_point((0.0, 1.0), -90) == [1.0, 0.0]
    assert transform_point((1.0, 0.0), (10.0, -2.0), 90) == [10.0, -1.0]


def test_sample_polyline_respects_max_spacing():
    sampled = sample_polyline([[0.0, 0.0], [0.0, 5.0]], spacing=0.75)
    assert sampled[0] == [0.0, 0.0]
    assert sampled[-1] == [0.0, 5.0]
    assert max(math.dist(a, b) for a, b in zip(sampled, sampled[1:])) <= 0.75 + 1e-6


def test_offset_centerline_produces_constant_lane_width_on_straight():
    center = sample_polyline([[0.0, -2.5], [0.0, 2.5]], spacing=0.5)
    left = offset_centerline(center, 1.5)
    right = offset_centerline(center, -1.5)
    widths = [math.dist(a, b) for a, b in zip(left, right)]
    assert min(widths) == max(widths) == 3.0
    assert left[0] == [-1.5, -2.5]
    assert right[-1] == [1.5, 2.5]


def test_chicane_offsets_do_not_self_intersect_or_cross():
    center = sample_polyline([[0, -2.5], [-0.8, -1.0], [0.8, 1.0], [0, 2.5]], spacing=0.25)
    left = offset_centerline(center, 0.6)
    right = offset_centerline(center, -0.6)
    assert not polyline_self_intersects(left)
    assert not polyline_self_intersects(right)
    assert not polylines_intersect(left, right)
