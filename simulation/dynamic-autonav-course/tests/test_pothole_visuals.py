import pathlib
import subprocess
import sys

import yaml

ROOT = pathlib.Path(__file__).resolve().parents[1]


def generate(seed=42):
    subprocess.run(
        [
            sys.executable,
            "scripts/generate_course.py",
            "--seed",
            str(seed),
            "--scenario",
            "normal",
            "--template",
            "oval_with_chicane",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return yaml.safe_load((ROOT / f"generated/generated_course_{seed}.yaml").read_text())


def test_generated_potholes_are_white_in_metadata():
    data = generate(42)
    potholes = [obj for obj in data["objects"] if obj["type"] == "pothole"]

    assert potholes
    assert {obj["color"] for obj in potholes} == {"white"}


def test_pothole_disc_model_material_is_white():
    sdf = (ROOT / "models/pothole_disc/model.sdf").read_text()

    assert "<ambient>1 1 1 1</ambient>" in sdf
    assert "<diffuse>1 1 1 1</diffuse>" in sdf
    assert "0.02 0.02 0.02 1" not in sdf


def test_generated_world_embeds_white_pothole_visuals():
    data = generate(42)
    sdf = (ROOT / "generated/generated_world_42.sdf").read_text()
    pothole_names = [obj["name"] for obj in data["objects"] if obj["type"] == "pothole"]

    assert pothole_names
    for name in pothole_names:
        start = sdf.index(f'<model name="{name}">')
        end = sdf.index("</model>", start)
        block = sdf[start:end]
        assert "<ambient>1 1 1 1</ambient>" in block
        assert "<diffuse>1 1 1 1</diffuse>" in block
        assert "0.01 0.01 0.01 1" not in block
        assert "0.02 0.02 0.02 1" not in block
