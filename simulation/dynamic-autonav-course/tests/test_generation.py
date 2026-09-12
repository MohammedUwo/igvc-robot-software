import hashlib
import pathlib
import subprocess
import sys

import yaml

ROOT = pathlib.Path(__file__).resolve().parents[1]


def run_generator(seed=42, scenario="normal"):
    result = subprocess.run(
        [sys.executable, "scripts/generate_course.py", "--seed", str(seed), "--scenario", scenario],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    return result.stdout


def metadata(seed):
    path = ROOT / "generated" / f"generated_course_{seed}.yaml"
    assert path.exists()
    return yaml.safe_load(path.read_text())


def test_seed_42_generation_creates_expected_outputs_and_passes_validation():
    out = run_generator(42, "normal")
    assert "Generated course seed: 42" in out
    assert "Scenario: normal" in out
    assert "Validation: PASS" in out
    assert (ROOT / "generated" / "generated_world_42.sdf").exists()
    assert (ROOT / "generated" / "generated_course_42.yaml").exists()
    png = ROOT / "generated" / "generated_course_42.png"
    assert png.exists()
    assert png.stat().st_size > 10_000
    data = metadata(42)
    assert data["validation"]["passed"] is True
    assert data["ramp"]["approach_clearance_passed"] is True
    assert data["ramp"]["exit_clearance_passed"] is True


def test_same_seed_reproduces_identical_metadata():
    run_generator(42, "normal")
    first = (ROOT / "generated" / "generated_course_42.yaml").read_bytes()
    run_generator(42, "normal")
    second = (ROOT / "generated" / "generated_course_42.yaml").read_bytes()
    assert hashlib.sha256(first).hexdigest() == hashlib.sha256(second).hexdigest()


def test_different_seeds_create_different_layouts():
    run_generator(42, "normal")
    run_generator(43, "normal")
    a = metadata(42)
    b = metadata(43)
    assert a["objects"] != b["objects"] or a["ramp"] != b["ramp"] or a["lighting"] != b["lighting"]


def test_object_counts_within_scenario_ranges():
    run_generator(42, "normal")
    data = metadata(42)
    rules = yaml.safe_load((ROOT / "config" / "spawn_rules.yaml").read_text())
    counts = {"barrel": 0, "drum": 0, "pothole": 0}
    for obj in data["objects"]:
        counts[obj["type"]] += 1
    assert rules["barrels"]["count_range"][0] <= counts["barrel"] <= rules["barrels"]["count_range"][1]
    assert rules["drums"]["count_range"][0] <= counts["drum"] <= rules["drums"]["count_range"][1]
    assert rules["potholes"]["count_range"][0] <= counts["pothole"] <= rules["potholes"]["count_range"][1]


def test_batch_generation_10_worlds_passes():
    result = subprocess.run(
        [sys.executable, "scripts/batch_generate_test.py", "--scenario", "normal", "--count", "10"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    assert "10 valid worlds generated" in result.stdout
    assert "0 validation failures" in result.stdout
