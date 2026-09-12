# GETSENSORS IGVC Hardware Bringup

This workspace contains ROS 2 Humble packages for IGVC hardware bringup and sensor/peripheral verification.

## Packages

- `igvc_hardware_bringup`
  - Launch/config for RPLIDAR, GPS, RealSense, OAK-D, serial watchdogs, and serial permission diagnostics.
- `igvc_estop_current`
  - ESP32 e-stop/current serial parser and ROS publishers.
- `igvc_odrive_interface`
  - Safe observe-first ODrive ROS interface with diagnostics and command gating.

## Current verified devices

- ESP32 e-stop/current board: `/dev/ttyUSB0`, 115200 baud, publishes power/current/safety topics.
- RPLIDAR: `/dev/ttyUSB1`, publishes `/scan` at about 6.6 Hz.
- ODrive V3.6: native USB serial `315B32623431`, firmware `0.5.6`, configured for two Nanotec `DB59L024035R-B` BLDC motors (axis0/M0 and axis1/M1) using source-backed motor limits; publishes `/odrive/vbus_voltage` and `/joint_states` at about 10 Hz in observe-only mode.
- RealSense D435: online with serial `939622074571`, but currently reports USB 2.1 reduced-performance mode.

## Current blockers

- OAK-D is not currently enumerating after being moved to direct USB3. Linux/DepthAI discovery reports no OAK-D device.
- GPS candidate `/dev/ttyACM0` is visible but not accessible from the current session because it is `0660 root:dialout` and the current user session lacks `dialout`.

See latest detailed evidence in:

- `logs/peripheral_bringup_2026-05-27/README.md`
- `docs/hardware_inventory.md`
- `docs/peripheral_sources.md`
- `docs/verification_log.md`

## Build

```bash
source /opt/ros/humble/setup.bash
colcon build --symlink-install
source install/setup.bash
```

## Tests

```bash
source /opt/ros/humble/setup.bash
source install/setup.bash
PYTHONPATH=src/igvc_estop_current:src/igvc_odrive_interface:src/igvc_hardware_bringup \
  python3 -m pytest src/igvc_estop_current/test src/igvc_odrive_interface/test src/igvc_hardware_bringup/test
```

## Common launches

RPLIDAR:

```bash
ros2 launch igvc_hardware_bringup rplidar.launch.py
ros2 topic hz /scan
```

ESP32 e-stop/current:

```bash
ros2 launch igvc_estop_current estop_current.launch.py
ros2 topic echo --once /power/odrive/current
ros2 topic echo --once /safety/estop
```

ODrive observe-only telemetry:

```bash
ros2 launch igvc_odrive_interface odrive.launch.py
ros2 topic hz /odrive/vbus_voltage
ros2 topic echo --once /diagnostics
```

ODrive DB59 motor configuration (writes both axis0/M0 and axis1/M1, then saves/reboots the ODrive):

```bash
python3 src/igvc_odrive_interface/scripts/configure_db59_odrive.py --serial 315B32623431
```

Source-backed values used for Nanotec `DB59L024035R-B`: 6 poles / 3 pole pairs, 24 V, rated current 9.4 A, peak current 28 A, rated torque 0.47 Nm, peak torque 1.41 Nm, torque constant 0.05 Nm/A, line-line resistance 0.22 ohm, line-line inductance 0.29 mH, rated speed 3500 rpm (58.3 turn/s). The script idles both axes and disables startup calibration/closed-loop so motion remains explicit.

RealSense:

```bash
ros2 launch igvc_hardware_bringup realsense.launch.py
```

GPS, after permissions are fixed:

```bash
ros2 launch igvc_hardware_bringup gps.launch.py
ros2 topic echo --once /gps/fix
```

OAK-D, after it enumerates in `lsusb`/DepthAI:

```bash
python3 -c "import depthai as dai; print(dai.Device.getAllAvailableDevices())"
ros2 launch igvc_hardware_bringup oakd.launch.py
```

## Permission/udev fix

The current session cannot open `/dev/ttyACM0` or `/dev/ttyACM1` because those devices are owned by `root:dialout` with mode `0660`.

Preferred durable fix:

```bash
sudo usermod -aG dialout igvc
# log out completely and start a fresh login/session
```

Or apply workspace udev rules:

```bash
sudo cp src/igvc_hardware_bringup/udev/99-igvc-robot.rules /etc/udev/rules.d/99-igvc-robot.rules
sudo udevadm control --reload-rules
sudo udevadm trigger
# unplug/replug affected USB serial devices if needed
```

Verify permissions:

```bash
stat -c '%A %U %G %n' /dev/ttyUSB0 /dev/ttyUSB1 /dev/ttyACM0 /dev/ttyACM1
ros2 launch igvc_hardware_bringup serial_permissions.launch.py
```

## Safety notes

- ODrive commands are disabled by default (`command_enabled: false`).
- ODrive command path also requires non-stale `/safety/estop` state and no active e-stop.
- No motion commands were used during the current bringup.
- The ESP32 e-stop is known to shut off the powered USB hub; hub-connected device disconnect/reconnect behavior still needs a controlled physical test.
