# IGVC hardware inventory

Generated from the connected machine during ROS 2 hardware bringup.

## Host / ROS

- Host OS: Ubuntu 22.04.5 LTS (jammy)
- Active ROS distro: Humble (`/opt/ros/humble`)
- Workspace: `/media/igvc/OS/GETSENSORS`

## Safety-critical USB power topology

- User-provided hardware fact: triggering the ESP32 e-stop shuts off the powered USB hub.
- All peripherals connected to that powered USB hub will disconnect when e-stop is triggered.
- ROS bringup must treat simultaneous disappearance of hub-attached devices as an expected e-stop/power-loss condition, not just independent device failures.
- Nodes for hub-powered peripherals should reconnect cleanly after e-stop reset and USB power restoration.
- ODrive/motion command handling must fail safe if `/safety/estop` becomes active, stale, or if USB peripherals disappear.

## Detected USB devices

| Peripheral | Detected identity | Current Linux path / ID | Notes |
| --- | --- | --- | --- |
| Intel RealSense D435 | `Intel RealSense D435`, serial `939622074571`, firmware `5.17.0.10` | USB ID `8086:0b07`; video nodes `/dev/video0`..`/dev/video5` | Use `realsense2_camera`; select by serial `939622074571`. If connected through the powered hub, it will disconnect during ESP32 e-stop. |
| OAK-D original model | Previously DepthAI MXID `1844301051345D0E00` | Not visible in latest `lsusb`; DepthAI Python discovery count `0` | User moved OAK-D to direct USB3, but it is currently not enumerating as USB device `03e7:2485`. Check cable/port/power and replug until `lsusb` shows it on a 5000M+ path. |
| Silicon Labs CP2102N serial device | `ID_SERIAL_SHORT=ee1d877cc382ee11901a429ec33d7414` | `/dev/ttyUSB0`, USB path `pci-0000:00:14.0-usb-0:5.1:1.0` | Positively identified as ESP32 current/e-stop board from 115200 baud firmware output. If the ESP32 remains upstream of hub power control, verify whether this serial link survives e-stop. |
| Slamtec RPLIDAR A-series | RPLIDAR S/N `EFFC9DF1C3E39AC4C3E698F91F2B340D`, firmware `1.24`, hardware rev `5` | CP2102 `ID_SERIAL_SHORT=0001`, currently `/dev/ttyUSB1`, target symlink `/dev/igvc_rplidar` | Positively identified by `rplidar_ros` active probe at 115200 baud. If hub-powered, it will disconnect during ESP32 e-stop. |
| Prolific USB serial controller | `ID_SERIAL_SHORT=AVCFz114J20` | `/dev/ttyACM0`, target symlink `/dev/igvc_gps`, USB path `pci-0000:00:14.0-usb-0:12:1.0` | Candidate Emlid Reach RS+ GPS serial adapter. Permission denied because current login session is not in `dialout` and device mode is `0660 root:dialout`; apply udev rule or start a new dialout-enabled session. If hub-powered, it will disconnect during ESP32 e-stop. |
| ODrive V3.6 | Serial `315B32623431`, firmware `0.5.6`, vbus about `23.97-24.00 V` | USB ID `1209:0d32`, `/dev/serial/by-id/usb-ODrive_Robotics_ODrive_3.6_CDC_Interface_315B32623431-if00 -> /dev/ttyACM1` | Discoverable by Python ODrive API only when serial is passed as uppercase hex string without `0x`. ROS telemetry works observe-only on axis1. CDC serial `/dev/ttyACM1` is permission denied until udev/dialout fix. |

## ROS driver availability observed

| Driver/package | Status |
| --- | --- |
| `realsense2_camera` | Installed under `/opt/ros/humble` |
| `depthai_ros_driver` | Installed under `/opt/ros/humble` |
| `depthai_ros_msgs` | Installed under `/opt/ros/humble` |
| OAK-D ROS RGB-only fallback | Previously `oakd_rgb_only.launch.py` published `/oak/rgb/image_raw` at about 7.5 Hz with OK diagnostics while connected at USB HIGH; after direct-USB3 move, OAK-D is not enumerating |
| `rplidar_ros` | Installed under `/opt/ros/humble`; active probe publishes `/scan` |
| `nmea_navsat_driver` | Installed under `/opt/ros/humble`; import requires `PYTHONNOUSERSITE=1` until user-site NumPy conflict is removed; serial access still blocked on `/dev/ttyACM0` |
| Python `odrive` | Installed: `0.6.10.post0`; ODrive serial `315B32623431` discovered |
| Python `serial` / `python3-serial` | PySerial installed in user site during bringup; apt package candidate exists: `python3-serial` |

## Stable-name target

Recommended udev symlinks once each serial device is positively mapped:

- `/dev/igvc_gps` -> candidate Prolific adapter `AVCFz114J20`
- `/dev/igvc_rplidar` -> CP2102 serial `0001`, RPLIDAR S/N `EFFC9DF1C3E39AC4C3E698F91F2B340D`
- `/dev/igvc_estop` -> CP2102N serial `ee1d877cc382ee11901a429ec33d7414`
- `/dev/igvc_odrive` -> ODrive CDC serial `315B32623431` once udev rules are applied; ODrive ROS node accesses native USB/Fibre by serial `315B32623431`.

## Open identification work

- The serial devices are visible, and ESP32/RPLIDAR mappings are confirmed. Current blockers:

- `/dev/ttyUSB0` is positively identified as the ESP32 current/e-stop board for current firmware output.
- `/dev/ttyACM0` returned permission denied during a raw read attempt.
- `/dev/ttyACM1` is ODrive CDC serial and also permission denied for raw serial, though native ODrive API access works.
- `/dev/ttyUSB1` is confirmed as RPLIDAR by active `rplidar_ros` probe.
- OAK-D is not currently visible after being moved to direct USB3.
- Need to verify which peripherals are physically downstream of the powered USB hub and which, if any, stay enumerated after ESP32 e-stop.

Next verification should check group permissions, install/apply udev rules, sample each remaining port at expected baud rates while each peripheral is powered, and explicitly test e-stop-triggered USB disconnect/reconnect behavior.
