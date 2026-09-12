# Autonomy

Two ROS 2 Humble workspaces, written by different people at different times. They do not talk to
each other yet, and joining them up is most of the remaining work.

## `getsensors/` — hardware bringup (May 2026)

The layer that talks to real devices. Three packages, with tests, and a written record of what was
actually verified on the robot:

| Package | Does |
|---|---|
| `igvc_hardware_bringup` | Launch + config for RPLIDAR, GPS, RealSense, OAK-D, plus a serial watchdog and permission diagnostics |
| `igvc_estop_current` | Parses the ESP32 e-stop/current board over serial, publishes safety and power topics |
| `igvc_odrive_interface` | ODrive interface, observe-first, with command gating and a safety timeout |

`docs/hardware_inventory.md` is the most accurate hardware record the team has — real serial
numbers, device paths, baud rates and firmware versions, taken off the running machine.

**Two facts from it worth knowing before touching anything:**

- **The e-stop cuts power to the USB hub.** Every peripheral on that hub disappears at once when
  the e-stop fires. Nodes must treat simultaneous device loss as an expected e-stop condition, not
  as separate failures, and must reconnect cleanly afterwards.
- **The motors are Nanotec `DB59L024035R-B` BLDC**, on ODrive V3.6 (serial `315B32623431`,
  firmware 0.5.6, ~24 V bus). `igvc_odrive_interface` ships with `command_enabled: false` — it only
  observes until someone deliberately turns that on.

Known blockers recorded at the time: the OAK-D stopped enumerating after being moved to direct
USB3, and GPS on `/dev/ttyACM0` is permission-denied pending the udev rules in
`igvc_hardware_bringup/udev/99-igvc-robot.rules`.

## `diff_drive_robot/` — the autonomy stack

Lane detection, gap-following, GPS waypoints and behaviour arbitration, plus a Gazebo simulation of
the whole robot. Written against simulation; the hardware constants in `odrive.py` are still the
tutorial defaults. See the root README for the known issues.

## How they relate

`getsensors` knows the real hardware and doesn't drive. `diff_drive_robot` knows how to drive and
has never seen the real hardware. The sensible path is to keep `getsensors` as the device layer and
point `diff_drive_robot`'s nodes at the topics it publishes, rather than keeping two ODrive
interfaces and two lidar drivers.
