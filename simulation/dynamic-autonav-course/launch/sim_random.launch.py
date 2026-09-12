#!/usr/bin/env python3
import os
import random
import shutil
import subprocess
import sys
from pathlib import Path

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess, OpaqueFunction, SetEnvironmentVariable
from launch.substitutions import LaunchConfiguration


def _package_root():
    """Return the source/workspace root when launched from an installed package.

    With --symlink-install the launch file may live under install/igvc_sim/share/igvc_sim,
    while the mutable generator/config/generated folders live in the source workspace.
    Prefer a parent that contains scripts/generate_course.py and config/tile_library.yaml.
    """
    here = Path(__file__).resolve()
    candidates = [here.parents[1], Path.cwd()]
    candidates.extend(here.parents)
    for root in candidates:
        if (root / "scripts" / "generate_course.py").exists() and (root / "config" / "tile_library.yaml").exists():
            return root
    return here.parents[1]


def generate_and_launch(context, *args, **kwargs):
    root = _package_root()
    seed_arg = LaunchConfiguration("seed").perform(context)
    scenario = LaunchConfiguration("scenario").perform(context)
    template = LaunchConfiguration("template").perform(context)
    seed = int(seed_arg) if seed_arg else random.SystemRandom().randint(1, 999999999)
    script = root / "scripts" / "generate_course.py"
    cmd = [sys.executable, str(script), "--seed", str(seed), "--scenario", scenario, "--template", template]
    print(f"Package/source root: {root}")
    print(f"Generated course seed: {seed}")
    print(f"Scenario: {scenario}")
    print(f"Template: {template}")
    result = subprocess.run(cmd, cwd=root, text=True, capture_output=True)
    print(result.stdout, end="")
    if result.returncode != 0:
        print(result.stderr, end="")
        raise RuntimeError(f"course generation failed for seed {seed}")
    world = root / "generated" / f"generated_world_{seed}.sdf"
    print(f"Generated world path: {world}")
    simulator = ["ign", "gazebo"] if shutil.which("ign") else ["gz", "sim"]
    return [
        SetEnvironmentVariable("GZ_SIM_RESOURCE_PATH", str(root / "models") + os.pathsep + os.environ.get("GZ_SIM_RESOURCE_PATH", "")),
        SetEnvironmentVariable("IGN_GAZEBO_RESOURCE_PATH", str(root / "models") + os.pathsep + os.environ.get("IGN_GAZEBO_RESOURCE_PATH", "")),
        ExecuteProcess(cmd=simulator + [str(world)], output="screen"),
    ]


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument("seed", default_value="", description="Course seed; omit for random seed"),
        DeclareLaunchArgument("scenario", default_value="normal", description="Scenario from config/scenarios.yaml"),
        DeclareLaunchArgument("template", default_value="oval_with_chicane", description="Course template from config/course_templates.yaml"),
        OpaqueFunction(function=generate_and_launch),
    ])
