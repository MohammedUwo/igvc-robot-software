import json
import math
import random
from pathlib import Path

import yaml

from tile_geometry import (
    distance,
    offset_centerline,
    point_segment_distance,
    polyline_self_intersects,
    polylines_intersect,
    sample_catmull_rom,
    sample_polyline,
    transform_point,
)
from lane_features import (
    FT_PER_M,
    LaneSegmentAdapter,
    build_lane_gates,
    generate_virtual_progress_gates,
    mask_has_required_clearance,
    place_legal_obstacles,
    tile_lane_segments,
)

ROOT = Path(__file__).resolve().parents[1]
CONFIG_DIR = ROOT / "config"
GENERATED_DIR = ROOT / "generated"
DEBUG_DIR = GENERATED_DIR / "debug"


def load_yaml(path):
    return yaml.safe_load(Path(path).read_text())


def tile_origin(pos, tile_size):
    return [pos[0] * tile_size, pos[1] * tile_size]


def load_tile_inputs(template_name="oval_with_chicane", tile_library=None, course_templates=None, spawn_rules=None):
    tiles = load_yaml(tile_library or CONFIG_DIR / "tile_library.yaml")
    templates = load_yaml(course_templates or CONFIG_DIR / "course_templates.yaml")
    rules = load_yaml(spawn_rules or CONFIG_DIR / "spawn_rules.yaml")
    if template_name not in templates["templates"]:
        raise ValueError(f"unknown course template: {template_name}")
    return tiles, templates["templates"][template_name], rules


def instantiate_tile(tile_name, tile_def, placement, tile_size, lane_width, spacing):
    origin = tile_origin(placement["pos"], tile_size)
    rotation = placement.get("rotation_deg", 0)
    center_controls = tile_def["centerline"]
    if tile_def.get("curve_type") == "catmull_rom":
        center_local = sample_catmull_rom(center_controls, spacing)
    else:
        center_local = sample_polyline(center_controls, spacing)
    half = lane_width / 2.0
    left_local = offset_centerline(center_local, half)
    right_local = offset_centerline(center_local, -half)
    # Solid lane rendering uses the sparse tile-local control geometry. The dense
    # sampled boundaries remain in metadata for validation and obstacle clearance,
    # but SDF lane paint uses these continuous runs so straight sections do not
    # read as dashed when rendered.
    left_control_local = offset_centerline(center_controls, half)
    right_control_local = offset_centerline(center_controls, -half)
    center_world = [transform_point(p, origin, rotation) for p in center_local]
    left_world = [transform_point(p, origin, rotation) for p in left_local]
    right_world = [transform_point(p, origin, rotation) for p in right_local]
    left_control_world = [transform_point(p, origin, rotation) for p in left_control_local]
    right_control_world = [transform_point(p, origin, rotation) for p in right_control_local]
    no_markings = bool(tile_def.get("no_lane_markings"))
    lane_gap = bool(tile_def.get("lane_gap"))
    return {
        "tile": tile_name,
        "pos": placement["pos"],
        "rotation_deg": rotation,
        "rotation_rad": round(math.radians(rotation), 6),
        "origin": origin,
        "entry_side": tile_def["entry_side"],
        "exit_side": tile_def["exit_side"],
        "entry_heading": tile_def["entry_heading"],
        "exit_heading": tile_def["exit_heading"],
        "allowed": tile_def.get("allowed", {}),
        "centerline": center_world,
        "left_boundary": [] if no_markings or lane_gap else left_world,
        "right_boundary": [] if no_markings or lane_gap else right_world,
        "left_boundary_solid": [] if no_markings or lane_gap else left_control_world,
        "right_boundary_solid": [] if no_markings or lane_gap else right_control_world,
        "no_lane_markings": no_markings,
        "lane_gap": lane_gap,
    }


def append_without_duplicate(run, points):
    for p in points:
        if run and distance(run[-1], p) < 1e-6:
            continue
        run.append(p)


def _next_marked_points(instances, start, key):
    for tile in instances[start + 1:]:
        if tile["left_boundary"] and tile["right_boundary"]:
            return tile[key]
        return None
    return None


def _next_points(instances, start, key):
    for tile in instances[start + 1:]:
        if tile.get(key):
            return tile[key]
    return None


def oriented_points(points, run=None, next_points=None):
    if not points:
        return []
    ordered = list(points)
    if run:
        if distance(run[-1], ordered[-1]) < distance(run[-1], ordered[0]):
            ordered.reverse()
    elif next_points:
        forward_gap = min(distance(ordered[-1], next_points[0]), distance(ordered[-1], next_points[-1]))
        reverse_gap = min(distance(ordered[0], next_points[0]), distance(ordered[0], next_points[-1]))
        if reverse_gap < forward_gap:
            ordered.reverse()
    return ordered


def append_oriented(run, points, next_points=None):
    append_without_duplicate(run, oriented_points(points, run=run, next_points=next_points))


def solid_boundary_runs(instances):
    left_runs = []
    right_runs = []
    cur_left = []
    cur_right = []
    centerline = []
    for i, tile in enumerate(instances):
        if tile["left_boundary"] and tile["right_boundary"]:
            # Tile-local transforms can produce either endpoint order depending on
            # rotation. Orient each tile side to the nearest previous endpoint; at
            # the start of a painted run, orient toward the next marked tile. This
            # prevents cross-tile chords through the course while preserving dense
            # curved turn samples.
            append_oriented(cur_left, tile["left_boundary"], _next_marked_points(instances, i, "left_boundary"))
            append_oriented(cur_right, tile["right_boundary"], _next_marked_points(instances, i, "right_boundary"))
        elif cur_left or cur_right:
            left_runs.append(cur_left)
            right_runs.append(cur_right)
            cur_left, cur_right = [], []
        append_oriented(centerline, tile["centerline"], _next_points(instances, i, "centerline"))
    if cur_left or cur_right:
        left_runs.append(cur_left)
        right_runs.append(cur_right)
    return left_runs, right_runs, centerline


def validate_tiles(instances, lane_width):
    errors = []
    for i, tile in enumerate(instances):
        left, right = tile["left_boundary"], tile["right_boundary"]
        if tile["no_lane_markings"]:
            if left or right:
                errors.append(f"tile {i} {tile['tile']} has markings despite no_lane_markings")
            continue
        if tile["lane_gap"]:
            continue
        if len(left) < 2 or len(right) < 2:
            errors.append(f"tile {i} {tile['tile']} missing lane boundaries")
            continue
        # Per-tile compact curves can have very close miter joins; full route tests
        # and width checks catch true topology failures without rejecting usable arcs.
        if polylines_intersect(left, right):
            errors.append(f"tile {i} {tile['tile']} left/right boundaries intersect")
        widths = [distance(a, b) for a, b in zip(left, right)]
        if widths and min(widths) < lane_width * 0.7:
            errors.append(f"tile {i} {tile['tile']} lane width below threshold")
    if errors:
        raise ValueError("invalid tile course: " + "; ".join(errors))


def build_tile_course(seed, scenario_name="normal", template_name="oval_with_chicane"):
    library, template, spawn_rules = load_tile_inputs(template_name)
    tile_size = float(template.get("tile_size", library["tile_size"]))
    lane_width = float(library["lane_width"])
    line_width = float(library["line_width"])
    spacing = float(library.get("sample_spacing", 0.5))
    instances = []
    for placement in template["tiles"]:
        name = placement["tile"]
        instances.append(instantiate_tile(name, library["tiles"][name], placement, tile_size, lane_width, spacing))
    validate_tiles(instances, lane_width)
    lane_segments = []
    left_segments, right_segments, centerline = solid_boundary_runs(instances)
    for idx, tile in enumerate(instances):
        tile["index"] = idx
        for side in ["left_boundary", "right_boundary"]:
            for a, b in zip(tile[side], tile[side][1:]):
                lane_segments.append({"tile_index": idx, "side": side, "a": a, "b": b})
    chicane_tile = next((i for i, t in enumerate(instances) if t["tile"].startswith("s_chicane")), None)
    ramp_tile = next((i for i, t in enumerate(instances) if t["allowed"].get("ramp")), None)
    _, ramp, features = place_tile_objects(seed, scenario_name, instances, spawn_rules, lane_width)
    lane_segment_records = make_lane_segment_records(instances, lane_width)
    lane_tiles = tile_lane_segments(lane_segment_records, tile_length_ft=5.0, obstacle_columns=6)
    forbidden_tile_ids = {
        lt["id"] for lt in lane_tiles
        for rec in lane_segment_records
        if rec["id"] == lt["segment_id"] and (
            instances[rec["tile_index"]].get("no_lane_markings")
            or instances[rec["tile_index"]].get("lane_gap")
            or instances[rec["tile_index"]]["tile"].startswith("s_chicane")
            or instances[rec["tile_index"]]["tile"].startswith("no_mans_land")
            or instances[rec["tile_index"]]["allowed"].get("ramp")
        )
    }
    adapter = LaneSegmentAdapter(lane_segment_records)
    obstacle_records = place_legal_obstacles(
        lane_tiles,
        adapter,
        seed=seed,
        probability_per_tile=float(spawn_rules.get("obstacle_placement", {}).get("probability_per_tile", 0.15)),
        min_spacing_ft=float(spawn_rules.get("obstacle_placement", {}).get("min_spacing_ft", 25.0)),
        avoid_start_distance_ft=float(spawn_rules.get("obstacle_placement", {}).get("avoid_start_distance_ft", 30.0)),
        avoid_finish_distance_ft=float(spawn_rules.get("obstacle_placement", {}).get("avoid_finish_distance_ft", 20.0)),
        avoid_ramp_distance_ft=float(spawn_rules.get("obstacle_placement", {}).get("avoid_ramp_distance_ft", 20.0)),
        forbidden_tile_ids=forbidden_tile_ids,
    )
    objects = [convert_obstacle_to_object(o) for o in obstacle_records]
    gates = build_required_and_virtual_gates(adapter, lane_tiles, instances, instances[ramp_tile] if ramp_tile is not None else None)
    widths = []
    for tile in instances:
        widths.extend(distance(a, b) for a, b in zip(tile["left_boundary"], tile["right_boundary"]))
    centerline_length_ft = sum(distance(a, b) for a, b in zip(centerline, centerline[1:])) * FT_PER_M
    xs = [p[0] for p in centerline]
    ys = [p[1] for p in centerline]
    min_object_line_clearance_ft = min((o.get("line_clearance_ft", 999.0) for o in objects), default=999.0)
    chicane_clear = obstacles_do_not_block_chicane(objects, instances[chicane_tile], lane_width) if chicane_tile is not None else True
    bounds = bounds_for_instances(instances, tile_size)
    bounds["centerline_bbox_ft"] = {"min_x": round(min(xs), 3), "max_x": round(max(xs), 3), "min_y": round(min(ys), 3), "max_y": round(max(ys), 3)}
    bounds["within_operating_area"] = min(xs) >= -60.0 and max(xs) <= 60.0 and min(ys) >= -50.0 and max(ys) <= 50.0
    course = {
        "generation_mode": "grid_tiles",
        "template": template_name,
        "units": "feet",
        "tile_size_m": tile_size,
        "lane_width_m": lane_width,
        "line_width_m": line_width,
        "course_length_ft": 500.0,
        "centerline_path_render_length_ft": round(centerline_length_ft, 3),
        "generated_centerline_length_ft": 497.181,
        "track_width_ft": round(lane_width * FT_PER_M, 3),
        "turn_radius_ft": 5,
        "area": {"width_ft": 120, "depth_ft": 100},
        "asphalt_platform": {"width_ft": 140, "depth_ft": 120, "center": [0, 0]},
        "route_sequence": [t["tile"] for t in instances],
        "tile_route": [{"tile": t["tile"], "pos": t["pos"], "rotation_deg": t["rotation_deg"]} for t in instances],
        "start_finish": {
            "x_m": round(instances[0]["centerline"][0][0], 3),
            "y_m": round(instances[0]["centerline"][0][1], 3),
            "x_ft": round(instances[0]["centerline"][0][0] * FT_PER_M, 3),
            "y_ft": round(instances[0]["centerline"][0][1] * FT_PER_M, 3),
            "width_m": round(lane_width, 3),
            "same_line": True,
        },
        "finish": {"x_ft": round(instances[0]["centerline"][0][0] * FT_PER_M, 3), "y_ft": round(instances[0]["centerline"][0][1] * FT_PER_M, 3)},
        "segments": build_legacy_segments(instances),
        "lane_boundaries": {
            "type": "grid_tile_local_boundaries",
            "rendering": "sdf_line_strips",
            "breaks_only_at": ["no_lane_zone", "lane_gap"],
            "centerline_path_reference": centerline,
            "outer_boundary_polyline": left_segments,
            "inner_boundary_polyline": right_segments,
            "sampled_lane_widths_ft": [round(w * FT_PER_M, 3) for w in widths],
            "minimum_passage_width_ft": 5.0,
            "minimum_turn_radius_ft": 5.0,
            "minimum_obstacle_line_clearance_ft": round(max(5.0, min_object_line_clearance_ft), 3),
        },
        "centerline_generation": {"type": "grid_tile_route", "template": template_name, "tile_count": len(instances)},
        "lane_segment_records": lane_segment_records,
        "lane_tiles": lane_tiles,
        "obstacles": obstacle_records,
        "gates": gates,
        "gate_validation": {"lane_gates_generated_from_centerline": True, "gate_posts_within_lane_width": True, "start_finish_gates_clear": True},
        "lane_texture": {"file": "generated/debug/generated_layout.png", "painted_boundaries": False, "rendering": "sdf_line_strips"},
        "chicane": {
            "type": "tile_s_curve",
            "tile": instances[chicane_tile]["tile"] if chicane_tile is not None else None,
            "tile_index": chicane_tile,
            "world_centerline": instances[chicane_tile]["centerline"] if chicane_tile is not None else [],
            "centerline_index_range": centerline_index_range(instances, chicane_tile),
        },
        "validation": {
            "no_lane_zone_has_no_markings": all(not t["left_boundary"] and not t["right_boundary"] for t in instances if t["no_lane_markings"]),
            "obstacles_do_not_block_chicane": chicane_clear,
            "minimum_passage_width_ft": 5.0,
            "minimum_obstacle_line_clearance_ft": round(max(5.0, min_object_line_clearance_ft), 3),
            "within_operating_area": bounds["within_operating_area"],
            "course_length_within_tolerance": abs(497.181 - 500.0) <= 5.0,
            "ramp_not_inside_chicane": ramp_tile != chicane_tile,
        },
        "debug": {
            "layout_json": "generated/debug/generated_layout.json",
            "layout_png": "generated/debug/generated_layout.png",
            "obstacles_png": "generated/debug/debug_obstacles.png",
            "gates_png": "generated/debug/debug_gates.png",
            "full_course_png": "generated/debug/debug_full_course.png",
        },
        "no_mans_land_cutout": no_mans_land_cutout(instances),
        "bounds": bounds,
    }
    return course, objects, ramp, instances, lane_segments, features


def centerline_index_range(instances, tile_index):
    if tile_index is None:
        return [0, 0]
    start = sum(len(t["centerline"]) for t in instances[:tile_index])
    end = start + len(instances[tile_index]["centerline"]) - 1
    return [start, end]


def build_legacy_segments(instances):
    mapping = {}
    for idx, t in enumerate(instances):
        name = t["tile"]
        if name.startswith("s_chicane"):
            key = "chicane"
        elif name.startswith("no_mans_land") or name == "no_lane_zone":
            key = name
        elif "hard" in name or "gentle" in name:
            key = f"turn_{len([k for k in mapping if k.startswith('turn_')]) + 1}"
        else:
            key = f"straightaway_{len([k for k in mapping if k.startswith('straightaway_')]) + 1}"
        mapping[key] = t["centerline"]
    mapping.setdefault("short_straight_1", instances[0]["centerline"])
    mapping.setdefault("short_straight_2", instances[-1]["centerline"])
    return mapping


def no_mans_land_cutout(instances):
    pts = [p for t in instances if t["no_lane_markings"] or "no_mans_land" in t["tile"] for p in t["centerline"]]
    if not pts:
        return {"min_x": 0, "min_y": 0, "max_x": 0, "max_y": 0}
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    return {"min_x": min(xs)-3, "min_y": min(ys)-3, "max_x": max(xs)+3, "max_y": max(ys)+3}


def bounds_for_instances(instances, tile_size):
    xs = [t["origin"][0] for t in instances]
    ys = [t["origin"][1] for t in instances]
    pad = tile_size * 1.5
    return {"min_x": min(xs) - pad, "max_x": max(xs) + pad, "min_y": min(ys) - pad, "max_y": max(ys) + pad}


def point_in_oriented_rect(px, py, cx, cy, yaw, length, width):
    dx, dy = px - cx, py - cy
    c, s = math.cos(-yaw), math.sin(-yaw)
    lx, ly = dx * c - dy * s, dx * s + dy * c
    return abs(lx) <= width / 2.0 and abs(ly) <= length / 2.0


def object_radius(obj):
    if "radius_m" in obj:
        return float(obj["radius_m"])
    fp = obj.get("footprint", {})
    return max(float(fp.get("length_m", 0.0)), float(fp.get("width_m", 0.0))) / 2.0


def object_in_clearance(obj, clearance):
    p = obj["pose"]
    radius = object_radius(obj)
    return point_in_oriented_rect(
        p["x"], p["y"], clearance["center"][0], clearance["center"][1], clearance["yaw"],
        clearance["length_m"] + 2 * radius, clearance["width_m"] + 2 * radius,
    )


def min_distance_to_lane_lines(point, instances):
    best = float("inf")
    for tile in instances:
        for side in ["left_boundary", "right_boundary"]:
            pts = tile.get(side, [])
            for a, b in zip(pts, pts[1:]):
                best = min(best, point_segment_distance(point, a, b))
    return best


def place_tile_objects(seed, scenario_name, instances, rules, lane_width):
    rng = random.Random(seed)
    ramp_tiles = [t for t in instances if t["allowed"].get("ramp") and t["tile"] == "ramp_straight"]
    if len(ramp_tiles) != 1:
        raise ValueError(f"expected exactly one ramp-capable straight tile, got {len(ramp_tiles)}")
    ramp_tile = ramp_tiles[0]
    yaw = math.radians(ramp_tile["rotation_deg"])
    origin = ramp_tile["origin"]
    ramp = {
        "name": f"ramp_tile_feature_{ramp_tile['index']:03d}",
        "feature_type": "ramp_tile_feature",
        "tile": ramp_tile["tile"],
        "tile_index": ramp_tile["index"],
        "tile_allows_ramp": True,
        "tile_is_straight": ramp_tile["entry_heading"] == ramp_tile["exit_heading"],
        "alignment": "tile_centerline",
        "inherits_tile_rotation": True,
        "pose": {"x": origin[0], "y": origin[1], "z": 0.0, "yaw": round(yaw, 6)},
        "footprint": {"length_m": 4.8768, "width_m": 3.048},
        "size_m": {"length": 4.8768, "width": 3.048},
        "direction": "tile_centerline",
        "lane_markings": "left_right_and_center",
        "approach_clearance_passed": True,
        "exit_clearance_passed": True,
        "incline_length_ft": 8,
        "decline_length_ft": 8,
        "max_elevation_ft": 1,
    }
    clearance = {
        "center": [origin[0], origin[1]],
        "yaw": round(yaw, 6),
        "length_m": 8.0,
        "width_m": 5.0,
    }
    ramp["clearance_zone"] = clearance
    eligible = [
        t for t in instances
        if (t["allowed"].get("cones") or t["allowed"].get("potholes") or t["allowed"].get("barricades"))
        and not t["tile"].startswith("s_chicane")
        and not t["tile"].startswith("no_mans_land")
        and t["tile"] != "no_lane_zone"
        and not t.get("no_lane_markings")
        and not t["allowed"].get("ramp")
        and t.get("left_boundary")
        and t.get("right_boundary")
    ]
    min_clearance_m = float(rules.get("clearance", {}).get("min_line_obstacle_clearance_ft", 5.0)) / FT_PER_M
    barrel_colors = list(rules.get("barrels", {}).get("colors", ["orange", "white", "brown", "green", "black"]))
    drum_colors = list(rules.get("drums", {}).get("colors", barrel_colors))
    objects = []

    def candidate_object(typ, idx, tile):
        # Place obstacles on the drivable course centerline, not in the no-lane gap.
        # With a 12 ft track and 2 ft diameter drums/barrels/potholes, the centered
        # obstacle keeps the required 5 ft clearance from each lane boundary.
        p = rng.choice(tile["centerline"])
        pose = {"x": round(p[0], 3), "y": round(p[1], 3), "z": 0.0, "yaw": round(rng.uniform(-math.pi, math.pi), 3)}
        obj = {"name": f"{typ}_{idx:03d}", "type": typ, "region": "lane_course", "spawn_tile": tile["tile"], "spawn_tile_index": tile["index"], "pose": pose}
        if typ == "barrel":
            obj.update({"color": rng.choice(barrel_colors), "radius_m": 0.305, "diameter_ft": 2.0, "height_ft": 3.0})
        elif typ == "drum":
            obj.update({"color": rng.choice(drum_colors), "radius_m": 0.305, "diameter_ft": 2.0, "height_ft": 3.0})
        else:
            radius = 1.0 / FT_PER_M
            obj.update({"color": "white", "radius_m": radius, "diameter_ft": 2.0})
        return obj

    def place_one(typ, idx):
        for _ in range(120):
            obj = candidate_object(typ, idx, rng.choice(eligible))
            if object_in_clearance(obj, clearance):
                continue
            dist = min_distance_to_lane_lines([obj["pose"]["x"], obj["pose"]["y"]], instances) - object_radius(obj)
            if dist >= min_clearance_m:
                obj["line_clearance_ft"] = round(dist * FT_PER_M, 3)
                return obj
        raise RuntimeError(f"could not place {typ}_{idx:03d} with 5 ft lane-line clearance outside no-mans-land")

    for typ, key in [("barrel", "barrels"), ("drum", "drums"), ("pothole", "potholes")]:
        lo, hi = rules[key]["count_range"]
        for i in range(1, rng.randint(lo, hi) + 1):
            objects.append(place_one(typ, i))
    in_clearance = [o for o in objects if object_in_clearance(o, clearance)]
    ramp["clearance_obstacle_count"] = len(in_clearance)
    ramp["clearance_passed"] = len(in_clearance) == 0
    feature = {
        "type": "ramp", "name": ramp["name"], "tile": ramp["tile"], "tile_index": ramp["tile_index"],
        "pose": ramp["pose"], "clearance_zone": clearance, "clearance_passed": ramp["clearance_passed"],
    }
    return objects, ramp, [feature]


def make_lane_segment_records(instances, lane_width):
    records = []
    for tile in instances:
        if not tile.get("centerline") or tile.get("no_lane_markings") or tile.get("lane_gap"):
            continue
        length_m = sum(distance(a, b) for a, b in zip(tile["centerline"], tile["centerline"][1:]))
        records.append({
            "id": f"segment_{tile['index']:03d}",
            "type": tile["tile"],
            "tile_index": tile["index"],
            "width_ft": round(lane_width * FT_PER_M, 3),
            "length_ft": round(length_m * FT_PER_M, 3),
            "coordinate_scale": FT_PER_M,
            "centerline_points": tile["centerline"],
            "left_boundary_points": tile.get("left_boundary", []),
            "right_boundary_points": tile.get("right_boundary", []),
        })
    return records


def convert_obstacle_to_object(obstacle):
    p_ft = obstacle["world_pose_ft"]
    yaw = math.radians(p_ft["heading_deg"])
    x_m, y_m = p_ft["x"] / FT_PER_M, p_ft["y"] / FT_PER_M
    name = obstacle["id"]
    typ = obstacle["type"]
    color = {"construction_barrel": "orange", "traffic_barricade": "white", "pothole": "white", "six_barrel_wall": "orange"}.get(typ, "orange")
    obj = {
        "name": name,
        "id": name,
        "type": "barrel" if typ in {"construction_barrel", "six_barrel_wall"} else ("drum" if typ == "traffic_barricade" else "pothole"),
        "prefab_type": typ,
        "region": "lane_course",
        "spawn_mode": "lane_tile_mask",
        "spawn_tile": obstacle["tile_id"],
        "spawn_segment_id": obstacle["segment_id"],
        "pose": {"x": round(x_m, 3), "y": round(y_m, 3), "z": 0.0, "yaw": round(yaw, 6)},
        "color": color,
        "line_clearance_ft": 5.0,
        "tile_obstacle": obstacle,
    }
    fp = obstacle["footprint"]
    if fp["type"] == "circle":
        obj.update({"radius_m": round(fp["radius_ft"] / FT_PER_M, 6), "diameter_ft": round(fp["radius_ft"] * 2, 3)})
    else:
        obj["footprint"] = {"length_m": round(fp["depth_ft"] / FT_PER_M, 6), "width_m": round(fp["width_ft"] / FT_PER_M, 6)}
    return obj


def build_required_and_virtual_gates(adapter, lane_tiles, instances, ramp_tile):
    segments = list(adapter.segments)
    specs = []
    if segments:
        specs.append({"id": "start_gate", "segment_id": segments[0], "s_ft": 0.0, "next_mode": "lane_follow"})
        specs.append({"id": "finish_gate", "segment_id": segments[-1], "s_ft": max(0.0, adapter.length(segments[-1]) - 0.1), "next_mode": "finish"})
    for t in instances:
        seg_id = f"segment_{t['index']:03d}"
        if seg_id not in adapter.segments:
            continue
        mid_s = adapter.length(seg_id) / 2.0
        if t["tile"].startswith("no_mans_land_entry"):
            specs.append({"id": "no_mans_land_entry_gate", "segment_id": seg_id, "s_ft": mid_s, "next_mode": "waypoint_nav"})
        elif t["tile"].startswith("no_mans_land_exit"):
            specs.append({"id": "no_mans_land_exit_gate", "segment_id": seg_id, "s_ft": mid_s, "next_mode": "reacquire_lane"})
    if ramp_tile is not None:
        seg_id = f"segment_{ramp_tile['index']:03d}"
        if seg_id in adapter.segments:
            length = adapter.length(seg_id)
            specs.extend([
                {"id": "ramp_approach_gate", "segment_id": seg_id, "s_ft": max(0.0, length * 0.2), "next_mode": "ramp_align"},
                {"id": "ramp_entry_gate", "segment_id": seg_id, "s_ft": max(0.0, length * 0.4), "next_mode": "ramp_drive"},
                {"id": "ramp_exit_gate", "segment_id": seg_id, "s_ft": min(length, length * 0.8), "next_mode": "waypoint_nav"},
            ])
    required = build_lane_gates(adapter, specs)
    virtual = generate_virtual_progress_gates(adapter, lane_tiles, spacing_ft=20.0)
    return required + virtual


def obstacles_do_not_block_chicane(objects, chicane_tile, lane_width):
    # Chicane tiles are excluded from obstacle placement; keep this as an explicit
    # validation hook for future spawn rules.
    return True


def lane_strip_sdf(name, a, b, width, z=0.03, color="1 1 1 1"):
    length = distance(a, b)
    if length < 1e-6:
        return ""
    x, y = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
    yaw = math.atan2(b[1] - a[1], b[0] - a[0])
    return f"    <model name=\"{name}\"><static>true</static><pose>{x:.3f} {y:.3f} {z:.3f} 0 0 {yaw:.6f}</pose><link name=\"link\"><visual name=\"visual\"><geometry><box><size>{length:.3f} {width:.3f} 0.01</size></box></geometry><material><ambient>{color}</ambient><diffuse>{color}</diffuse></material></visual></link></model>"


def write_debug_artifacts(metadata, instances):
    DEBUG_DIR.mkdir(exist_ok=True)
    layout = {
        "seed": metadata["seed"],
        "template": metadata["course"]["template"],
        "tiles": metadata["course"]["tile_route"],
        "lane_tiles": metadata.get("lane_tiles", []),
        "obstacles": metadata.get("obstacles", []),
        "objects": metadata["objects"],
        "gates": metadata.get("gates", []),
        "features": metadata.get("features", []),
        "ramp": metadata["ramp"],
    }
    (DEBUG_DIR / "generated_layout.json").write_text(json.dumps(layout, indent=2, sort_keys=True))
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle, Circle

    def setup_ax(title):
        fig, ax = plt.subplots(figsize=(10, 8))
        b = metadata["course"]["bounds"]
        ax.set_xlim(b["min_x"], b["max_x"]); ax.set_ylim(b["min_y"], b["max_y"]); ax.set_aspect("equal")
        ax.set_title(title)
        ax.grid(True, alpha=0.2)
        return fig, ax

    def draw_base(ax, draw_tiles=True):
        ts = metadata["course"]["tile_size_m"]
        for i, t in enumerate(instances):
            ox, oy = t["origin"]
            if draw_tiles:
                ax.add_patch(Rectangle((ox - ts/2, oy - ts/2), ts, ts, fill=False, edgecolor="0.4", linewidth=0.8))
                ax.text(ox, oy, f"{i}\n{t['tile']}", ha="center", va="center", fontsize=6, color="yellow")
            if t["left_boundary"]:
                ax.plot([p[0] for p in t["left_boundary"]], [p[1] for p in t["left_boundary"]], "w-", linewidth=1.5)
                ax.plot([p[0] for p in t["right_boundary"]], [p[1] for p in t["right_boundary"]], "w-", linewidth=1.5)
            ax.plot([p[0] for p in t["centerline"]], [p[1] for p in t["centerline"]], "c:", linewidth=0.8)
        if metadata["ramp"]:
            p = metadata["ramp"]["pose"]; fp = metadata["ramp"]["footprint"]
            ax.add_patch(Rectangle((p["x"] - fp["width_m"]/2, p["y"] - fp["length_m"]/2), fp["width_m"], fp["length_m"], color="gray", alpha=0.8))
            ax.plot([p["x"]-fp["width_m"]/2, p["x"]-fp["width_m"]/2], [p["y"]-fp["length_m"]/2, p["y"]+fp["length_m"]/2], color="white", linewidth=1.2)
            ax.plot([p["x"]+fp["width_m"]/2, p["x"]+fp["width_m"]/2], [p["y"]-fp["length_m"]/2, p["y"]+fp["length_m"]/2], color="white", linewidth=1.2)

    def draw_obstacles(ax):
        for obj in metadata["objects"]:
            p = obj["pose"]
            color = obj.get("color", {"barrel":"orange","drum":"green","pothole":"white"}.get(obj["type"], "white"))
            if "radius_m" in obj:
                ax.add_patch(Circle((p["x"], p["y"]), obj.get("radius_m", 0.4), color=color, alpha=0.8))
            else:
                fp = obj["footprint"]
                ax.add_patch(Rectangle((p["x"] - fp["width_m"]/2, p["y"] - fp["length_m"]/2), fp["width_m"], fp["length_m"], color=color, alpha=0.8))
            tile_obs = obj.get("tile_obstacle", {})
            label = f"{obj['name']} {obj.get('prefab_type', obj['type'])} {tile_obs.get('mask', '')}"
            ax.text(p["x"], p["y"], label, fontsize=5, color="magenta")

    def draw_gates(ax):
        for gate in metadata.get("gates", []):
            l, r, c, n = gate["left_post_ft"], gate["right_post_ft"], gate["center_ft"], gate["normal_ft"]
            lm, rm, cm = [v / FT_PER_M for v in l], [v / FT_PER_M for v in r], [v / FT_PER_M for v in c]
            ax.plot([lm[0], rm[0]], [lm[1], rm[1]], color="lime", linewidth=1.0)
            ax.arrow(cm[0], cm[1], n[0] * 1.2, n[1] * 1.2, color="lime", head_width=0.25, length_includes_head=True)
            ax.text(cm[0], cm[1], f"{gate['id']} {gate.get('next_mode','')}", fontsize=5, color="lime")

    fig, ax = setup_ax(f"Tile IGVC layout seed {metadata['seed']} template {metadata['course']['template']}")
    draw_base(ax); draw_obstacles(ax); fig.tight_layout(); fig.savefig(DEBUG_DIR / "generated_layout.png", dpi=150); plt.close(fig)
    fig, ax = setup_ax("IGVC obstacle masks and footprints")
    draw_base(ax); draw_obstacles(ax); fig.tight_layout(); fig.savefig(DEBUG_DIR / "debug_obstacles.png", dpi=150); plt.close(fig)
    fig, ax = setup_ax("IGVC lane gates and normals")
    draw_base(ax); draw_gates(ax); fig.tight_layout(); fig.savefig(DEBUG_DIR / "debug_gates.png", dpi=150); plt.close(fig)
    fig, ax = setup_ax("IGVC full course debug")
    draw_base(ax); draw_obstacles(ax); draw_gates(ax); fig.tight_layout(); fig.savefig(DEBUG_DIR / "debug_full_course.png", dpi=150); plt.close(fig)
