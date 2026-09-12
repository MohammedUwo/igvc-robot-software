# Rutgers IGVC — robot archive

Everything the team has, in one place, as of September 2026: the software pulled off the
competition NUC, the PCB exports, the lab photos, and the notes.

The NUC (`igvc-NUC12DCMi9`) has **not** been wiped yet — a rebuild is planned but hasn't happened.
This archive exists so that when it does, nothing is lost.

This is a save, not a live project. Work on the robot happens elsewhere — this is what exists
today so none of it gets lost again.

## What's in here

| Folder | Size | Contents |
|---|---:|---|
| `autonomy/` | 45 files | The ROS 2 package the robot runs — `diff_drive_robot`, ~2,300 lines: lane detection, lidar driver, obstacle avoidance, GPS waypoints, ODrive motor control, plus URDF and Gazebo worlds |
| `hardware/schematics/` | 18 projects | Every EasyEDA board the team has designed — schematics as SVG, layouts as fab PDFs. E-stop RX/TX, LED controller, power distribution, IMU handler, and the rest |
| `photos/` | 156 photos | The robot (108) and the lab stock (48), September 2026 |
| `docs/` | 4 files | The build plan, a long writeup of how the autonomy works, the lab inventory, and an index of the NUC backup |
| `system/` | 22 files | What the NUC was: partition table, package lists, hardware inventory, and the 5 udev rules that give the sensors stable device names |
| `legacy/` | 2 files | Safety-light code from the 2021–22 robot. Still the best reference we have for that. |

Start with [`docs/qualification-plan.md`](docs/qualification-plan.md) if you want to know what
needs doing, or [`docs/lab-inventory.md`](docs/lab-inventory.md) if you're new and looking for a
part.

## Why this repo exists

`autonomy/diff_drive_robot` had never been committed anywhere. It lives as an uncommitted working
tree on one machine — `igvc-NUC12DCMi9` — which is due to be rebuilt. A reinstall would erase it
permanently. Until that machine is wiped there are two copies; after, this is the only one.

The rest was gathered at the same time because it was scattered across that NUC, a Drive folder,
and a Desktop directory, and nobody could have found it in six months.

## Before running the autonomy on hardware

Three things are known-wrong and will bite:

1. **`odrive.py` has simulation geometry** — `wheel_radius = 0.05`, `wheel_base = 0.3` are
   tutorial defaults, not this robot. Every velocity command is scaled wrong until they're measured.
2. **`vel_limit` disagrees with itself** — 30 in the code, 50 in the saved ODrive config. IGVC
   wants the speed cap governed in hardware, so pick one number deliberately.
3. **The saved TF dump reads `"No tf data received"`** — the EKF, SLAM and Nav2 are all inert
   without a transform tree.

Smaller stuff: `package.xml` still has the upstream author's metadata, `robot.launch.py` opens
duplicate RViz windows, and `avoid_obstacle.py` is unused.

Build it the normal way:

```bash
colcon build --symlink-install --packages-select diff_drive_robot
source install/setup.bash
ros2 launch diff_drive_robot robot.launch.py            # Gazebo sim
ros2 launch diff_drive_robot autonomous_drive.launch.py # real hardware
```

The package started as a clone of
[adoodevv/diff_drive_robot](https://github.com/adoodevv/diff_drive_robot), a Gazebo tutorial.
Everything in `diff_drive_robot/`, plus `autonomous_drive.launch.py` and most of `config/`, is
Rutgers work on top of it.

## The robot

| Part | Notes |
|---|---|
| Intel NUC12DCMi9 | 64 GB RAM, RTX 3060, Ubuntu 22.04, ROS 2 Humble |
| RPLIDAR A1 | 0.15–12 m, shows up as `/dev/rplidar` |
| Luxonis OAK-D | DepthAI |
| Intel RealSense | librealsense2 |
| Emlid Reach RS+ | NMEA over TCP, `192.168.1.100:2101` |
| ODrive v3.x | Two axes, 4096 cpr, 3 pole pairs |
| Battery | 24 V 50 Ah |

## What's not here

| Where | What |
|---|---|
| Google Drive, `nuc-backup/tar/` | Full NUC disk images — 162 archives, 102 GiB. See [`docs/nuc-backup-index.md`](docs/nuc-backup-index.md). |
| Google Drive, `Igvc Robot` | Full-resolution photos. The copies here are downscaled to 1280 px. |
| [ozatyx/rutgers_igvc_electrical](https://github.com/ozatyx/rutgers_igvc_electrical) | Firmware for the boards in `hardware/` — E-stop RX/TX, manual control, ODrive config |
| [Rutgers-IGVC-2026-2027/Old-Robot-](https://github.com/Rutgers-IGVC-2026-2027/Old-Robot-) | Team-org copy of the software half of this |

## No secrets in here

No passwords, tokens, or keys. The NUC's shell history and SSH keys were left out on purpose —
the history had a live Cloudflare tunnel token and a plaintext password in it. Those two archives
are still in the Drive backup; treat them as secret-bearing.
