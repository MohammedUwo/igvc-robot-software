import math


def _round_point(p, ndigits=6):
    return [round(float(p[0]), ndigits), round(float(p[1]), ndigits)]


def rotate_point(point, angle_deg):
    x, y = point
    a = math.radians(angle_deg)
    ca, sa = math.cos(a), math.sin(a)
    return _round_point([x * ca - y * sa, x * sa + y * ca])


def transform_point(local_point, tile_origin, tile_rotation):
    r = rotate_point(local_point, tile_rotation)
    return _round_point([tile_origin[0] + r[0], tile_origin[1] + r[1]])


def distance(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


def sample_polyline(points, spacing=0.5):
    sampled = []
    for a, b in zip(points, points[1:]):
        seg_len = distance(a, b)
        steps = max(1, int(math.ceil(seg_len / spacing)))
        for i in range(steps):
            if sampled and i == 0:
                continue
            t = i / steps
            sampled.append(_round_point([a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t]))
    sampled.append(_round_point(points[-1]))
    return sampled


def _catmull_rom_point(p0, p1, p2, p3, t):
    t2, t3 = t * t, t * t * t
    return [
        0.5 * ((2 * p1[0]) + (-p0[0] + p2[0]) * t + (2*p0[0] - 5*p1[0] + 4*p2[0] - p3[0]) * t2 + (-p0[0] + 3*p1[0] - 3*p2[0] + p3[0]) * t3),
        0.5 * ((2 * p1[1]) + (-p0[1] + p2[1]) * t + (2*p0[1] - 5*p1[1] + 4*p2[1] - p3[1]) * t2 + (-p0[1] + 3*p1[1] - 3*p2[1] + p3[1]) * t3),
    ]


def sample_catmull_rom(points, spacing=0.5):
    if len(points) < 3:
        return sample_polyline(points, spacing)
    # Use a monotone quadratic Bezier through each 3-point turn/chicane control
    # instead of an open Catmull-Rom spline. Catmull-Rom can overshoot compact IGVC
    # tiles; the overshoot was enough to make offset lane boundaries fold and cross.
    sampled = []
    if len(points) == 3:
        p0, p1, p2 = points
        approx_len = distance(p0, p1) + distance(p1, p2)
        steps = max(8, int(math.ceil(approx_len / spacing)))
        for step in range(steps):
            t = step / steps
            omt = 1.0 - t
            sampled.append(_round_point([
                omt * omt * p0[0] + 2 * omt * t * p1[0] + t * t * p2[0],
                omt * omt * p0[1] + 2 * omt * t * p1[1] + t * t * p2[1],
            ]))
        sampled.append(_round_point(p2))
        return sampled
    return sample_polyline(points, spacing)


def compute_normals(sampled_centerline):
    normals = []
    n = len(sampled_centerline)
    for i, p in enumerate(sampled_centerline):
        if i == 0:
            a, b = p, sampled_centerline[i + 1]
        elif i == n - 1:
            a, b = sampled_centerline[i - 1], p
        else:
            a, b = sampled_centerline[i - 1], sampled_centerline[i + 1]
        dx, dy = b[0] - a[0], b[1] - a[1]
        length = math.hypot(dx, dy) or 1.0
        normals.append([-dy / length, dx / length])
    return normals


def _line_intersection(p1, p2, p3, p4):
    x1, y1 = p1
    x2, y2 = p2
    x3, y3 = p3
    x4, y4 = p4
    den = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
    if abs(den) < 1e-9:
        return None
    px = ((x1*y2 - y1*x2) * (x3 - x4) - (x1 - x2) * (x3*y4 - y3*x4)) / den
    py = ((x1*y2 - y1*x2) * (y3 - y4) - (y1 - y2) * (x3*y4 - y3*x4)) / den
    return [px, py]


def _segment_normal(a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    length = math.hypot(dx, dy) or 1.0
    return [-dy / length, dx / length]


def offset_centerline(centerline, offset_distance):
    """Offset an open sampled polyline using mitered joins.

    Averaging vertex normals can fold compact S-curves into themselves. This builds
    per-segment offset lines, then intersects adjacent offset lines at each join.
    """
    if len(centerline) < 2:
        return [_round_point(p) for p in centerline]
    offset_segments = []
    for a, b in zip(centerline, centerline[1:]):
        n = _segment_normal(a, b)
        oa = [a[0] + n[0] * offset_distance, a[1] + n[1] * offset_distance]
        ob = [b[0] + n[0] * offset_distance, b[1] + n[1] * offset_distance]
        offset_segments.append((oa, ob))
    pts = [offset_segments[0][0]]
    for i in range(1, len(offset_segments)):
        prev_a, prev_b = offset_segments[i - 1]
        cur_a, cur_b = offset_segments[i]
        joined = _line_intersection(prev_a, prev_b, cur_a, cur_b)
        if joined is None or distance(joined, centerline[i]) > abs(offset_distance) * 4.0:
            joined = [(prev_b[0] + cur_a[0]) / 2.0, (prev_b[1] + cur_a[1]) / 2.0]
        pts.append(joined)
    pts.append(offset_segments[-1][1])
    return [_round_point(p) for p in pts]


def _orientation(a, b, c):
    v = (b[1] - a[1]) * (c[0] - b[0]) - (b[0] - a[0]) * (c[1] - b[1])
    if abs(v) < 1e-9:
        return 0
    return 1 if v > 0 else 2


def _on_segment(a, b, c):
    return min(a[0], c[0]) - 1e-9 <= b[0] <= max(a[0], c[0]) + 1e-9 and min(a[1], c[1]) - 1e-9 <= b[1] <= max(a[1], c[1]) + 1e-9


def segments_intersect(a, b, c, d):
    if a in (c, d) or b in (c, d):
        return False
    o1, o2, o3, o4 = _orientation(a, b, c), _orientation(a, b, d), _orientation(c, d, a), _orientation(c, d, b)
    if o1 != o2 and o3 != o4:
        return True
    return (o1 == 0 and _on_segment(a, c, b)) or (o2 == 0 and _on_segment(a, d, b)) or (o3 == 0 and _on_segment(c, a, d)) or (o4 == 0 and _on_segment(c, b, d))


def polyline_self_intersects(polyline):
    segs = list(zip(polyline, polyline[1:]))
    for i, (a, b) in enumerate(segs):
        for j, (c, d) in enumerate(segs):
            if abs(i - j) <= 1:
                continue
            if segments_intersect(a, b, c, d):
                return True
    return False


def polylines_intersect(a_poly, b_poly):
    for a, b in zip(a_poly, a_poly[1:]):
        for c, d in zip(b_poly, b_poly[1:]):
            if segments_intersect(a, b, c, d):
                return True
    return False


def point_segment_distance(p, a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    denom = dx * dx + dy * dy
    if denom == 0:
        return distance(p, a)
    t = max(0.0, min(1.0, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / denom))
    return distance(p, [a[0] + t * dx, a[1] + t * dy])
