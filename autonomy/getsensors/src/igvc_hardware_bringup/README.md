# IGVC hardware bringup

This package contains launch files, configuration, udev templates, and documentation for the connected IGVC robot peripherals.

## Build

```bash
cd /media/igvc/OS/GETSENSORS
source /opt/ros/humble/setup.bash
colcon build --symlink-install
source install/setup.bash
```

## Current detected hardware

See `docs/hardware_inventory.md` for the current USB inventory and unresolved serial-device mapping.

## Launch examples

```bash
ros2 launch igvc_hardware_bringup realsense.launch.py
ros2 launch igvc_hardware_bringup oakd.launch.py
ros2 launch igvc_hardware_bringup oakd_rgb_only.launch.py
ros2 launch igvc_hardware_bringup rplidar.launch.py
ros2 launch igvc_hardware_bringup rplidar_rviz.launch.py
PYTHONNOUSERSITE=1 ros2 launch igvc_hardware_bringup gps.launch.py
ros2 launch igvc_hardware_bringup serial_watchdog.launch.py
ros2 launch igvc_estop_current estop_current.launch.py
```

Install/apply the udev rules before using stable serial names:

```bash
sudo cp src/igvc_hardware_bringup/udev/99-igvc-robot.rules /etc/udev/rules.d/
sudo udevadm control --reload-rules
sudo udevadm trigger
```

Current live mappings observed on 2026-05-27:

- `/dev/igvc_estop` -> ESP32 e-stop/current board, CP2102N serial `ee1d877cc382ee11901a429ec33d7414`, 115200 baud.
- `/dev/igvc_rplidar` -> RPLIDAR A-series adapter, CP2102 serial `0001`, 115200 baud.
- `/dev/igvc_gps` -> candidate Emlid Reach RS+ Prolific adapter, serial `AVCFz114J20`; access is currently blocked until the `igvc` login session has dialout permission or udev mode is applied.

The ROS Humble `nmea_navsat_driver` import can fail if the user-site NumPy shadows Ubuntu's ROS-compatible NumPy. Launch GPS with `PYTHONNOUSERSITE=1` until the user-site NumPy conflict is removed.

The OAK-D is currently enumerating as USB HIGH (USB2). Full RGBD launch still hits DepthAI `X_LINK_ERROR`; use `oakd_rgb_only.launch.py` for reliable RGB publishing until the camera is moved to USB SUPER/USB3 or the full RGBD bandwidth problem is fixed.

## Validation

Use `docs/verification_log.md` to record every hardware verification run.
