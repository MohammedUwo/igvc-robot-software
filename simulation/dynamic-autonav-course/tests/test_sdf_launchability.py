import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]


def test_generated_sdf_loads_with_ign_gazebo_server_iterations():
    subprocess.run(
        [sys.executable, "scripts/generate_course.py", "--seed", "42", "--scenario", "normal"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    result = subprocess.run(
        ["ign", "gazebo", "-r", "-s", "--iterations", "1", "generated/generated_world_42.sdf"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=30,
    )
    output = result.stdout + result.stderr
    assert "Error reading element" not in output
    assert "Unable to read file" not in output
    assert result.returncode == 0
