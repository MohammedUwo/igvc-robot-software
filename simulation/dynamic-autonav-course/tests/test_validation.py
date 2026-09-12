import pathlib
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


def validate(seed=42):
    return subprocess.run(
        [sys.executable, "scripts/validate_course.py", f"generated/generated_course_{seed}.yaml"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )


def test_validate_course_reports_pass_for_generated_course():
    generate(42)
    result = validate(42)
    assert "Validation report for seed 42" in result.stdout
    assert "[PASS] Config loaded" in result.stdout
    assert "[PASS] Object spacing" in result.stdout
    assert "[PASS] Ramp approach/exit" in result.stdout
    assert "Validation: PASS" in result.stdout


def test_generated_objects_have_valid_regions_and_clear_start_finish():
    generate(42)
    data = yaml.safe_load((ROOT / "generated" / "generated_course_42.yaml").read_text())
    assert data["validation"]["forbidden_zone_check"] == "passed"
    assert data["validation"]["blocked_path_check"] == "passed"
    assert all(obj["region"] in {"lane_course", "no_mans_land"} for obj in data["objects"])


def test_generated_world_contains_all_models_and_lighting():
    generate(42)
    sdf = (ROOT / "generated" / "generated_world_42.sdf").read_text()
    assert "<world name=\"igvc_dynamic_autonav_42\">" in sdf
    assert "model://barrel" in sdf
    assert "model://drum" in sdf
    assert "model://pothole_disc" in sdf
    assert "model://ramp" in sdf
    assert "<light type=\"directional\" name=\"sun\">" in sdf
