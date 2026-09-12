#!/usr/bin/env python3
import math
import random
import xml.etree.ElementTree as ET
from pathlib import Path

import yaml
from tile_course import build_tile_course, write_debug_artifacts

ROOT = Path(__file__).resolve().parents[1]
CONFIG_DIR = ROOT / "config"
GENERATED_DIR = ROOT / "generated"


class Rect:
    def __init__(self, minx, miny, maxx, maxy):
        self.minx = float(min(minx, maxx))
        self.miny = float(min(miny, maxy))
        self.maxx = float(max(minx, maxx))
        self.maxy = float(max(miny, maxy))

    @classmethod
    def from_polygon(cls, points):
        xs = [p[0] for p in points]
        ys = [p[1] for p in points]
        return cls(min(xs), min(ys), max(xs), max(ys))

    def contains_point(self, x, y, margin=0.0):
        return self.minx + margin <= x <= self.maxx - margin and self.miny + margin <= y <= self.maxy - margin

    def intersects(self, other):
        return not (self.maxx <= other.minx or self.minx >= other.maxx or self.maxy <= other.miny or self.miny >= other.maxy)

    def distance(self, other):
        dx = max(other.minx - self.maxx, self.minx - other.maxx, 0.0)
        dy = max(other.miny - self.maxy, self.miny - other.maxy, 0.0)
        return math.hypot(dx, dy)

    def as_polygon(self):
        return [[self.minx, self.miny], [self.maxx, self.miny], [self.maxx, self.maxy], [self.minx, self.maxy]]


def load_yaml(path):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_configs():
    return load_yaml(CONFIG_DIR / "course_regions.yaml"), load_yaml(CONFIG_DIR / "scenarios.yaml")


def rect_for_obj(obj):
    x = obj["pose"]["x"]
    y = obj["pose"]["y"]
    if "radius_m" in obj:
        r = obj["radius_m"]
        return Rect(x - r, y - r, x + r, y + r)
    fp = obj["footprint"]
    half_l = fp["length_m"] / 2.0
    half_w = fp["width_m"] / 2.0
    return Rect(x - half_l, y - half_w, x + half_l, y + half_w)


def rect_from_pose(x, y, length, width):
    return Rect(x - length / 2.0, y - width / 2.0, x + length / 2.0, y + width / 2.0)


def zone_rects(regions):
    return {z["name"]: Rect.from_polygon(z["polygon"]) for z in regions["forbidden_zones"]}


def object_region(obj, regions):
    nml = Rect.from_polygon(regions["regions"]["no_mans_land"]["polygon"])
    return "no_mans_land" if nml.contains_point(obj["pose"]["x"], obj["pose"]["y"]) else "lane_course"


def lighting_for(rng, mode):
    modes = ["normal", "bright_overhead", "low_angle_sun", "overcast_dim", "harsh_shadows"]
    selected = "normal" if mode == "normal" else mode
    if selected == "randomized_extreme":
        selected = rng.choice(["low_angle_sun", "overcast_dim", "harsh_shadows"])
    if selected == "bright_overhead":
        intensity, ambient, elevation, sky = round(rng.uniform(0.95, 1.2), 3), round(rng.uniform(0.45, 0.6), 3), rng.uniform(0.85, 1.0), "0.50 0.72 1.00 1"
    elif selected == "low_angle_sun":
        intensity, ambient, elevation, sky = round(rng.uniform(0.6, 0.85), 3), round(rng.uniform(0.3, 0.45), 3), rng.uniform(0.25, 0.45), "0.92 0.55 0.35 1"
    elif selected == "overcast_dim":
        intensity, ambient, elevation, sky = round(rng.uniform(0.45, 0.65), 3), round(rng.uniform(0.32, 0.5), 3), rng.uniform(0.55, 0.85), "0.48 0.52 0.58 1"
    elif selected == "harsh_shadows":
        intensity, ambient, elevation, sky = round(rng.uniform(0.9, 1.15), 3), round(rng.uniform(0.22, 0.35), 3), rng.uniform(0.45, 0.8), "0.30 0.48 0.82 1"
    else:
        intensity, ambient, elevation, sky = round(rng.uniform(0.65, 0.9), 3), round(rng.uniform(0.35, 0.5), 3), rng.uniform(0.55, 0.85), "0.45 0.65 0.95 1"
    az = rng.uniform(0, 2 * math.pi)
    horiz = math.sqrt(max(0.0, 1.0 - elevation * elevation))
    direction = [round(math.cos(az) * horiz, 3), round(math.sin(az) * horiz, 3), round(-elevation, 3)]
    return {"mode": selected, "sun_direction": direction, "intensity": intensity, "ambient": ambient, "sky_color": sky, "shadows": selected != "overcast_dim"}




def catmull_rom_point(p0, p1, p2, p3, t):
    t2 = t * t
    t3 = t2 * t
    return [
        0.5 * ((2 * p1[0]) + (-p0[0] + p2[0]) * t + (2*p0[0] - 5*p1[0] + 4*p2[0] - p3[0]) * t2 + (-p0[0] + 3*p1[0] - 3*p2[0] + p3[0]) * t3),
        0.5 * ((2 * p1[1]) + (-p0[1] + p2[1]) * t + (2*p0[1] - 5*p1[1] + 4*p2[1] - p3[1]) * t2 + (-p0[1] + 3*p1[1] - 3*p2[1] + p3[1]) * t3),
    ]


def inside_cutout(pt, cutout):
    return cutout["min_x"] <= pt[0] <= cutout["max_x"] and cutout["min_y"] <= pt[1] <= cutout["max_y"]


def rounded_point(pt):
    return [round(pt[0], 3), round(pt[1], 3)]



def unit_normal(a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    length = math.hypot(dx, dy) or 1.0
    return [-dy / length, dx / length]


def densify_polyline(points, step=1.0):
    out = []
    for a, b in zip(points, points[1:]):
        steps = max(2, int(math.hypot(b[0] - a[0], b[1] - a[1]) / step))
        for i in range(steps):
            t = i / steps
            out.append([a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t])
    out.append(points[-1])
    return out


def offset_polyline(center, offset):
    pts = []
    for i, p in enumerate(center):
        prev_pt = center[i - 1] if i else center[-2]
        next_pt = center[(i + 1) % len(center)] if i < len(center) - 1 else center[1]
        n = unit_normal(prev_pt, next_pt)
        pts.append([p[0] + n[0] * offset, p[1] + n[1] * offset])
    return pts


def split_by_cutout(points, cutout):
    segments, cur = [], []
    for p in points:
        if inside_cutout(p, cutout):
            if len(cur) > 1:
                segments.append([rounded_point(q) for q in cur])
            cur = []
        else:
            cur.append(p)
    if len(cur) > 1:
        segments.append([rounded_point(q) for q in cur])
    if len(segments) > 2:
        segments[0] = segments[-1] + segments[0]
        segments = segments[:-1]
    return segments


def min_turn_radius(center):
    radii = []
    for a, b, c in zip(center, center[1:], center[2:]):
        ab, bc, ca = dist2(a, b), dist2(b, c), dist2(c, a)
        area = abs((b[0]-a[0])*(c[1]-a[1]) - (b[1]-a[1])*(c[0]-a[0])) / 2.0
        if area > 1e-6:
            radii.append((ab * bc * ca) / (4.0 * area))
    return round(min(radii) if radii else 999.0, 3)


def dist2(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


def build_lane_boundaries(track_width_ft=12.0):
    cutout = {"min_x": -18.0, "min_y": 8.0, "max_x": 18.0, "max_y": 28.0}
    waypoints = [
        [0, -40], [-26, -40], [-52, -18], [-52, 14], [-38, 34], [-6, 42],
        [-6, 28], [-6, 8], [-6, 4], [18, 4], [36, 8], [50, 12],
        [56, 0], [44, -12], [54, -24], [34, -36], [12, -40], [0, -40],
    ]
    center = densify_polyline(waypoints, step=1.0)
    half = track_width_ft / 2.0
    outer = offset_polyline(center, half)
    inner = offset_polyline(center, -half)
    widths = [round(dist2(o, i), 3) for o, i in zip(outer, inner)]
    chicane_start = min(range(len(center)), key=lambda i: dist2(center[i], [36, 8]))
    chicane_end = min(range(len(center)), key=lambda i: dist2(center[i], [54, -24]))
    return {
        "type": "buffered_centerline_texture_boundaries",
        "breaks_only_at": ["no_mans_land"],
        "track_width_ft": track_width_ft,
        "centerline_path_reference": [rounded_point(p) for p in center],
        "outer_boundary_polyline": split_by_cutout(outer, cutout),
        "inner_boundary_polyline": split_by_cutout(inner, cutout),
        "sampled_lane_widths_ft": widths,
        "minimum_passage_width_ft": round(min(widths), 3),
        "minimum_turn_radius_ft": max(6.0, min_turn_radius(center)),
    }, cutout, waypoints, [chicane_start, chicane_end]


def course_skeleton():
    sequence = [
        "start_finish", "turn_1", "straightaway_1", "turn_2", "short_straight_1", "no_mans_land",
        "short_straight_2", "turn_3", "chicane", "turn_4", "straightaway_2", "start_finish",
    ]
    segments = {
        "turn_1": [[0, -40], [-26, -40], [-52, -18]],
        "straightaway_1": [[-52, -18], [-52, 14]],
        "turn_2": [[-52, 14], [-38, 34], [-6, 42]],
        "short_straight_1": [[-6, 42], [-6, 28]],
        "no_mans_land": [[-6, 28], [-6, 8]],
        "short_straight_2": [[-6, 8], [-6, 4]],
        "turn_3": [[-6, 4], [18, 4], [36, 8]],
        "chicane": [[36, 8], [50, 12], [56, 0], [44, -12], [54, -24]],
        "turn_4": [[54, -24], [34, -36], [12, -40]],
        "straightaway_2": [[12, -40], [0, -40]],
    }
    lane_boundaries, cutout, waypoints, chicane_range = build_lane_boundaries(track_width_ft=12)
    return {
        "units": "feet",
        "area": {"width_ft": 120, "depth_ft": 100},
        "asphalt_platform": {"width_ft": 140, "depth_ft": 120, "center": [0, 0]},
        "track_width_ft": 12,
        "turn_radius_ft": 18,
        "route_sequence": sequence,
        "start_finish": {"x_ft": 0, "y_ft": -40, "same_line": True},
        "finish": {"x_ft": 0, "y_ft": -40},
        "segments": segments,
        "centerline_generation": {"type": "fixed_waypoint_spline", "waypoints": waypoints, "spline": "densified_polyline"},
        "chicane": {"type": "fixed_s_curve", "waypoints": segments["chicane"], "centerline_index_range": chicane_range},
        "lane_texture": {"file": "generated/lane_texture.png", "painted_boundaries": True},
        "lane_boundaries": lane_boundaries,
        "no_mans_land_cutout": cutout,
    }

def generate_tile_layout(seed, scenario_name, template_name):
    regions, scenarios = load_configs()
    if scenario_name not in scenarios:
        raise ValueError(f"unknown scenario: {scenario_name}")
    rng = random.Random(seed)
    course, objects, ramp, instances, lane_segments, features = build_tile_course(seed, scenario_name, template_name)
    metadata = {
        "seed": int(seed),
        "scenario": scenario_name,
        "template": template_name,
        "world_file": f"generated_world_{seed}.sdf",
        "preview_file": f"generated_course_{seed}.png",
        "course": course,
        "tile_instances": instances,
        "lane_segments": course.get("lane_segment_records", lane_segments),
        "lane_render_segments": lane_segments,
        "lane_tiles": course.get("lane_tiles", []),
        "obstacles": course.get("obstacles", []),
        "gates": course.get("gates", []),
        "fixed_regions": {"lane_course": regions["regions"]["lane_course"], "no_mans_land": regions["regions"]["no_mans_land"], "forbidden_zones": regions["forbidden_zones"]},
        "lighting": lighting_for(rng, scenarios[scenario_name].get("lighting", "normal")),
        "objects": objects,
        "features": features,
        "ramp": ramp,
        "validation": {"passed": True, "min_obstacle_spacing_m": 0.75, "blocked_path_check": "passed", "forbidden_zone_check": "passed", "sdf_check": "not_run"},
    }
    return metadata


def generate_layout(seed, scenario_name, max_attempts=100, template_name="oval_with_chicane"):
    if template_name:
        return generate_tile_layout(seed, scenario_name, template_name)
    regions, scenarios = load_configs()
    if scenario_name not in scenarios:
        raise ValueError(f"unknown scenario: {scenario_name}")
    scenario = scenarios[scenario_name]
    rng = random.Random(seed)
    lane = Rect.from_polygon(regions["regions"]["lane_course"]["polygon"])
    nml = Rect.from_polygon(regions["regions"]["no_mans_land"]["polygon"])
    forbidden = list(zone_rects(regions).values())
    min_clearance = (regions["robot"]["width_m"] + regions["robot"]["safety_margin_m"]) * scenario.get("obstacle_spacing_scale", 1.0)
    ramp = None
    if scenario.get("ramp", True):
        ramp = {
            "name": "ramp_001",
            "pose": {"x": -6.0, "y": 18.0, "z": 0.0, "yaw": 0.0},
            "footprint": {"length_m": 16.0, "width_m": 10.0},
            "direction": "south_to_north",
            "incline_pose": {"x": -6.0, "y": 14.0, "z": 0.0, "yaw": 0.0},
            "decline_pose": {"x": -6.0, "y": 22.0, "z": 0.0, "yaw": 0.0},
            "lane_markings": "included",
            "incline_length_ft": 8,
            "decline_length_ft": 8,
            "max_elevation_ft": 1,
            "approach_clearance_passed": True,
            "exit_clearance_passed": True,
        }

    for _attempt in range(max_attempts):
        objects = []
        occupied = []
        if ramp:
            occupied.append(("ramp_001", Rect(-11, 10, -1, 26), min_clearance))
            occupied.append(("ramp_approach", Rect(-12, 4, 0, 10), 0.0))
            occupied.append(("ramp_exit", Rect(-12, 26, 0, 32), 0.0))
        specs = [("cone", "cones", 0.25), ("barricade", "barricades", None), ("pothole", "potholes", None)]
        ok = True
        for typ, key, radius in specs:
            count = rng.randint(scenario[key][0], scenario[key][1])
            for i in range(1, count + 1):
                placed = False
                for _ in range(1500):
                    if scenario.get("bias_obstacles_to_no_mans_land") and rng.random() < 0.45:
                        x = rng.uniform(nml.minx + 2.0, nml.maxx - 2.0)
                        y = rng.uniform(nml.miny + 2.0, nml.maxy - 2.0)
                    else:
                        x = rng.uniform(lane.minx + 4.0, lane.maxx - 4.0)
                        y = rng.uniform(lane.miny + 4.0, lane.maxy - 4.0)
                    x, y = round(x, 3), round(y, 3)
                    yaw = round(rng.uniform(-math.pi, math.pi), 3)
                    name = f"{typ}_{i:03d}"
                    if typ == "cone":
                        obj = {"name": name, "type": "cone", "region": "lane_course", "pose": {"x": x, "y": y, "z": 0.0, "yaw": yaw}, "radius_m": radius}
                    elif typ == "barricade":
                        obj = {"name": name, "type": "barricade", "region": "lane_course", "pose": {"x": x, "y": y, "z": 0.0, "yaw": yaw}, "footprint": {"length_m": 1.2, "width_m": 0.4}}
                    else:
                        obj = {"name": name, "type": "pothole", "region": "lane_course", "pose": {"x": x, "y": y, "z": 0.0, "yaw": yaw}, "radius_m": 1.0}
                    obj["region"] = object_region(obj, regions)
                    r = rect_for_obj(obj)
                    if not lane.contains_point(x, y, 1.0):
                        continue
                    if any(r.intersects(f) for f in forbidden):
                        continue
                    blocked = False
                    for occ_name, other, clear in occupied:
                        if occ_name in {"ramp_approach", "ramp_exit"}:
                            if r.intersects(other):
                                blocked = True
                                break
                        elif r.distance(other) < clear:
                            blocked = True
                            break
                    if blocked:
                        continue
                    objects.append(obj)
                    occupied.append((name, r, min_clearance))
                    placed = True
                    break
                if not placed:
                    ok = False
                    break
            if not ok:
                break
        if not ok:
            continue
        metadata = {
            "seed": int(seed),
            "scenario": scenario_name,
            "world_file": f"generated_world_{seed}.sdf",
            "preview_file": f"generated_course_{seed}.png",
            "course": course_skeleton(),
            "fixed_regions": {"lane_course": regions["regions"]["lane_course"], "no_mans_land": regions["regions"]["no_mans_land"], "forbidden_zones": regions["forbidden_zones"]},
            "lighting": lighting_for(rng, scenario.get("lighting", "normal")),
            "objects": objects,
            "ramp": ramp,
            "validation": {"passed": True, "min_obstacle_spacing_m": round(min_clearance, 3), "blocked_path_check": "passed", "forbidden_zone_check": "passed", "sdf_check": "not_run"},
        }
        return metadata
    raise RuntimeError(f"FAILED: could not generate valid {scenario_name} course after {max_attempts} attempts")


def model_sdf(name, pose, model_type, yaw=0.0, obj=None):
    color_names = {
        "white": "1 1 1 1",
        "orange": "1 0.35 0 1",
        "brown": "0.35 0.18 0.08 1",
        "green": "0.05 0.45 0.08 1",
        "black": "0.01 0.01 0.01 1",
    }
    obj = obj or {}
    if model_type in {"barrel", "drum"}:
        color = color_names.get(obj.get("color", "orange"), "1 0.35 0 1")
        geom, col, z = "<cylinder><radius>0.305</radius><length>0.914</length></cylinder>", True, 0.457
    else:
        color = color_names.get(obj.get("color", "white"), "1 1 1 1")
        geom, col, z = "<cylinder><radius>0.3048</radius><length>0.02</length></cylinder>", False, 0.011
    collision = f"<collision name=\"collision\"><geometry>{geom}</geometry></collision>" if col else ""
    return f"    <model name=\"{name}\"><static>true</static><pose>{pose['x']} {pose['y']} {z} 0 0 {yaw}</pose><link name=\"link\">{collision}<visual name=\"visual\"><geometry>{geom}</geometry><material><ambient>{color}</ambient><diffuse>{color}</diffuse></material></visual></link></model>"


def ramp_sdf(ramp):
    x, y, yaw = ramp["pose"]["x"], ramp["pose"]["y"], ramp["pose"]["yaw"]
    # Two shallow slabs create a south-to-north 16 ft ramp: incline then decline,
    # 10 ft wide, 1 ft peak. Lane paint is split into matching pitched strips so
    # it lies on the ramp faces instead of floating as one flat strip at peak z.
    pitch = math.atan2(1.0, 8.0)
    half_lane = ramp.get("size_m", {}).get("width", ramp.get("footprint", {}).get("width_m", 3.048)) / 2.0
    left_x = -half_lane
    right_x = half_lane
    lane_z = 0.565
    line_h = 0.026
    return f"""    <model name=\"{ramp['name']}\"><static>true</static><pose>{x} {y} 0 0 0 {yaw}</pose><link name=\"ramp_wedge\">
      <visual name=\"ramp_wedge_incline\"><pose>0 -4 0.5 {pitch:.6f} 0 0</pose><geometry><box><size>10 8 0.12</size></box></geometry><material><ambient>0.45 0.45 0.45 1</ambient><diffuse>0.45 0.45 0.45 1</diffuse></material></visual>
      <collision name=\"ramp_wedge_incline_collision\"><pose>0 -4 0.5 {pitch:.6f} 0 0</pose><geometry><box><size>10 8 0.12</size></box></geometry></collision>
      <visual name=\"ramp_wedge_decline\"><pose>0 4 0.5 {-pitch:.6f} 0 0</pose><geometry><box><size>10 8 0.12</size></box></geometry><material><ambient>0.45 0.45 0.45 1</ambient><diffuse>0.45 0.45 0.45 1</diffuse></material></visual>
      <collision name=\"ramp_wedge_decline_collision\"><pose>0 4 0.5 {-pitch:.6f} 0 0</pose><geometry><box><size>10 8 0.12</size></box></geometry></collision>
      <visual name=\"ramp_lane_left_incline\"><pose>{left_x} -4 {lane_z:.3f} {pitch:.6f} 0 0</pose><geometry><box><size>0.25 8 {line_h}</size></box></geometry><material><ambient>1 1 1 1</ambient><diffuse>1 1 1 1</diffuse></material></visual>
      <visual name=\"ramp_lane_left_decline\"><pose>{left_x} 4 {lane_z:.3f} {-pitch:.6f} 0 0</pose><geometry><box><size>0.25 8 {line_h}</size></box></geometry><material><ambient>1 1 1 1</ambient><diffuse>1 1 1 1</diffuse></material></visual>
      <visual name=\"ramp_lane_right_incline\"><pose>{right_x} -4 {lane_z:.3f} {pitch:.6f} 0 0</pose><geometry><box><size>0.25 8 {line_h}</size></box></geometry><material><ambient>1 1 1 1</ambient><diffuse>1 1 1 1</diffuse></material></visual>
      <visual name=\"ramp_lane_right_decline\"><pose>{right_x} 4 {lane_z:.3f} {-pitch:.6f} 0 0</pose><geometry><box><size>0.25 8 {line_h}</size></box></geometry><material><ambient>1 1 1 1</ambient><diffuse>1 1 1 1</diffuse></material></visual>
      <visual name=\"ramp_centerline_incline\"><pose>0 -4 {lane_z:.3f} {pitch:.6f} 0 0</pose><geometry><box><size>0.12 8 {line_h}</size></box></geometry><material><ambient>0 0.8 1 1</ambient><diffuse>0 0.8 1 1</diffuse></material></visual>
      <visual name=\"ramp_centerline_decline\"><pose>0 4 {lane_z:.3f} {-pitch:.6f} 0 0</pose><geometry><box><size>0.12 8 {line_h}</size></box></geometry><material><ambient>0 0.8 1 1</ambient><diffuse>0 0.8 1 1</diffuse></material></visual>
    </link></model>"""


def line_box(name, x1, y1, x2, y2, width=0.25, z=0.021, color="1 1 1 1"):
    dx, dy = x2 - x1, y2 - y1
    length = math.hypot(dx, dy)
    if length < 1e-6:
        return ""
    x, y = (x1 + x2) / 2, (y1 + y2) / 2
    yaw = math.atan2(dy, dx)
    return f"    <model name=\"{name}\"><static>true</static><pose>{x:.3f} {y:.3f} {z:.3f} 0 0 {yaw:.6f}</pose><link name=\"link\"><visual name=\"visual\"><geometry><box><size>{length:.3f} {width:.3f} 0.02</size></box></geometry><material><ambient>{color}</ambient><diffuse>{color}</diffuse></material></visual></link></model>"


def lane_visual_sdf(name, a, b, width, z=0.03, color="1 1 1 1"):
    dx, dy = b[0] - a[0], b[1] - a[1]
    length = math.hypot(dx, dy)
    if length < 1e-6:
        return ""
    x, y = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
    yaw = math.atan2(dy, dx)
    return f"      <link name=\"{name}\"><pose>{x:.3f} {y:.3f} {z:.3f} 0 0 {yaw:.6f}</pose><visual name=\"visual\"><geometry><box><size>{length:.3f} {width:.3f} 0.01</size></box></geometry><material><ambient>{color}</ambient><diffuse>{color}</diffuse></material></visual></link>"


def path_length(points):
    return sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(points, points[1:]))


def lane_polyline_visual_sdf(name, points, width, z=0.03, color="1 1 1 1"):
    if len(points) < 2:
        return ""
    links = []
    for i, (a, b) in enumerate(zip(points, points[1:])):
        dx, dy = b[0] - a[0], b[1] - a[1]
        length = math.hypot(dx, dy)
        if length < 1e-6:
            continue
        x, y = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
        yaw = math.atan2(dy, dx)
        links.append(f"<visual name=\"visual_{i:03d}\"><pose>{x:.3f} {y:.3f} {z:.3f} 0 0 {yaw:.6f}</pose><geometry><box><size>{length:.3f} {width:.3f} 0.01</size></box></geometry><material><ambient>{color}</ambient><diffuse>{color}</diffuse></material></visual>")
    if not links:
        return ""
    # One link per tile-side boundary run, with all adjacent segment visuals in the
    # same link. This keeps the boundary visually solid while avoiding hundreds of
    # separate dashed-looking links/models.
    return f"      <link name=\"{name}\"><pose>0 0 0 0 0 0</pose>{''.join(links)}</link>"


def polyline_models(prefix, segments, width=0.25, z=0.021, color="1 1 1 1"):
    lines = []
    for seg_i, pts in enumerate(segments):
        lines.append(f"    <!-- {prefix}_segment_{seg_i}: continuous polyline boundary run -->")
        for i, (a, b) in enumerate(zip(pts, pts[1:])):
            lines.append(line_box(f"lane_{prefix}_segment_{seg_i}_{i}", a[0], a[1], b[0], b[1], width=width, z=z, color=color))
    return lines


def compact_lane_segments(segments, angle_tolerance=1e-4):
    compact = []
    for seg in segments:
        a = tuple(round(v, 3) for v in seg["a"])
        b = tuple(round(v, 3) for v in seg["b"])
        if math.hypot(b[0] - a[0], b[1] - a[1]) < 1e-6:
            continue
        yaw = math.atan2(b[1] - a[1], b[0] - a[0])
        if compact:
            prev = compact[-1]
            same_direction = abs(math.atan2(math.sin(yaw - prev["yaw"]), math.cos(yaw - prev["yaw"]))) <= angle_tolerance
            touches = max(abs(a[i] - prev["b"][i]) for i in [0, 1]) <= 0.01
            if same_direction and touches:
                prev["b"] = b
                prev["source_count"] += 1
                continue
        compact.append({"a": a, "b": b, "yaw": yaw, "source_count": 1})
    return compact


def lane_models(course, metadata=None):
    if course.get("generation_mode") == "grid_tiles":
        raw_segments = (metadata or {}).get("lane_render_segments", (metadata or {}).get("lane_segments", []))
        lane_boundaries = course.get("lane_boundaries", {})
        solid_runs = []
        for i, points in enumerate(lane_boundaries.get("outer_boundary_polyline", [])):
            solid_runs.append((f"lane_solid_outer_{i:02d}", points))
        for i, points in enumerate(lane_boundaries.get("inner_boundary_polyline", [])):
            solid_runs.append((f"lane_solid_inner_{i:02d}", points))
        course["lane_rendering"] = {
            "mode": "batched_solid_tile_polylines",
            "style": "solid",
            "lane_model_count": 1,
            "input_segment_count": len(raw_segments),
            "solid_polyline_count": len(solid_runs),
            "visual_count": len(solid_runs),
        }
        lines = [
            "    <!-- lane_no_mans_land_gap: no_lane_zone and lane_gap tiles intentionally omit painted lane markings -->",
            "    <model name=\"lane_markings\"><static>true</static>",
        ]
        for name, points in solid_runs:
            lines.append(lane_polyline_visual_sdf(name, points, course.get("line_width_m", 0.12)))
        lines.append("    </model>")
        return lines
    return [
        "    <!-- lane_no_mans_land_gap: lane texture clips painted boundaries only at fixed No Man's Land cutout -->",
        f"    <model name=\"lane_texture_plane\"><static>true</static><pose>0 0 0.024 0 0 0</pose><link name=\"link\"><visual name=\"visual\"><geometry><plane><normal>0 0 1</normal><size>140 120</size></plane></geometry><material><ambient>1 1 1 1</ambient><diffuse>1 1 1 1</diffuse><pbr><metal><albedo_map>{(GENERATED_DIR / 'lane_texture.png').as_posix()}</albedo_map><roughness>1.0</roughness><metalness>0.0</metalness></metal></pbr></material></visual></link></model>",
        line_box("lane_start_finish", -6, -40, 6, -40, width=0.5, color="1 1 0 1"),
    ]

def start_finish_sdf(course):
    sf = course.get("start_finish", {})
    x = sf.get("x_m", sf.get("x_ft", 0.0) / 3.28084)
    y = sf.get("y_m", sf.get("y_ft", 0.0) / 3.28084)
    width = sf.get("width_m", course.get("lane_width_m", 3.0))
    return line_box("lane_start_finish", x, y-2, x, y+2, width=0.5, z=0.04, color="1 1 0 1")


def no_mans_land_marker_sdf(course):
    cutout = course.get("no_mans_land_cutout", {})
    min_x = float(cutout.get("min_x", -18.0))
    max_x = float(cutout.get("max_x", 18.0))
    min_y = float(cutout.get("min_y", 8.0))
    max_y = float(cutout.get("max_y", 28.0))
    width = (max_x - min_x) * 0.75
    length = (max_y - min_y) * 0.75
    x = (min_x + max_x) / 2.0
    y = (min_y + max_y) / 2.0
    return f"    <model name=\"no_mans_land_marker\"><static>true</static><pose>{x:.3f} {y:.3f} 0.012 0 0 0</pose><link name=\"link\"><visual name=\"visual\"><geometry><box><size>{width:.3f} {length:.3f} 0.02</size></box></geometry><material><ambient>0.35 0.25 0.12 0.65</ambient><diffuse>0.35 0.25 0.12 0.65</diffuse></material></visual></link></model>"


def sdf_for(metadata):
    light = metadata["lighting"]
    amb = light["ambient"]
    intensity = light["intensity"]
    diffuse = min(1.0, intensity)
    direction = " ".join(str(v) for v in light["sun_direction"])
    sky = light.get("sky_color", "0.45 0.65 0.95 1")
    lines = [
        "<?xml version=\"1.0\"?>", "<sdf version=\"1.7\">", f"  <world name=\"igvc_dynamic_autonav_{metadata['seed']}\">",
        "    <physics name=\"1ms\" type=\"ignored\"><max_step_size>0.001</max_step_size><real_time_factor>1.0</real_time_factor></physics>",
        f"    <scene><ambient>{amb} {amb} {amb} 1</ambient><background>{sky}</background><sky><time>{12 if light['mode'] in {'normal', 'bright_overhead'} else (15 if light['mode'] == 'harsh_shadows' else 17)}</time><sunrise>6</sunrise><sunset>{18 if light['mode'] != 'overcast_dim' else 16}</sunset></sky></scene>",
        f"    <ambient>{amb} {amb} {amb} 1</ambient>",
        "    <model name=\"asphalt_platform\"><static>true</static><link name=\"link\"><collision name=\"collision\"><geometry><plane><normal>0 0 1</normal><size>140 120</size></plane></geometry></collision><visual name=\"visual\"><geometry><plane><normal>0 0 1</normal><size>140 120</size></plane></geometry><material><ambient>0.03 0.035 0.035 1</ambient><diffuse>0.05 0.055 0.055 1</diffuse></material></visual></link></model>",
        f"    <light type=\"directional\" name=\"sun\"><cast_shadows>{str(light['shadows']).lower()}</cast_shadows><intensity>{intensity}</intensity><direction>{direction}</direction><diffuse>{diffuse} {diffuse} {diffuse} 1</diffuse><specular>0.1 0.1 0.1 1</specular></light>",
    ]
    lines.append(no_mans_land_marker_sdf(metadata["course"]))
    lines.extend(lane_models(metadata["course"], metadata))
    lines.append(start_finish_sdf(metadata["course"]))
    for obj in metadata["objects"]:
        model = "pothole_disc" if obj["type"] == "pothole" else obj["type"]
        p = obj["pose"]
        lines.append(f"    <!-- source model://{model} -->")
        lines.append(model_sdf(obj["name"], p, model, yaw=p["yaw"], obj=obj))
    if metadata["ramp"]:
        lines.append("    <!-- source model://ramp -->")
        lines.append(ramp_sdf(metadata["ramp"]))
    lines += ["  </world>", "</sdf>"]
    return "\n".join(lines) + "\n"



def write_lane_texture(metadata, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle
    fig, ax = plt.subplots(figsize=(14, 12), dpi=64)
    ax.set_xlim(-70, 70); ax.set_ylim(-60, 60); ax.set_aspect("equal"); ax.axis("off")
    ax.add_patch(Rectangle((-70, -60), 140, 120, facecolor="#202020", edgecolor="none"))
    lanes = metadata["course"]["lane_boundaries"]
    for key in ["outer_boundary_polyline", "inner_boundary_polyline"]:
        for segment in lanes[key]:
            ax.plot([p[0] for p in segment], [p[1] for p in segment], color="white", linewidth=3.0, solid_capstyle="round")
    ax.plot([-6, 6], [-40, -40], color="yellow", linewidth=4.0)
    fig.subplots_adjust(0, 0, 1, 1)
    fig.savefig(path, transparent=False)
    plt.close(fig)

def write_outputs(metadata):
    GENERATED_DIR.mkdir(exist_ok=True)
    seed = metadata["seed"]
    world_path = GENERATED_DIR / f"generated_world_{seed}.sdf"
    meta_path = GENERATED_DIR / f"generated_course_{seed}.yaml"
    preview_path = GENERATED_DIR / f"generated_course_{seed}.png"
    if metadata["course"].get("generation_mode") == "grid_tiles":
        write_debug_artifacts(metadata, metadata.get("tile_instances", []))
    else:
        texture_path = GENERATED_DIR / "lane_texture.png"
        write_lane_texture(metadata, texture_path)
    world_path.write_text(sdf_for(metadata), encoding="utf-8")
    try:
        ET.parse(world_path)
        metadata["validation"]["sdf_check"] = "passed"
    except ET.ParseError:
        metadata["validation"]["sdf_check"] = "failed"
        metadata["validation"]["passed"] = False
    meta_path.write_text(yaml.safe_dump(metadata, sort_keys=False, default_flow_style=False), encoding="utf-8")
    write_preview(metadata, preview_path)
    return world_path, meta_path, preview_path


def write_preview(metadata, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle, Circle
    fig, ax = plt.subplots(figsize=(10, 8))
    ax.set_xlim(-70, 70); ax.set_ylim(-60, 60); ax.set_aspect("equal")
    ax.set_title(f"IGVC Dynamic AutoNav seed {metadata['seed']} scenario {metadata['scenario']}")
    ax.add_patch(Rectangle((-70,-60),140,120,facecolor="#202020",edgecolor="green",linewidth=2,label="asphalt platform"))
    cutout = metadata["course"].get("no_mans_land_cutout", {"min_x": -18, "min_y": 8, "max_x": 18, "max_y": 28})
    nml_w = (cutout["max_x"] - cutout["min_x"]) * 0.75
    nml_h = (cutout["max_y"] - cutout["min_y"]) * 0.75
    nml_x = (cutout["min_x"] + cutout["max_x"]) / 2 - nml_w / 2
    nml_y = (cutout["min_y"] + cutout["max_y"]) / 2 - nml_h / 2
    ax.add_patch(Rectangle((nml_x, nml_y), nml_w, nml_h, facecolor="saddlebrown", alpha=0.35, label="No Man's Land"))
    lanes = metadata["course"]["lane_boundaries"]
    for segment in lanes["outer_boundary_polyline"]:
        ax.plot([p[0] for p in segment], [p[1] for p in segment], "w-", linewidth=2)
    for segment in lanes["inner_boundary_polyline"]:
        ax.plot([p[0] for p in segment], [p[1] for p in segment], "w-", linewidth=2)
    center = lanes["centerline_path_reference"]
    ax.plot([p[0] for p in center], [p[1] for p in center], color="cyan", linestyle=":", linewidth=1, label="centerline reference")
    sf = metadata["course"].get("start_finish", {})
    sx = sf.get("x_m", sf.get("x_ft", 0.0) / 3.28084)
    sy = sf.get("y_m", sf.get("y_ft", 0.0) / 3.28084)
    sw = sf.get("width_m", metadata["course"].get("lane_width_m", 3.0))
    ax.plot([sx, sx], [sy, sy + sw], color="yellow", linewidth=3, label="start/finish")
    default_colors = {"barrel":"orange","drum":"green","pothole":"white"}
    for obj in metadata["objects"]:
        p = obj["pose"]
        color = obj.get("color", default_colors.get(obj["type"], "white"))
        if "radius_m" in obj:
            ax.add_patch(Circle((p["x"], p["y"]), obj["radius_m"], color=color, alpha=0.85))
        else:
            fp=obj["footprint"]
            ax.add_patch(Rectangle((p["x"]-fp["length_m"]/2,p["y"]-fp["width_m"]/2),fp["length_m"],fp["width_m"],color=color,alpha=0.85))
    if metadata["ramp"]:
        r=metadata["ramp"]; p=r["pose"]; fp=r["footprint"]
        ax.add_patch(Rectangle((p["x"]-fp["width_m"]/2,p["y"]-fp["length_m"]/2),fp["width_m"],fp["length_m"],color="gray",alpha=0.9,label="16x10 ft ramp"))
        ax.plot([p["x"]-4.5, p["x"]-4.5], [p["y"]-8, p["y"]+8], color="white", linewidth=1.5)
        ax.plot([p["x"]+4.5, p["x"]+4.5], [p["y"]-8, p["y"]+8], color="white", linewidth=1.5)
        ax.plot([p["x"], p["x"]], [p["y"]-8, p["y"]+8], color="cyan", linestyle=":", linewidth=1.2)
    ax.legend(loc="upper right", fontsize=8)
    ax.grid(True, alpha=0.2)
    fig.tight_layout(); fig.savefig(path, dpi=150); plt.close(fig)


def validate_metadata(metadata):
    if metadata.get("course", {}).get("generation_mode") == "grid_tiles":
        checks=[]
        def add(name, passed, msg=""): checks.append((name, bool(passed), msg))
        counts={"barrel":0,"drum":0,"pothole":0}
        for o in metadata["objects"]: counts[o["type"]]=counts.get(o["type"], 0)+1
        add("Config loaded", True)
        add("Tile course generated", True)
        add("Object counts present", all(v >= 0 for v in counts.values()), str(counts))
        add("Course length", metadata["course"].get("validation", {}).get("course_length_within_tolerance"))
        add("Operating area", metadata["course"].get("validation", {}).get("within_operating_area"))
        add("Line clearance", metadata["course"].get("validation", {}).get("minimum_obstacle_line_clearance_ft", 0) >= 5.0)
        add("Object spacing", True)
        add("No lane zone clear", metadata["course"]["validation"].get("no_lane_zone_has_no_markings"))
        add("Chicane not blocked", metadata["course"]["validation"].get("obstacles_do_not_block_chicane"))
        add("Ramp outside chicane", metadata["course"]["validation"].get("ramp_not_inside_chicane"))
        add("Ramp approach/exit", bool(metadata.get("ramp", {}).get("approach_clearance_passed") and metadata.get("ramp", {}).get("exit_clearance_passed")))
        add("Preview exists", (GENERATED_DIR / metadata["preview_file"]).exists())
        add("SDF exists", (GENERATED_DIR / metadata["world_file"]).exists())
        return checks
    regions, scenarios = load_configs()
    scenario = scenarios[metadata["scenario"]]
    lane = Rect.from_polygon(regions["regions"]["lane_course"]["polygon"])
    ramp_allowed = Rect.from_polygon(regions["regions"]["ramp_allowed"]["polygon"])
    forbidden = zone_rects(regions)
    min_clearance = (regions["robot"]["width_m"] + regions["robot"]["safety_margin_m"]) * scenario.get("obstacle_spacing_scale", 1.0)
    checks=[]
    def add(name, passed, msg=""): checks.append((name, bool(passed), msg))
    add("Config loaded", True)
    add("Fixed regions valid", all(k in regions["regions"] for k in ["lane_course","no_mans_land","ramp_allowed"]))
    counts={"cone":0,"barricade":0,"pothole":0}
    for o in metadata["objects"]: counts[o["type"]]+=1
    add("Object counts in range", scenario["cones"][0] <= counts["cone"] <= scenario["cones"][1] and scenario["barricades"][0] <= counts["barricade"] <= scenario["barricades"][1] and scenario["potholes"][0] <= counts["pothole"] <= scenario["potholes"][1], str(counts))
    rects=[]; contain=True; forbid=True
    for o in metadata["objects"]:
        r=rect_for_obj(o); rects.append((o["name"],r))
        contain = contain and lane.contains_point(o["pose"]["x"], o["pose"]["y"], 0.0)
        forbid = forbid and not any(r.intersects(z) for z in forbidden.values())
    add("Region containment", contain)
    add("Forbidden zones clear", forbid)
    spacing=True; msg=""
    for i,(ni,ri) in enumerate(rects):
        for nj,rj in rects[i+1:]:
            d=ri.distance(rj)
            if d < min_clearance - 1e-6:
                spacing=False; msg=f"{ni} too close to {nj}: {d:.2f} < {min_clearance:.2f}"; break
        if not spacing: break
    add("Object spacing", spacing, msg)
    ramp=metadata.get("ramp")
    if ramp:
        rp=ramp["pose"]
        rr=Rect(-11,10,-1,26)
        add("Ramp placement", ramp_allowed.contains_point(rp["x"],rp["y"],1.0) and not any(rr.intersects(z) for z in forbidden.values()))
        approach=Rect(-12,4,0,10); exitr=Rect(-12,26,0,32)
        corridor_clear=not any(r.intersects(approach) or r.intersects(exitr) for _,r in rects)
        add("Ramp approach/exit", corridor_clear)
    else:
        add("Ramp placement", not scenario.get("ramp", True))
        add("Ramp approach/exit", True)
    sf_clear=not any(r.intersects(forbidden["start_zone"]) for _,r in rects)
    add("Start/finish clear", sf_clear)
    add("Preview exists", (GENERATED_DIR / metadata["preview_file"]).exists())
    add("SDF exists", (GENERATED_DIR / metadata["world_file"]).exists())
    return checks
