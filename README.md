# Robot Software — Rutgers IGVC 2026–2027

Autonomy stack, hardware configuration, and system reference for the IGVC robot.

Most of this was **recovered from the competition NUC (`igvc-NUC12DCMi9`) before it was wiped.**
The autonomy package below had never been committed to any repository — it existed only as an
uncommitted working tree on that one machine. Treat this repo as the authoritative copy.

---

## Layout

| Path | What it is |
|---|---|
| `autonomy/diff_drive_robot/` | The ROS 2 autonomy package — nodes, launch files, configs, URDF, Gazebo worlds |
| `docs/ros_knowledge.md` | Long-form internal writeup of how the stack works, written by a previous member. Start here. |
| `system/udev/` | udev rules that give the robot's hardware stable device names. Copy to `/etc/udev/rules.d/` on any new install. |
| `system/manifest/` | NUC hardware and package inventory — partition table, fstab, installed packages, `lspci`/`lsusb`/`dmidecode` |
| `legacy/pathfinder-led/` | Safety-light control from the 2021–22 robot (ROS 1 + Arduino). Reference for the IGVC safety-light requirement. |

## The autonomy package

`autonomy/diff_drive_robot` is an `ament_python` ROS 2 package (Humble). ~2,300 lines.

**Nodes** (`diff_drive_robot/`):

| Node | Role |
|---|---|
| `behavior_node.py` | Command arbitration. Priority: critical lidar → camera obstacle → waypoint → map → line following. Publishes `/cmd_vel`. |
| `detect_line.py` | OpenCV white-line detection → `/line_cmd_vel` |
| `rplidar_driver.py` | RPLIDAR A1 driver → `/scan` |
| `odrive.py` | Twist → ODrive velocity commands, with a 0.5 s command watchdog |
| `emlid_gps.py` | Emlid Reach NMEA over TCP → `/fix`, `/emlid/pose` |
| `waypoint_driver.py` | Drives waypoints from `config/waypoints.yaml` using `/odometry/filtered` |
| `path_trail.py` | Path + marker visualisation |
| `process_image.py` | OpenCV helpers for line detection |

**Build and run:**

```bash
cd <workspace>
colcon build --symlink-install --packages-select diff_drive_robot
source install/setup.bash

ros2 launch diff_drive_robot robot.launch.py            # full Gazebo simulation
ros2 launch diff_drive_robot autonomous_drive.launch.py # autonomy only (real hardware)
```

## Known issues — read before running on hardware

1. **`odrive.py` still carries simulation geometry.** `wheel_radius = 0.05` (5 cm) and
   `wheel_base = 0.3` (30 cm) are the tutorial defaults, not this robot. Every velocity command
   is scaled wrong until these are measured and set.
2. **`vel_limit` disagrees with the saved ODrive config** — 30 in `odrive.py`, 50.0 in the board
   config. IGVC requires the 5 mph cap to be *hardware*-governed, so this needs to be one number,
   set deliberately.
3. **The saved TF dump reads `"No tf data received"`.** Nav2, SLAM Toolbox, and the EKF are all
   inert without a transform tree. Fixing the URDF frames is a prerequisite for everything.
4. `package.xml` metadata is still the upstream author's; `setup.py` disagrees with it.
5. `robot.launch.py` includes `autonomous_drive.launch.py`, which starts RViz again — launching
   the full sim opens duplicate RViz windows.
6. `avoid_obstacle.py` is effectively unused.

## Hardware

| Part | Notes |
|---|---|
| Intel NUC12DCMi9 | 64 GB DDR4, RTX 3060 12 GB, Ubuntu 22.04.5, ROS 2 Humble |
| RPLIDAR A1 | 0.15–12 m. `rplidar.rules` binds it to `/dev/rplidar` |
| Luxonis OAK-D | DepthAI; `80-movidius.rules` |
| Intel RealSense | librealsense2 + `realsense2_camera` |
| Emlid Reach RS+ | NMEA over TCP, default `192.168.1.100:2101` |
| ODrive v3.x | Two axes, 4096 cpr encoders, 3 pole pairs |
| Battery | 24 V 50 Ah |

## IGVC 2026 requirements this code has to satisfy

- Course is **asphalt**, with ramps up to **15% grade**
- Vehicle 3–7 ft long, 2–4 ft wide, ≤6 ft tall
- **1 mph minimum** average, **5 mph maximum, hardware-governed**
- Must carry a 20 lb payload (~16″×8″×8″)
- Mechanical E-stop: red, ≥1 in, **center rear, 2–4 ft above ground**, hardware only
- Wireless E-stop: **≥100 ft**, hardware only, not software-controlled
- Safety light: **solid** when powered, **flashing** in autonomous

Full rules: <http://www.igvc.org/2026rules.pdf>

## Upstream

`autonomy/diff_drive_robot` began as a clone of
[adoodevv/diff_drive_robot](https://github.com/adoodevv/diff_drive_robot), a Gazebo
differential-drive tutorial package. Everything in `diff_drive_robot/` (the nodes), plus
`autonomous_drive.launch.py` and most of `config/`, is Rutgers work layered on top and was
never committed upstream or anywhere else.

## Housekeeping

Nothing secret belongs in this repo — no passwords, tokens, API keys, or OAuth secrets.
Shell history and SSH keys from the NUC were deliberately excluded from this recovery.
