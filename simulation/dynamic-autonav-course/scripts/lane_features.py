import math
import random
from bisect import bisect_right

FT_PER_M = 3.28084

MASKS = {
    "empty": "000000",
    "left_2": "110000",
    "center_2": "001100",
    "right_2": "000011",
    "left_3": "111000",
    "center_4": "011110",
    "right_3": "000111",
    "full_block": "111111",
}

OBSTACLE_MODELS = {
    "construction_barrel": {
        "footprint_type": "circle",
        "radius_ft": 1.25,
        "allowed_masks": ["110000", "001100", "000011"],
        "lethal": False,
    },
    "traffic_barricade": {
        "footprint_type": "rectangle",
        "width_ft": 5.0,
        "depth_ft": 2.0,
        "allowed_masks": ["111000", "011110", "000111"],
        "lethal": False,
    },
    "pothole": {
        "footprint_type": "circle",
        "radius_ft": 1.0,
        "allowed_masks": ["110000", "001100", "000011"],
        "lethal": True,
    },
    "six_barrel_wall": {
        "footprint_type": "rectangle",
        "width_ft": 10.0,
        "depth_ft": 2.5,
        "allowed_masks": ["111111"],
        "lethal": False,
    },
}


def _dist(a, b):
    return math.hypot(b[0] - a[0], b[1] - a[1])


def _round3(x):
    return round(float(x), 3)


class LaneSegmentAdapter:
    def __init__(self, lane_segments):
        self.segments = {s["id"]: self._prepare_segment(s) for s in lane_segments}

    def _prepare_segment(self, seg):
        pts = seg.get("centerline_points") or seg.get("centerline")
        if not pts or len(pts) < 2:
            raise ValueError(f"lane segment {seg.get('id')} needs at least 2 centerline points")
        scale = float(seg.get("coordinate_scale", 1.0))
        pts_ft = [[p[0] * scale, p[1] * scale] for p in pts]
        lengths = [0.0]
        for a, b in zip(pts_ft, pts_ft[1:]):
            lengths.append(lengths[-1] + _dist(a, b))
        out = dict(seg)
        out["centerline_points"] = pts_ft
        out["length_ft"] = float(seg.get("length_ft", lengths[-1]))
        out["_cum_lengths"] = lengths
        return out

    def pose_at_s(self, segment_id, s_ft):
        seg = self.segments[segment_id]
        pts = seg["centerline_points"]
        lengths = seg["_cum_lengths"]
        s = max(0.0, min(float(s_ft), lengths[-1]))
        idx = min(max(0, bisect_right(lengths, s) - 1), len(pts) - 2)
        a, b = pts[idx], pts[idx + 1]
        span = max(1e-9, lengths[idx + 1] - lengths[idx])
        t = (s - lengths[idx]) / span
        x = a[0] + (b[0] - a[0]) * t
        y = a[1] + (b[1] - a[1]) * t
        heading = math.atan2(b[1] - a[1], b[0] - a[0])
        return [x, y, heading]

    def normal_at_s(self, segment_id, s_ft):
        _, _, heading = self.pose_at_s(segment_id, s_ft)
        return [-math.sin(heading), math.cos(heading)]

    def width_at_s(self, segment_id, s_ft):
        return float(self.segments[segment_id].get("width_ft", 10.0))

    def length(self, segment_id):
        return float(self.segments[segment_id]["length_ft"])


# Free-function adapters for callers that prefer the requested helper names.
def pose_at_s(lane_segments, segment_id, s_ft):
    return LaneSegmentAdapter(lane_segments).pose_at_s(segment_id, s_ft)


def normal_at_s(lane_segments, segment_id, s_ft):
    return LaneSegmentAdapter(lane_segments).normal_at_s(segment_id, s_ft)


def width_at_s(lane_segments, segment_id, s_ft):
    return LaneSegmentAdapter(lane_segments).width_at_s(segment_id, s_ft)


def tile_lane_segments(lane_segments, tile_length_ft=5.0, obstacle_columns=6):
    adapter = LaneSegmentAdapter(lane_segments)
    tiles = []
    for seg in lane_segments:
        seg_id = seg["id"]
        length = adapter.length(seg_id)
        n = int(math.ceil(length / tile_length_ft))
        for i in range(n):
            start = i * tile_length_ft
            end = min(length, (i + 1) * tile_length_ft)
            center = (start + end) / 2.0
            tiles.append({
                "id": f"tile_{len(tiles):03d}",
                "segment_id": seg_id,
                "s_start_ft": round(start, 3),
                "s_end_ft": round(end, 3),
                "s_center_ft": round(center, 3),
                "width_ft": round(adapter.width_at_s(seg_id, center), 3),
                "obstacle_columns": int(obstacle_columns),
                "obstacle_mask": "000000",
                "obstacle_type": None,
            })
    return tiles


def column_centers(width_ft, columns=6):
    cw = float(width_ft) / columns
    return [float(width_ft) / 2.0 - (i + 0.5) * cw for i in range(columns)]


def occupied_columns(mask):
    if len(mask) != 6 or any(c not in "01" for c in mask):
        raise ValueError(f"invalid 6-column obstacle mask: {mask}")
    return [i for i, c in enumerate(mask) if c == "1"]


def mask_to_lateral_offset(mask, width_ft):
    occ = occupied_columns(mask)
    if not occ:
        return 0.0
    centers = column_centers(width_ft, len(mask))
    return sum(centers[i] for i in occ) / len(occ)


def max_adjacent_empty_columns(mask):
    best = cur = 0
    for c in mask:
        if c == "0":
            cur += 1
            best = max(best, cur)
        else:
            cur = 0
    return best


def mask_has_required_clearance(mask, width_ft, required_passage_ft=5.0, bypass_defined=False):
    if mask == "111111" and not bypass_defined:
        return False
    col_width = float(width_ft) / len(mask)
    required_empty = int(math.ceil(required_passage_ft / col_width - 1e-9))
    return max_adjacent_empty_columns(mask) >= required_empty


def mask_allowed_by_width_policy(mask, width_ft):
    if width_ft <= 10.01 and mask in {"001100", "011110", "111111"}:
        return False
    return True


def obstacle_pose_for_tile(tile, mask, adapter):
    s_ft = float(tile["s_center_ft"])
    x, y, heading = adapter.pose_at_s(tile["segment_id"], s_ft)
    nx, ny = adapter.normal_at_s(tile["segment_id"], s_ft)
    d_ft = mask_to_lateral_offset(mask, float(tile["width_ft"]))
    return {
        "s_ft": round(s_ft, 3),
        "lane_relative": {"d_ft": round(d_ft, 3)},
        "world_pose_ft": {
            "x": round(x + d_ft * nx, 3),
            "y": round(y + d_ft * ny, 3),
            "heading_deg": round(math.degrees(heading), 3),
        },
    }


def _footprint_for_model(model):
    if model["footprint_type"] == "circle":
        return {"type": "circle", "radius_ft": model["radius_ft"]}
    return {"type": "rectangle", "width_ft": model["width_ft"], "depth_ft": model["depth_ft"]}


def place_legal_obstacles(
    lane_tiles,
    adapter,
    seed=1,
    probability_per_tile=0.15,
    min_spacing_ft=25.0,
    avoid_start_distance_ft=30.0,
    avoid_finish_distance_ft=20.0,
    avoid_ramp_distance_ft=20.0,
    forbidden_tile_ids=None,
    ramp_s_values=None,
):
    rng = random.Random(seed)
    forbidden_tile_ids = set(forbidden_tile_ids or [])
    ramp_s_values = list(ramp_s_values or [])
    obstacles = []
    model_names = ["construction_barrel", "traffic_barricade", "pothole", "six_barrel_wall"]
    segment_offsets = {}
    cursor = 0.0
    for seg_id, seg in adapter.segments.items():
        segment_offsets[seg_id] = cursor
        cursor += float(seg["length_ft"])
    total_length = cursor
    last_global_s = None

    for tile in lane_tiles:
        seg_id = tile["segment_id"]
        s = float(tile["s_center_ft"])
        global_s = segment_offsets.get(seg_id, 0.0) + s
        if tile["id"] in forbidden_tile_ids or tile.get("forbidden"):
            continue
        if global_s < avoid_start_distance_ft or (total_length - global_s) < avoid_finish_distance_ft:
            continue
        if any(abs(global_s - rs) < avoid_ramp_distance_ft for rs in ramp_s_values):
            continue
        if rng.random() > probability_per_tile:
            continue
        if last_global_s is not None and abs(global_s - last_global_s) < min_spacing_ft:
            continue
        rng.shuffle(model_names)
        accepted = None
        for typ in model_names:
            model = OBSTACLE_MODELS[typ]
            masks = list(model["allowed_masks"])
            rng.shuffle(masks)
            for mask in masks:
                if not mask_allowed_by_width_policy(mask, float(tile["width_ft"])):
                    continue
                if not mask_has_required_clearance(mask, float(tile["width_ft"])):
                    continue
                pose = obstacle_pose_for_tile(tile, mask, adapter)
                accepted = {
                    "id": f"obs_{len(obstacles) + 1:03d}",
                    "type": typ,
                    "tile_id": tile["id"],
                    "segment_id": seg_id,
                    "s_ft": pose["s_ft"],
                    "mask": mask,
                    "lane_relative": pose["lane_relative"],
                    "world_pose_ft": pose["world_pose_ft"],
                    "footprint": _footprint_for_model(model),
                    "lethal": bool(model["lethal"]),
                }
                break
            if accepted:
                break
        if accepted:
            tile["obstacle_mask"] = accepted["mask"]
            tile["obstacle_type"] = accepted["type"]
            obstacles.append(accepted)
            last_global_s = global_s
    return obstacles


def build_lane_gates(adapter, gate_specs):
    gates = []
    for idx, spec in enumerate(gate_specs):
        seg_id = spec["segment_id"]
        s = float(spec["s_ft"])
        x, y, heading = adapter.pose_at_s(seg_id, s)
        nx, ny = adapter.normal_at_s(seg_id, s)
        width = float(spec.get("width_ft", adapter.width_at_s(seg_id, s)))
        gate = {
            "id": spec.get("id", f"gate_{idx + 1:03d}"),
            "type": spec.get("type", "lane_gate"),
            "segment_id": seg_id,
            "s_ft": round(s, 3),
            "center_ft": [round(x, 3), round(y, 3)],
            "heading_deg": round(math.degrees(heading), 3),
            "width_ft": round(width, 3),
            "left_post_ft": [round(x + (width / 2) * nx, 3), round(y + (width / 2) * ny, 3)],
            "right_post_ft": [round(x - (width / 2) * nx, 3), round(y - (width / 2) * ny, 3)],
            "normal_ft": [round(math.cos(heading), 6), round(math.sin(heading), 6)],
            "next_mode": spec.get("next_mode", "lane_follow"),
        }
        gates.append(gate)
    return gates


def generate_virtual_progress_gates(adapter, lane_tiles, spacing_ft=20.0):
    blocked = {(t["segment_id"], round(float(t["s_start_ft"]), 3), round(float(t["s_end_ft"]), 3)) for t in lane_tiles if t.get("obstacle_mask", "000000") != "000000"}
    specs = []
    for seg_id, seg in adapter.segments.items():
        s = float(spacing_ft)
        while s < float(seg["length_ft"]):
            if not any(seg_id == b[0] and b[1] <= s <= b[2] for b in blocked):
                specs.append({"id": f"progress_{len(specs):03d}", "type": "lane_gate", "segment_id": seg_id, "s_ft": s, "next_mode": "lane_follow"})
            s += float(spacing_ft)
    return build_lane_gates(adapter, specs)


def has_crossed_gate(prev_pos, curr_pos, gate):
    cx, cy = gate["center_ft"]
    nx, ny = gate["normal_ft"]
    prev_side = (prev_pos[0] - cx) * nx + (prev_pos[1] - cy) * ny
    curr_side = (curr_pos[0] - cx) * nx + (curr_pos[1] - cy) * ny
    return prev_side < 0 and curr_side >= 0
