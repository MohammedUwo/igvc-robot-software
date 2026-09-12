import pathlib
import re
import subprocess
import sys

import yaml

ROOT = pathlib.Path(__file__).resolve().parents[1]


def generate(seed=42, scenario="normal"):
    subprocess.run(
        [sys.executable, "scripts/generate_course.py", "--seed", str(seed), "--scenario", scenario],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return yaml.safe_load((ROOT / "generated" / f"generated_course_{seed}.yaml").read_text())


def test_course_metadata_describes_required_route_sequence_and_dimensions():
    data = generate(42)
    course = data["course"]
    assert course["units"] == "feet"
    assert course["area"] == {"width_ft": 120, "depth_ft": 100}
    assert 10 <= course["track_width_ft"] <= 20
    assert course["turn_radius_ft"] >= 5
    assert course["generation_mode"] == "grid_tiles"
    assert "s_chicane_left_right" in course["route_sequence"]
    assert "no_lane_zone" in course["route_sequence"]
    assert course["tile_route"][0]["tile"] == "straight"
    assert course["start_finish"]["same_line"] is True


def test_generated_sdf_has_large_asphalt_platform_and_grounded_lane_markings():
    generate(42)
    sdf = (ROOT / "generated" / "generated_world_42.sdf").read_text()
    assert "<size>140 120</size>" in sdf
    lane_poses = re.findall(r'<visual name="visual_[^"]+"><pose>[^<]+ ([0-9.]+) 0 0 [^<]+</pose>', sdf)
    assert lane_poses
    assert all(float(z) <= 0.03 for z in lane_poses)


def test_lanes_include_curves_chicane_no_mans_land_gap_and_return_to_start():
    data = generate(42)
    sdf = (ROOT / "generated" / "generated_world_42.sdf").read_text()
    for name in ["straight", "s_chicane_left_right", "no_lane_zone", "ramp_straight"]:
        assert name in data["course"]["route_sequence"]
    assert "lane_solid_" in sdf
    assert "lane_no_mans_land_gap" in sdf
    assert "lane_texture_plane" not in sdf
    assert data["course"]["start_finish"]["x_ft"] == data["course"]["finish"]["x_ft"]
    assert data["course"]["start_finish"]["y_ft"] == data["course"]["finish"]["y_ft"]


def test_ramp_is_visible_and_has_ramp_geometry_not_flat_box():
    data = generate(42)
    sdf = (ROOT / "generated" / "generated_world_42.sdf").read_text()
    assert data["ramp"]["pose"]["z"] == 0.0
    assert "ramp_tile_feature_" in sdf
    assert "<mesh><uri>model://ramp</uri></mesh>" in sdf or "ramp_wedge" in sdf
    assert "<box><size>2.0 1.0 0.3</size></box>" not in sdf


def test_sky_changes_between_lighting_modes():
    generate(42, "normal")
    normal_sdf = (ROOT / "generated" / "generated_world_42.sdf").read_text()
    generate(142, "bad_lighting")
    bad_sdf = (ROOT / "generated" / "generated_world_142.sdf").read_text()
    normal_sky = re.search(r'<sky>.*?</sky>', normal_sdf, re.S).group(0)
    bad_sky = re.search(r'<sky>.*?</sky>', bad_sdf, re.S).group(0)
    assert normal_sky != bad_sky
