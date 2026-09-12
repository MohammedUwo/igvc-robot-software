#!/usr/bin/env python3
"""Generate an IGVC random course and spawn the diff_drive_robot into it.

This launch intentionally only solves world + robot spawning. Controller, lidar,
EKF, and autonomy errors are debugged after the robot is automatically present in
Gazebo.
"""
import math
import os
import random
import shutil
import subprocess
import sys
from pathlib import Path

import yaml
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess, OpaqueFunction, SetEnvironmentVariable, TimerAction
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.actions import IncludeLaunchDescription


def _package_root():
    """Return mutable igvc_sim source/workspace root when launched installed."""
    here = Path(__file__).resolve()
    candidates = [here.parents[1], Path.cwd()]
    candidates.extend(here.parents)
    for root in candidates:
        if (root / "scripts" / "generate_course.py").exists() and (root / "config" / "tile_library.yaml").exists():
            return root
    return here.parents[1]


def _as_bool(value):
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def _first_segment_yaw(course):
    centerline = course.get("lane_boundaries", {}).get("centerline_path_reference", [])
    if len(centerline) < 2:
        return 0.0
    x0, y0 = centerline[0]
    # Skip duplicate or extremely close points.
    for x1, y1 in centerline[1:]:
        dx = float(x1) - float(x0)
        dy = float(y1) - float(y0)
        if math.hypot(dx, dy) > 1e-4:
            return math.atan2(dy, dx)
    return 0.0


def _spawn_pose_from_metadata(meta_path, spawn_z):
    metadata = yaml.safe_load(Path(meta_path).read_text(encoding="utf-8"))
    explicit = metadata.get("robot_spawn", {})
    if explicit:
        return {
            "x": float(explicit.get("x_m", explicit.get("x", 0.0))),
            "y": float(explicit.get("y_m", explicit.get("y", 0.0))),
            "z": float(explicit.get("z_m", explicit.get("z", spawn_z))),
            "yaw": float(explicit.get("yaw_rad", explicit.get("yaw", 0.0))),
        }

    course = metadata.get("course", {})
    start = course.get("start_finish", {})
    return {
        "x": float(start.get("x_m", start.get("x_ft", 0.0) / 3.28084)),
        "y": float(start.get("y_m", start.get("y_ft", 0.0) / 3.28084)),
        "z": float(spawn_z),
        "yaw": _first_segment_yaw(course),
    }


def generate_world_and_spawn_robot(context, *args, **kwargs):
    root = _package_root()
    seed_arg = LaunchConfiguration("seed").perform(context)
    scenario = LaunchConfiguration("scenario").perform(context)
    template = LaunchConfiguration("template").perform(context)
    spawn_z = float(LaunchConfiguration("spawn_z").perform(context))
    rviz = LaunchConfiguration("rviz").perform(context)
    start_autonomy = _as_bool(LaunchConfiguration("autonomy").perform(context))

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
    meta = root / "generated" / f"generated_course_{seed}.yaml"
    spawn = _spawn_pose_from_metadata(meta, spawn_z)

    print(f"Generated world path: {world}")
    print(f"Generated metadata path: {meta}")
    print(
        "Robot spawn pose from generated metadata: "
        f"x={spawn['x']:.3f}, y={spawn['y']:.3f}, z={spawn['z']:.3f}, yaw={spawn['yaw']:.6f}"
    )

    diff_drive_share = Path(get_package_share_directory("diff_drive_robot"))
    # Use processed URDF because robot.urdf contains xacro includes and this
    # package's rsp.launch.py cats the file rather than running xacro.
    urdf = diff_drive_share / "urdf" / "robot_processed.urdf"
    bridge_params = diff_drive_share / "config" / "gz_bridge.yaml"
    rviz_config = diff_drive_share / "rviz" / "bot.rviz"
    simulator = ["ign", "gazebo"] if shutil.which("ign") else ["gz", "sim"]

    robot_state_publisher = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(str(diff_drive_share / "launch" / "rsp.launch.py")),
        launch_arguments={"use_sim_time": "true", "urdf": str(urdf)}.items(),
    )
    spawn_robot = Node(
        package="ros_gz_sim",
        executable="create",
        arguments=[
            "-topic", "robot_description",
            "-name", "diff_bot",
            "-x", f"{spawn['x']:.3f}",
            "-y", f"{spawn['y']:.3f}",
            "-z", f"{spawn['z']:.3f}",
            "-Y", f"{spawn['yaw']:.6f}",
        ],
        output="screen",
    )
    bridge = Node(
        package="ros_gz_bridge",
        executable="parameter_bridge",
        arguments=["--ros-args", "-p", f"config_file:={bridge_params}"],
        parameters=[{"use_sim_time": True}],
        output="screen",
    )
    joint_state_broadcaster = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["joint_state_broadcaster"],
        output="screen",
    )
    diff_drive_controller = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["diff_drive_controller"],
        output="screen",
    )

    actions = [
        SetEnvironmentVariable("GZ_SIM_RESOURCE_PATH", str(root / "models") + os.pathsep + os.environ.get("GZ_SIM_RESOURCE_PATH", "")),
        SetEnvironmentVariable("IGN_GAZEBO_RESOURCE_PATH", str(root / "models") + os.pathsep + os.environ.get("IGN_GAZEBO_RESOURCE_PATH", "")),
        ExecuteProcess(cmd=simulator + [str(world)], output="screen"),
        robot_state_publisher,
        bridge,
        # Give robot_state_publisher time to create its parameter service before
        # gz_ros2_control asks for robot_description during robot insertion.
        TimerAction(period=3.0, actions=[spawn_robot]),
        # Start controller spawners only after the model/control plugin has had
        # time to initialize /controller_manager. This keeps the launch focused
        # on base motion before autonomy/lidar/EKF debugging.
        TimerAction(period=8.0, actions=[joint_state_broadcaster]),
        TimerAction(period=10.0, actions=[diff_drive_controller]),
    ]

    if _as_bool(rviz):
        actions.append(
            Node(
                package="rviz2",
                executable="rviz2",
                name="rviz_full",
                arguments=["-d", str(rviz_config)],
                parameters=[{"use_sim_time": True}],
                output="screen",
            )
        )

    if start_autonomy:
        actions.append(
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(str(diff_drive_share / "launch" / "autonomous_drive.launch.py")),
                launch_arguments={"rviz": "False"}.items(),
            )
        )

    return actions


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument("seed", default_value="", description="Course seed; omit for random seed"),
        DeclareLaunchArgument("scenario", default_value="normal", description="Scenario from config/scenarios.yaml"),
        DeclareLaunchArgument("template", default_value="oval_with_chicane", description="Course template from config/course_templates.yaml"),
        DeclareLaunchArgument("spawn_z", default_value="0.12", description="Robot spawn height in meters"),
        DeclareLaunchArgument("rviz", default_value="False", description="Open RViz after spawning robot"),
        DeclareLaunchArgument("autonomy", default_value="False", description="Also start diff_drive_robot autonomy stack after spawning robot"),
        OpaqueFunction(function=generate_world_and_spawn_robot),
    ])
