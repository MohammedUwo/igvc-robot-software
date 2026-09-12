# Peripheral source-of-truth facts

Facts in this file must come from datasheets, vendor docs, observed tool output, or direct user-provided hardware facts. Do not treat assumptions as facts.

| Peripheral | Fact | Value used | Source | Evidence date | Used by |
| --- | --- | --- | --- | --- | --- |
| Host ROS | ROS distro | Humble | `env` and `/opt/ros/humble` observed on this host | 2026-05-27 | workspace build/launch |
| Powered USB hub / ESP32 e-stop | E-stop power behavior | Triggering the ESP32 e-stop shuts off the powered USB hub; all peripherals connected to that hub disconnect | Direct user-provided hardware fact in chat | 2026-05-27 | safety design, reconnect handling, verification plan |
| Intel RealSense D435 | Serial number | `939622074571` | `rs-enumerate-devices -s` | 2026-05-27 | `config/realsense.yaml` |
| Intel RealSense D435 | Firmware | `5.17.0.10` | `rs-enumerate-devices -s` | 2026-05-27 | diagnostics |
| OAK-D | MXID | `1844301051345D0E00` | DepthAI Python `Device.getAllAvailableDevices()` | 2026-05-27 | `config/oakd.yaml` |
| OAK-D | USB identity | `03e7:2485` Intel Movidius MyriadX | `lsusb` | 2026-05-27 | inventory |
| OAK-D after direct-USB3 move | Current enumeration | Not present in `lsusb`; DepthAI discovery count `0` | `lsusb`; Python `depthai.Device.getAllAvailableDevices()` | 2026-05-27 | OAK-D verification blocker |
| CP2102N serial device | Stable serial | `ee1d877cc382ee11901a429ec33d7414` | `udevadm info -q property -n /dev/ttyUSB0` | 2026-05-27 | udev candidate |
| RPLIDAR A-series | USB adapter stable serial | `0001` | `udevadm info -q property -n /dev/ttyUSB1` plus active `rplidar_ros` probe | 2026-05-27 | `/dev/igvc_rplidar`, `config/rplidar.yaml` |
| RPLIDAR A-series | RPLIDAR identity | S/N `EFFC9DF1C3E39AC4C3E698F91F2B340D`, firmware `1.24`, hardware rev `5`, health OK | `ros2 run rplidar_ros rplidar_node --ros-args -p serial_port:=/dev/ttyUSB1 -p serial_baudrate:=115200` output | 2026-05-27 | `config/rplidar.yaml`, verification |
| RPLIDAR A-series | Serial baud | `115200` | Successful `rplidar_ros` active probe on `/dev/ttyUSB1`; node reported scan mode Express | 2026-05-27 | `config/rplidar.yaml` |
| Prolific serial device | Stable serial | `AVCFz114J20` | `udevadm info -q property -n /dev/ttyACM0` | 2026-05-27 | udev candidate |
| Prolific serial device | Current access | `/dev/ttyACM0` exists as `0660 root:dialout`; current `igvc` session lacks `dialout`; raw serial and `nmea_navsat_driver` fail permission denied | `stat /dev/ttyACM0`; PySerial; `ros2 launch igvc_hardware_bringup gps.launch.py` | 2026-05-27 | GPS blocker |
| ODrive V3.6 | Native USB serial | `315B32623431` | Python ODrive API `find_any(serial_number='315B32623431')` | 2026-05-27 | `config/odrive.yaml`, udev rules |
| ODrive V3.6 | Firmware / bus | firmware `0.5.6`, vbus about `23.96-23.99 V` | Python ODrive API; ROS `/odrive/vbus_voltage` | 2026-05-27 | ODrive telemetry |
| ODrive V3.6 | ROS telemetry | `/odrive/vbus_voltage` and `/joint_states` at about `10.0 Hz`; diagnostics OK on `axis1`; commands disabled by e-stop-active safety gate | `ros2 launch igvc_odrive_interface odrive.launch.py`; `ros2 topic hz`; `ros2 topic echo` | 2026-05-27 | observe-only motor telemetry |
| ODrive V3.6 | Electrical limits | input range 12-24 V for 24 V variant / 12-56 V for 56 V variant; peak current per motor 120 A; continuous current cooling-dependent, 40 A per channel with heatsink in still air | ODrive docs v0.5.6 `specifications.html` / `_sources/specifications.rst.txt` | 2026-06-01 | DB59 ODrive config safety bounds |
| ODrive V3.6 firmware 0.5.6 | Motor setup semantics | two brushless motors supported; `pole_pairs` is motor magnet poles divided by two; `torque_constant` is Nm/A and docs say use 8.27/KV if KV is known; encoder CPR is 4x PPR; `save_configuration()` persists `.config` and reboots board | ODrive docs v0.5.6 `getting-started.html` / `_sources/getting-started.rst.txt` | 2026-06-01 | `scripts/configure_db59_odrive.py` |
| Nanotec DB59L024035R-B | Motor identity / electrical constants | BLDC motor, 6 poles, 24 VDC, no-load/rated/peak current `<0.8 / 9.4 / 28 A`, line-line resistance `0.22 ohm`, line-line inductance `0.29 mH`, rated/peak torque `0.47 / 1.41 Nm`, torque constant `0.05 Nm/A`, back-EMF constant `3.8 Vrms/krpm`, rated power `172 W`, no-load/rated speed `4500 / 3500 rpm` | Nanotec datasheet PDF `https://www.nanotec.com/fileadmin/files/Datenblaetter/BLDC/DB59-rund/DB59L-R/DB59L024035R-B.pdf` | 2026-06-01 | `scripts/configure_db59_odrive.py`, `README.md` |
| ODrive V3.6 / Nanotec DB59L024035R-B | Configured motor count and mapping | two DB59 motors controlled: axis0/M0 and axis1/M1; both configured with `pole_pairs=3`, `torque_constant=0.05`, `current_lim=9.4`, `calibration_current=5.0`, `requested_current_range=30.0`, `vel_limit=58.3 turn/s`; startup calibration and startup closed-loop disabled | User request plus Nanotec datasheet plus ODrive v0.5.6 docs; applied with `python3 src/igvc_odrive_interface/scripts/configure_db59_odrive.py --serial 315B32623431` | 2026-06-01 | live ODrive persistent config |
| ESP32 firmware | Serial baud | `115200` | `/home/igvc/Downloads/rutgers_igvc_electrical-main/estop_PCB/igvc_estop_receiver/src/main.cpp`, `Serial.begin(115200)` | 2026-05-27 | `igvc_estop_current` |
| ESP32 firmware | ADS1115 I2C address | `0x48` | firmware source line with `ADS1115 ADS(0x48)` | 2026-05-27 | ESP32 docs/parser assumptions |
| ESP32 firmware | ADC channel | `3` | firmware source line with `ADS.readADC(3)` | 2026-05-27 | `igvc_estop_current` |

## Safety implications of powered-hub e-stop behavior

- The ROS system must expect a single ESP32 e-stop action to remove multiple USB devices at once.
- Loss of camera/lidar/GPS/ODrive USB devices during e-stop should be reported as e-stop/power-loss stale state where possible, not misdiagnosed as unrelated hardware failures.
- After e-stop reset and powered hub restoration, launch/systemd/supervisor strategy should allow driver nodes to reconnect or be restarted cleanly.
- Verification must include an e-stop disconnect/reconnect test with `ros2 topic hz`, diagnostics, and `lsusb`/udev monitoring.

## Assumptions / needs confirmation

- Which peripherals are physically downstream of the powered USB hub must be verified by triggering e-stop while monitoring `lsusb` and ROS diagnostics.
- GPS serial data on `/dev/ttyACM0` still needs access after dialout/udev permission fix; device is a GPS candidate, not proven by NMEA output yet.
- ODrive native USB access and ROS telemetry are verified; CDC serial access still needs dialout/udev permission if raw serial is required.
- ODrive DB59 motor calibration is complete for both axes, but encoder feedback is not calibrated: incremental mode reported no response; Hall mode reported illegal Hall state with `hall_state=0`. Verify encoder/Hall wiring, power, and intended mode before closed-loop motion.
- Emlid Reach RS+ output protocol/baud must be confirmed from Reach settings or observed NMEA/UBX data.
- ACS770LCB-100U-PFF-T sensitivity and zero-current output must be confirmed from the exact datasheet before final current calibration.
- ADS1115 gain enum/full-scale mapping must be confirmed against the installed ADS1X15 library documentation/source before final current conversion.
