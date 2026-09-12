# Rutgers IGVC — Lab Inventory

**Last updated:** 6 September 2026
**Maintainer:** Mohammed Halai

This is the "where is it and what is it for" document. If you are new to the team, read
[Start here](#start-here) first, then skim the [Quick index](#quick-index).

**Convention used below:**
`✅ CONFIRMED` — verified in photos or in person.
`📍 TBD` — we know we own it; someone needs to write down where it lives. Fill these in.
`⚠️` — read the note, it will save you time or hardware.

**Do not put passwords, API keys, or OAuth secrets in this file.** Credentials live in the
team password manager / with the lead. See [Accounts](#accounts-and-services).

---

## Start here

We build an autonomous ground vehicle for the [Intelligent Ground Vehicle
Competition](http://www.igvc.org). Our next target is **IGVC 2027** at Oakland University,
Rochester MI, around late May 2027.

The single thing worth understanding before you touch anything: **qualification is ten
pass/fail checks**, not a race. A judge measures the robot, tests both emergency stops,
watches the safety light, and confirms it can follow a lane, avoid an obstacle, and reach a
GPS waypoint. Nothing about speed or sophistication counts until those ten pass. Most of
what we build is aimed squarely at that list.

**The robot is currently mid-rework.** The power distribution panel is off the vehicle on a
clear acrylic plate. It has not driven recently.

---

## Quick index

| I need… | Go to |
|---|---|
| A microcontroller | [Compute and controllers](#compute-and-controllers) |
| A camera, lidar, or GPS | [Sensors](#sensors) |
| Anything that makes the robot move | [Drive](#drive) |
| Batteries, fuses, converters | [Power](#power) |
| E-stop parts, the safety light | [Safety systems](#safety-systems) |
| A LoRa or ESP-NOW radio | [Radios](#radios) |
| Resistors, caps, MOSFETs | [Electronic components](#electronic-components) |
| Connectors, wire, crimps | [Connectors and wire](#connectors-and-wire) |
| T-slot nuts, brackets, bearings | [Mechanical hardware](#mechanical-hardware) |
| A soldering iron, scope, printer | [Bench and tools](#bench-and-tools) |
| The code | [Code and repos](#code-and-repos) |

---

## The robot

**Platform:** 80/20 aluminum T-slot frame, four pneumatic knobby wheels, roller-chain drive,
plywood equipment decks, clear acrylic side panels.

| Subsystem | What's on the robot | Status |
|---|---|---|
| Frame | 80/20 extrusion, plywood decks | Assembled |
| Drive | 2 × brushed DC gearmotors, chain, sprockets | Assembled, untested recently |
| Motor control | ODrive + 50 W 2 Ω brake resistor | Mounted |
| Compute | Intel NUC12DCMi9 | Mounted |
| Sensing | 2D lidar + depth camera on front mast | Mounted |
| Power | 24 V 50 Ah pack, distribution panel | ⚠️ **Panel currently removed** |
| E-stop | Mushroom button on front mast | ⚠️ **Wrong position — must move to centre rear** |
| Safety light | Not installed | Amber bars are in the lab, unwired |
| Payload mount | Not built | Competition requires carrying 20 lb |

⚠️ **Two known rule violations to fix before anything else:** the mechanical E-stop must sit
at the **centre rear**, 2–4 ft off the ground (ours is on the front mast), and the wireless
E-stop currently has **no heartbeat** — if the radio link drops, the robot keeps driving.
Both are cheap fixes and both are hard qualification gates.

---

## Compute and controllers

| Item | Qty | What it's for | Location |
|---|---|---|---|
| Intel NUC12DCMi9 | 1 | Main robot computer. Ubuntu 22.04, ROS 2 Humble. Hostname `igvc-NUC12DCMi9` | On the robot ✅ |
| Pixhawk 4 (Holybro) | 1 | Flight controller — we use it as a GPS + IMU + compass source for waypoint navigation | 📍 TBD |
| STM32 Nucleo-H723ZG | 1 | High-performance MCU dev board | 📍 TBD |
| ST-LINK/V2 programmers | several | Flashing and debugging STM32 boards | Parts drawer labelled `ST-LINKS` ✅ |
| ESP32 dev boards (Inland) | ≥1 | General ESP32 work; the E-stop system is ESP32-based | 📍 TBD |
| Seeed XIAO boards | ≥2 | Tiny ESP32/SAMD boards for small jobs | 📍 TBD |
| Digilent Zybo + Pmod kits | 1 + kits | FPGA board, from a Digilent sponsorship. Not used on the robot | 📍 TBD |
| Raspberry Pi proto HAT | 1 | Prototyping board | 📍 TBD |
| USB-serial adapters (CP2102/CH340) | several | Talking to microcontrollers over serial | 📍 TBD |

**NUC access:** `ssh igvc@172.30.111.245`, username `igvc`. Credentials from the team lead —
**not in this file.**

---

## Sensors

| Item | Qty | What it's for | Location |
|---|---|---|---|
| 2D lidar (RPLidar-class) | 1 | Obstacle detection. Spinning black cylinder on the front mast | On the robot ✅ |
| Depth/stereo camera | 1 | Lane detection. Red-and-white unit on the mast | On the robot ✅ |
| MPU-6050 IMU | ~100 | Accelerometer + gyro. Bulk stock from an LCSC order | With the LCSC component bags 📍 |
| Fingerprint sensor | 1 | Not used on the robot | 📍 TBD |

⚠️ **Someone needs to read the model numbers off the lidar and the camera housings.** The
ROS driver, the calibration procedure, and the launch files all differ between an Intel
RealSense and a Luxonis OAK. We currently have driver packages checked out for *both*, which
is why nobody is sure which one is actually mounted.

---

## Drive

| Item | Qty | What it's for | Location |
|---|---|---|---|
| Brushed DC gearmotors | 2 | Main drive. Marked `GPMS-52-26-SER` | On the robot ✅ |
| ODrive motor controller | 1 | Closed-loop control of both motors from the NUC over USB | On the robot ✅ |
| Brake resistor, 50 W 2 Ω | 1 | Dumps regenerative braking energy. **Required** — without it the ODrive faults on decel | On the robot, next to the ODrive ✅ |
| Roller chain + sprockets | — | Motor to wheel | On the robot ✅ |
| Pneumatic knobby wheels | 4 + 1 spare | Spare is new, still bagged | Spare 📍 TBD |
| Pillow block bearings | several | Shaft support | Orange bin ✅ |
| Wheel hubs / flanges | several | Wheel-to-shaft mounting | Yellow bin ✅ |
| Shaft collars, keyed shaft | several | Drivetrain assembly | 📍 TBD |

**ODrive working configuration** — saved as
`ODrive_config/odrive-config-3659385B3030.json` in the electrical repo:

```
axis0/1.motor.config.current_lim        30.0 A
axis0/1.motor.config.pole_pairs         3
axis0/1.motor.config.torque_constant    0.05
axis0/1.encoder.config.cpr              4096
axis0/1.controller.config.vel_limit     50.0
axis0/1.trap_traj.config.vel_limit      2.0
```

⚠️ **Restore this file rather than re-tuning from scratch.** It represents a working
calibration and saves days. `vel_limit` is also our hardware speed governor for the
competition's 5 mph ceiling — once it's set and we qualify at that speed, **it must not be
changed.**

---

## Power

| Item | Qty | What it's for | Location |
|---|---|---|---|
| Dakota Lithium 24 V 50 Ah | 1+ | Main robot battery | Under the bench ✅ |
| AGM battery (Optima-style) | 1 | Secondary / older pack | Under the bench ✅ |
| SkyRC iMax B6 mini charger | 1 | Balance charger for LiPo/LiFe/Li-ion | 📍 TBD |
| 80 A ANL bolt-down fuse + holder | 1 | Main battery protection | On the power panel ✅ |
| Blade fuses + inline holders | several | Branch circuit protection | 📍 TBD |
| ZK-12KX V2 buck converter | 1 | Adjustable step-down with OLED readout | On the power panel ✅ |
| 5 V and 12 V step-down modules | several | Rails for logic and sensors | 📍 TBD |
| 800 W pure sine inverter | 1 | Currently powers the NUC via its AC brick | On the robot ⚠️ |
| Distribution blocks + GND busbar | 2 | Power distribution | On the power panel ✅ |
| Main rocker switch | 1 | Master power | On the power panel ✅ |
| PPTC resettable fuses | 5 | Board-level protection | LCSC bags 📍 |

⚠️ **The inverter should eventually go.** Converting 24 V DC → 120 V AC → back to 19 V DC to
feed the NUC wastes a large fraction of the battery and adds weight and a failure point. A
24 V → 19 V DC-DC does the same job far more efficiently. Not a qualification issue, so it's
not urgent — but it's why runtime is poor.

---

## Safety systems

These map directly onto competition requirements, so treat them as first-class.

| Item | Qty | What it's for | Location |
|---|---|---|---|
| E-stop mushroom buttons | several | Mechanical emergency stop. Red, latching, ≥1 in | 📍 TBD |
| 3D-printed E-stop enclosures | several | Red and black printed housings for the buttons | 📍 TBD |
| Amber LED strobe light bars | 2–3 | **This is our safety light.** Solid when powered, flashing in autonomous mode | 📍 TBD |
| Rutgers IGVC E-Stop & Current Sensing PCB rev 1 | ≥1 | Custom board: ESP32 + 2 power MOSFETs + ADS1115 current sensing + XT60 in/out | On the power panel ✅ |
| 4-channel relay module | 1 | Switching the safety light and other loads | On the robot ✅ |
| Spare bare E-stop PCBs | several | Unpopulated boards from JLCPCB | Blue JLCPCB boxes 📍 |

**How the E-stop works:** an ESP32 on the custom board receives ESP-NOW packets from a
handheld transmitter. On a stop command it drives `GPIO 33`, which switches the power
MOSFETs and cuts motor power. Firmware lives in the electrical repo under
`estop_PCB/igvc_estop_receiver/` and `estop_remote/igvc_estop_transmitter/`.

⚠️ **Known defect:** the transmitter has no heartbeat. The original author left the comment
*"should work as is but wont know if they are out of range."* If the link drops, the robot
keeps driving. This is fail-unsafe and will fail qualification, where a judge stands 100 ft
away holding the remote. The fix is a watchdog — the receiver expects a packet every N ms
and cuts power if one doesn't arrive.

⚠️ `LED_controller/` in the repo contains a single file called `temp_filler.txt`. The safety
light has never been implemented in software, despite us owning the lights.

---

## Radios

| Item | Qty | Notes | Location |
|---|---|---|---|
| RAK3172 LoRa modules | several | 900 MHz LoRa. Longer range and far more robust than ESP-NOW in a crowded 2.4 GHz field | 📍 TBD |
| Adafruit Feather M0 with LoRa | ≥1 | LoRa transmitter option | 📍 TBD |
| 900 MHz whip antennas | several | Large black rubber-duck style | 📍 TBD |
| u.FL → SMA pigtails | several | Antenna connections for small boards | 📍 TBD |

**Current design decision:** stay on the existing **ESP32 / ESP-NOW** board because it is
already built, add the heartbeat, and range-test past 100 ft. Only move to LoRa if that test
fails. The LoRa module can drive the same MOSFETs, so it is a radio swap, not a board
redesign.

---

## Electronic components

Mostly a July 2026 LCSC and DigiKey order placed to assemble more E-stop boards, plus
general stock.

| Category | Examples we hold |
|---|---|
| Passives | 0603 resistors and ceramic caps in bulk (100 nF, 2.2 nF, 100 Ω, 1 % values); SMD resistor kit book; 500-pc SMD capacitor assortment |
| Semiconductors | AO3400 / 2N7002 N-channel MOSFETs, P-channel MOSFETs, SS14 Schottky diodes, BJTs in SOT-23 and TO-92 |
| Regulators | AMS1117-3.3 (SOT-223), assorted linear regulators |
| ICs | CH340-family USB-serial converters, RS-485 transceivers (TI, DigiKey), Li-ion battery management ICs |
| Indicators | 520 nm green 0603 LEDs (×100) |
| Switches | SMD tactile switches, 4 mm × 3 mm and 6 mm |
| Filtering | 100 Ω ferrite beads 0603, PPTC resettable fuses |

**Storage:** two large Husky multi-drawer cabinets on the bench, drawers individually
labelled. Confirmed labels include `ST-LINKS`, `MISC CAPACITORS`, `MISC VOLTAGE
REGULATORS`, `2mm JST XH CONNECTORS`, `5.08mm MALE HEADERS`, `3.5mm FEMALE HEADERS`,
`PUSHBUTTONS`. ✅

⚠️ **Everything from LCSC is surface-mount.** If you need through-hole parts for
breadboarding, check the drawers rather than the LCSC bags.

---

## Connectors and wire

| Item | Notes | Location |
|---|---|---|
| XT60 / XT90 connectors | Main power connections, bagged in ~10s | 📍 TBD |
| XT30 connectors | Smaller power runs | LCSC bags 📍 |
| JST-XH 2.5 mm headers | Board-to-wire | Labelled drawer ✅ |
| 0.1 in headers, male and female | Right-angle and straight | Labelled drawers ✅ |
| Wago lever connectors | Quick splices — used on the robot decks | On the robot ✅ |
| Dupont jumper wires | Prototyping | 📍 TBD |
| Wire spools | Multiple gauges and colours | Pegboard ✅ |
| Ring terminals, heat shrink | Battery and high-current terminations | 📍 TBD |
| Crimping tools | Ratcheting crimper for JST/Dupont | Pegboard ✅ |

---

## Mechanical hardware

| Item | Notes | Location |
|---|---|---|
| 80/20 T-slot extrusion | Various lengths, plus spare stock | Black toolbox + 📍 |
| T-slot nuts | Bags of several hundred | 📍 TBD |
| Corner brackets, gussets, plates | Aluminium, various | Orange bin ✅ |
| Rivet nut kit | M3 / M4 / M5 / M6 / M8, 102 pc | 📍 TBD |
| Machine screws, nuts, washers | Extensive, sorted | Yellow bins ✅ |
| Lag bolts, threaded rod | 📍 TBD |
| Wire rope + ferrules | 📍 TBD |
| Anodized standoffs | Blue aluminium | 📍 TBD |
| Pillow block bearings, hubs | See [Drive](#drive) | Orange bin ✅ |

---

## Bench and tools

| Item | Notes | Location |
|---|---|---|
| Rigol oscilloscope | Bench, main electronics station ✅ |
| Bench power supply | Bench ✅ |
| Weller soldering station | Bench ✅ |
| SMD reflow hotplate | For surface-mount assembly and rework | Bench ✅ |
| 3D printers | In the lab ✅ |
| Multimeter(s) | Pegboard ✅ |
| Hand tools | Pliers, cutters, drivers, hex keys | Pegboard ✅ |
| Husky 20-pc socket wrench set | 📍 TBD |
| IRONANT step drill set | 1/8"–1 3/8" | 📍 TBD |
| Precision screwdriver set | 📍 TBD |
| Solder, Sn63/Pb37 0.8 mm | Bench ✅ |

⚠️ **Hotplate note:** a previous session charred the FR4 on a board at 340 °C. Start lower
and go up; most leaded paste reflows well under 250 °C.

---

## Code and repos

| Repo | What's in it |
|---|---|
| [`ozatyx/rutgers_igvc_electrical`](https://github.com/ozatyx/rutgers_igvc_electrical) | E-stop firmware (receiver + transmitter), E-stop PCB (EasyEDA), ODrive config and manual-control scripts, LED controller (empty), power distribution diagrams |
| `kev197/rutgers_igvc` | ROS navigation package — referenced from the electrical repo's README |
| `rutgers/IGVC21-22` | 2021–22 season: ROS 1 catkin workspace and electronics |

**On the NUC** (`/home/igvc/`):

| Path | Contents |
|---|---|
| `igvc_ws/src/` | Our packages: `lane_following`, `will_robot`, `will`, `sim1` |
| `ros2_ws/src/` | Third-party: RTAB-Map, realsense-ros, rplidar_ros, depthai-ros, pointcloud_to_grid |
| `dai_ws/` | Luxonis DepthAI ROS workspace |
| `gz_ws/` | Gazebo simulation workspace |

⚠️ **Honest state of the software:** the autonomy is not written. `lane_following` contains
launch files and no nodes — two of them are the stock ROS 2 tutorial talker/listener demos.
`will_robot` is a publisher/subscriber exercise. `sim1` is an empty package skeleton. Do not
assume any of this works; plan on writing the navigation stack from scratch.

**Architecture decision:** we are building a **reactive** stack, not SLAM. The competition
rules forbid mapping and course memorisation, and judges reshuffle the course between runs
specifically to defeat it. Four small nodes — lane detection, gap-following obstacle
avoidance, GPS waypoint bearing, and a priority arbiter — clear every autonomy requirement
in a few hundred debuggable lines. The RTAB-Map work in `ros2_ws` is a dead end.

---

## Backups

The NUC's full contents were backed up in September 2026 before a planned wipe and
reinstall. Both Ubuntu installations on the drive were archived and verified.

- **Location:** Google Drive, `nuc-backup/tar/`
- **Format:** one zstd-compressed tar per top-level directory, preserving permissions,
  ownership, and symlinks
- **Size:** 162 archives, 102.4 GiB
- **Verified:** every archive was downloaded, decompressed, and listed — zero failures
- **Also included:** a system manifest with the partition table, package lists for both
  installations, `fstab`, `blkid` UUIDs, and hardware inventory

⚠️ The NUC has **two** Ubuntu installations on one drive — a 92 GB partition running the
current system, and a **469 GB partition with a second install** under user `rieee` that
contains Vivado and about 120 GB of home directory. Do not repartition without checking
both.

---

## Accounts and services

| Service | Used for |
|---|---|
| Google Drive | Backups, photos, documents |
| JLCPCB | PCB fabrication — we have order history |
| LCSC / DigiKey | Component sourcing |
| GitHub | Code, under several personal accounts (see [Code and repos](#code-and-repos)) |

**Credentials are not stored in this repository.** Ask the team lead.

**Sponsors** (per the sticker panel built for the robot): Texas Instruments, IEEE, Digilent,
onsemi, Knowles, OSH Park, GitHub, PNI, 80/20 Inc.

---

## Known gaps

Things we do *not* have, or that are incomplete, so nobody wastes time looking:

- **Safety light wiring and firmware** — hardware exists, nothing is connected
- **Payload mount** — competition requires securely carrying a 20 lb, 16 × 8 × 8 in block
- **Lane following, obstacle avoidance, waypoint navigation** — all unwritten
- **E-stop heartbeat** — the wireless stop is currently fail-unsafe
- **Robot dimensions** — never recorded; three qualification checks depend on them
- **A documented wiring diagram** for the current power panel — only drawio sketches exist

---

## Contributing to this document

If you find something, put it back where you found it and **update the location here**. A
`📍 TBD` you resolve in thirty seconds saves the next person twenty minutes. Note the date
and your name at the top when you make a substantive change.
