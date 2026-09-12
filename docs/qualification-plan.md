# Ten gates to qualification

**Target:** IGVC 2027, Oakland University, late May 2027.
**Revised:** 12 September 2026. Supersedes the 6 Sept version, which was wrong on three counts —
see [Corrections](#corrections).

Qualification is not a race. It is ten pass/fail checks a judge performs with a tape measure and
a stopwatch. Nothing about speed, elegance or placing counts until those ten pass. This plan
targets them and ignores everything else.

## Corrections to the earlier plan

1. **The autonomy exists.** The earlier plan said it had to be written from scratch, based on
   `igvc_ws/lane_following` being a stub. It is a stub — but the real stack was in
   `gz_ws/ros2_ws/src/diff_drive_robot`, ~2,300 lines, uncommitted, recovered into `autonomy/`
   in this repo. The schedule below assumes fixing and integrating it, not writing it.
2. **The course is asphalt.** Not grass. Ramps up to 15% grade. This matters for the wheel choice.
3. **Top speed is already measured** at roughly 1.75 mph per the team's own task board — above the
   1 mph minimum, well under the 5 mph cap. Gate 07 is close to met.

## The gates

| # | Check | Spec | Status | What closes it |
|---|---|---|---|---|
| 01 | Length | 3–7 ft | Unmeasured | Tape measure. New chassis — design to spec. |
| 02 | Width | 2–4 ft | Unmeasured | Prime suspect for the 2026 mechanical failure. Design the new chassis inside 4 ft. |
| 03 | Height | ≤6 ft, excl. antenna | Unmeasured | Record it. |
| 04 | Mechanical E-stop | Red, ≥1 in, push-to-stop, **centre rear, 2–4 ft high**, hardware only | Wrong place | Was on the front mast. The new chassis needs a rear mast or plate at that height — design it in now. |
| 05 | Wireless E-stop | ≥100 ft, hardware only | **Fail-unsafe** | ESP-NOW firmware has no heartbeat: link loss leaves the robot driving. Invert it — transmitter pings continuously, receiver drops the relay after ~200 ms of silence. Then range-test past 100 ft. |
| 06 | Safety light | Solid = powered, flashing = autonomous | Unwired | Amber bars are in the lab. Reference implementation in `legacy/pathfinder-led/`. |
| 07 | Speed | ≥1 mph avg, ≤5 mph, hardware-governed | Nearly met | ~1.75 mph measured. Set ODrive `vel_limit` deliberately and record it — no changes after you pass. |
| 08 | Lane following | Detect and follow | Code exists, untested on hardware | `detect_line.py` + `behavior_node.py`. Needs a real camera feed and tuning. |
| 09 | Obstacle avoidance | Detect and avoid | Code exists, untested on hardware | `rplidar_driver.py` → `behavior_node.py` priority ladder. |
| 10 | Waypoint nav | Reach a 2 m waypoint around an obstacle, **integrated, not a separate mode** | Code exists, untested | `emlid_gps.py` + `waypoint_driver.py` feed the same arbiter. The integration requirement is already satisfied by the architecture. |
| 11 | Payload | 20 lb, ~16×8×8 in, securely mounted | No mount | Build a bolted cradle into the new chassis. If it falls off mid-run, the run ends. |

Two traps in the fine print: the waypoint software **cannot be a separate mode** — the rules
require it be integrated into the original autonomous software. And max speed must be governed in
hardware with no changes after you pass; running a performance event faster than your
qualification speed voids it.

## Mechanical direction

The team is building a new chassis in-house with four omnidirectional wheels.

On asphalt, omni wheels are viable — the traction objection that applies on grass does not apply
here. The real constraint is the 15% ramp: **free-rolling omni wheels do not resist lateral
motion**, so on a cross-slope the unpowered end crabs downhill and no amount of software fixes it.
Two ways out:

- Drive all four → four motor axes → **two ODrives**. You have one (two axes) and two motors.
  That is roughly $400–700 in controllers plus two motors, against a few-hundred-dollar budget.
- **Two driven rubber traction wheels + two free omnis or casters.** Keeps the single ODrive, both
  motors, `diff_drive_controller`, and every line of the recovered code.

Nothing in AutoNav rewards holonomic motion. The second option is the recommendation.

## Software direction: reactive, not SLAM

The rules state: *"Mapping or course position memorization is not allowed. Judges will adjust
course between runs to nullify any mapping."*

`autonomous_drive.launch.py` currently starts `slam_toolbox` and a Nav2 local costmap. Drop
SLAM Toolbox from the launch. Keep `behavior_node.py`'s fixed priority ladder — critical lidar,
then camera obstacle, then waypoint, then line following. That ladder is exactly the reactive
architecture the rules push you toward, and it is already written.

## Blocking work, in order

Everything in phase 1 and 2 is bench work and does not wait on the chassis.

**Phase 1 — safety gates (bench).**
Rewrite the E-stop with a receiver-side watchdog. Port the safety light from
`legacy/pathfinder-led/` and drive it from a spare GPIO through the relay module. Both are hard
gates and both are testable on a table.

**Phase 2 — sensors talking (bench).**
RPLIDAR A1, OAK-D and Emlid Reach publishing on the rebuilt NUC with a **TF tree that is not
empty** — the saved dump reads `"No tf data received"`, and Nav2, SLAM and the EKF are all inert
without it. Record a bag for offline development.

**Phase 3 — drivetrain constants.**
`odrive.py` still carries `wheel_radius = 0.05` and `wheel_base = 0.3`, the tutorial defaults.
Measure the real values once wheels are chosen. Reconcile `vel_limit` (30 in code, 50 in the saved
board config) and set it to whatever caps you at 5 mph.

**Phase 4 — chassis and mounting.**
Build to the envelope in gates 01–03, with the rear E-stop position and the payload cradle
designed in rather than retrofitted.

**Phase 5 — tune on hardware.**
Lane following and obstacle avoidance against a taped practice lane (10 ft wide, 3 in white tape,
barrels). Longest and riskiest phase.

**Phase 6 — rehearse the inspection.**
Run all ten gates exactly as a judge would, with someone else holding the wireless E-stop. Repeat
until it passes twice consecutively.

## Money

| Item | Cost |
|---|---|
| IGVC 2027 registration (non-refundable, ~28 Feb deadline) | $500 |
| Certificate of insurance, $1 M via Rutgers risk management | $0 (institutional, but takes weeks — start in November) |
| Lane tape, barrels, practice consumables | ~$60 |
| Connectors, wire, fasteners | ~$40 |
| Chassis material | TBD |
| Contingency (a failed motor or ODrive is the real risk) | ~$150 |

Registration is the line that needs a funding conversation. The sponsor panel already lists TI,
onsemi, Digilent, OSH Park and 80/20.

## Still needed

1. Tape-measured length, width, height, and E-stop button height.
2. Does the drivetrain still turn under manual control?
3. Confirmed lidar and camera model numbers.
4. Discord history from the May 2026 competition weekend — the judges' actual qualification
   feedback is the most precise specification available, and it is free.
5. Which end is the front.

---

Sources: [IGVC 2026 Official Rules](http://www.igvc.org/2026rules.pdf) §I.2, §I.4, §II; the `igvc`
and `rieee` home directories from the NUC backup; `ozatyx/rutgers_igvc_electrical`; the team task
board in the RUIGVC Drive; 156 lab and robot photographs.
