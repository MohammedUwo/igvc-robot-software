# Handoff — Rutgers IGVC, September 2026

Written for whoever picks this up next: a new team member, or a fresh AI session with no memory
of how any of this got here. Everything below is either verifiable in this repo or linked.

---

## 1. The goal

> "Have a functioning robot by the end of this semester. It just needs to be able to qualify —
> it doesn't need any fancy PCBs, just a minimal design and function so it is able to qualify."

Target is **IGVC 2027** at Oakland University, late May 2027. Registration (~$500,
non-refundable) closes around 28 February 2027.

Qualification is ten pass/fail checks a judge performs with a tape measure and a stopwatch — not
a race. The full breakdown, with current status per gate, is in
[`qualification-plan.md`](qualification-plan.md). Read that before planning any work.

The team attended IGVC in May 2026 and failed qualification on mechanical, safety **and** autonomy.

---

## 2. Where everything is

### Repositories

| Link | What |
|---|---|
| [MohammedUwo/igvc-robot-software](https://github.com/MohammedUwo/igvc-robot-software) | **This repo.** Everything: both ROS workspaces, PCB exports, photos, docs, system config. Personal account, complete. |
| [Rutgers-IGVC-2026-2027/Old-Robot-](https://github.com/Rutgers-IGVC-2026-2027/Old-Robot-) | Team-org copy, nested under one `robot-software/` folder. **Behind** — has the software half only, not the photos/schematics/GETSENSORS. |
| [Rutgers-IGVC-2026-2027/Power-System-Processing-](https://github.com/Rutgers-IGVC-2026-2027/Power-System-Processing-) | Power sensing module → ROS 2. Separate effort, not examined. |
| [ozatyx/rutgers_igvc_electrical](https://github.com/ozatyx/rutgers_igvc_electrical) | E-stop TX/RX firmware, E-stop + current-sensing PCB, ODrive config, power diagrams, manual control. Clean, fully pushed, last commit May 2025. Has a [wiki](https://github.com/ozatyx/rutgers_igvc_electrical/wiki). |
| [kev197/rutgers_igvc](https://github.com/kev197/rutgers_igvc) | ROS 1 catkin workspace, 2 commits, build artifacts committed. **Never examined** — the last unopened thing. |
| [adoodevv/diff_drive_robot](https://github.com/adoodevv/diff_drive_robot) | Upstream tutorial package that `autonomy/diff_drive_robot` was forked from. |

### Google Drive

| Link | What |
|---|---|
| [RUIGVC](https://drive.google.com/drive/folders/14_LkNCPo5Y71Fl-R7mJpTYKmLOogfvpS) | Team folder. Budgeting, Funding, Reimbursements, Alumni Contacts, Subteam Project Docs, Photos. |
| [IGVC Project Signups](https://docs.google.com/spreadsheets/d/1Fp2fxqv8Yz1hzHz5CQFm-M1GybJNndiURRorJT166gg/edit) | The team's own task board — ~30 names, priorities, status. Most accurate picture of who is doing what. |
| [E-Stop Wireless Remote](https://docs.google.com/document/d/12v5iyWKgHmwqQCnYccDY-uYneQcSHL7CmXHSifTwTGM/edit) | Remote revamp spec: Full / Gentle / Disengage buttons, 100 ft rule, CAN-vs-ROS decision. |
| [E-Stop & Current Sensing Board 2nd Revision](https://docs.google.com/document/d/1Zi9gckQ8qKyqZ7sZ62QwZe2jwxI-TSgEYXUCCOjpX7Q/edit) | Rev-2 fix list for the board. |
| `gdrive:nuc-backup/tar/` | Full NUC disk images — 162 archives, 102 GiB. Index and restore command in [`nuc-backup-index.md`](nuc-backup-index.md). |

### Rules

[IGVC 2026 Official Rules](http://www.igvc.org/2026rules.pdf) — the 2027 rules were not published as
of September 2026. Assume these until they are.

---

## 3. What was done, and what it means

The NUC (`igvc-NUC12DCMi9`) was fully backed up on 3 September 2026 — 162 tar+zstd archives,
102.4 GiB, every one verified by download-and-list. **The machine has not been wiped yet.**

Going through that backup turned up the thing that mattered: **the team's autonomy code had never
been committed to any repository.** It existed only as an uncommitted working tree on that one
machine. One reinstall would have erased it. It is now `autonomy/diff_drive_robot/` here.

A first pass concluded the autonomy didn't exist at all, based on `igvc_ws/lane_following` being a
stub (stock ROS 2 demo launch files). That was wrong — the real work was in a differently-named
workspace. Anything written before ~10 September that says "write the autonomy from scratch" is
stale.

### The two code bases

Neither talks to the other. Joining them is most of the remaining work.

- **`autonomy/diff_drive_robot/`** — ~2,300 lines. Lane detection, gap following, GPS waypoints,
  behaviour arbitration with a fixed priority ladder, plus a full Gazebo model. Written against
  simulation; **never run on the real robot.**
- **`autonomy/getsensors/`** — May 2026, three packages with tests. Knows the real hardware:
  verified serials, ports, baud rates. Observe-only — it doesn't drive.

`getsensors` should stay the device layer; `diff_drive_robot` should be pointed at its topics
rather than keeping two ODrive interfaces and two lidar drivers.

---

## 4. Facts that change decisions

Each of these was discovered during this work and isn't obvious from the code.

1. **The e-stop cuts power to the USB hub.** Every peripheral on that hub disappears at once when
   it fires. Nodes must treat simultaneous device loss as an expected e-stop condition and
   reconnect after reset. Source: `autonomy/getsensors/docs/hardware_inventory.md`.
2. **The wireless e-stop is fail-unsafe.** The ESP-NOW firmware has no heartbeat — if the link
   drops, the robot keeps driving. The transmitter source says so in its own comments. IGVC
   requires ≥100 ft, hardware-based. Fix: transmitter pings continuously, receiver drops the relay
   after ~200 ms of silence. That replacement is now specified end to end in
   [`../hardware/wireless-estop.md`](../hardware/wireless-estop.md) — LoRa rather than ESP-NOW.
3. **The AutoNav course is asphalt**, with ramps to 15% grade. Not grass. This is what makes omni
   wheels viable at all.
4. **Free-rolling omni wheels don't resist lateral motion.** On a 15% cross-slope the unpowered end
   crabs downhill and software can't fix it. Either drive all four (two ODrives, ~$400–700 you
   don't have) or use two driven traction wheels plus two free omnis (keeps the single ODrive and
   every line of existing code).
5. **`odrive.py` carries simulation geometry** — `wheel_radius = 0.05`, `wheel_base = 0.3` are
   tutorial defaults. Every velocity command is scaled wrong until measured.
6. **Top speed is already ~1.75 mph** per the team's own task board — inside the 1–5 mph window.
7. **The saved TF dump reads `"No tf data received"`.** The EKF, SLAM and Nav2 are all inert
   without a transform tree.
8. **Motors are Nanotec `DB59L024035R-B` BLDC** on ODrive V3.6 (serial `315B32623431`, fw 0.5.6).
9. **SLAM is a liability, not an asset.** The rules forbid course memorisation and judges change
   the course between runs. `autonomous_drive.launch.py` still starts `slam_toolbox` — drop it.
   The reactive priority ladder in `behavior_node.py` is the right architecture and already exists.

---

## 5. Open decisions

| Decision | Status |
|---|---|
| Wheel/drive configuration | Team is building a new chassis with four omni wheels. Drive-count not settled — see fact 4. |
| Keep the 800 W inverter, or go DC-DC to the NUC? | Unassigned on the team task board. Measure actual draw first. |
| Gentle E-stop over CAN or ROS? | Spec'd in the Drive doc, not decided. |

## 6. Blocking questions for the team

1. Tape-measured length, width, height, and E-stop button height off the ground. Three gates are
   pure measurements.
2. Does the drivetrain still turn under manual control?
3. Which end is the front? The mechanical E-stop must sit centre rear.
4. Discord history from the May 2026 competition weekend — the judges' actual qualification
   feedback is the most precise specification available, and nobody has retrieved it.

## 7. Next actions, in order

Phases 1 and 2 are bench work and don't wait on the chassis.

1. **E-stop heartbeat rewrite** — hard gate, testable on a bench with the two radios and a relay.
   Design, firmware and commissioning steps: [`../hardware/wireless-estop.md`](../hardware/wireless-estop.md).
2. **Safety light** — hard gate. Reference implementation in `legacy/pathfinder-led/`.
3. **Sensor bring-up** with a non-empty TF tree. Use `autonomy/getsensors/` — it already has the
   launch files and the udev rules.
4. **Measure and set the drivetrain constants**, and reconcile `vel_limit` (30 in code, 50 in the
   board config).
5. **Chassis** to the gate 01–03 envelope, with the rear E-stop position and payload cradle
   designed in, not retrofitted.
6. **Tune lane following and obstacle avoidance** — use `simulation/dynamic-autonav-course/` before
   going outside.

---

## 8. Outstanding security items

Not optional, and not yet done:

- **A live Cloudflare tunnel token** is in the NUC's `.bash_history` (an `eyJhIjoi…` string, used
  three times). Anyone holding it can stand up a tunnel into the network. **Revoke it** in the
  Cloudflare Zero Trust dashboard.
- **The NUC password** was typed at a `sudo` prompt and captured in that same history. Rotate it.
- **A Google OAuth client secret** was shared during the backup setup. Rotate it in the Google
  Cloud console.
- **`/etc/sudoers.d/igvc-nopasswd`** on the NUC grants passwordless sudo. It was added deliberately
  for the backup. Remove it after the rebuild: `sudo rm /etc/sudoers.d/igvc-nopasswd`.
- `C:\Users\peppe\nuc\tok.out` on the work laptop holds the rclone OAuth token. Delete it once the
  backup work is finished.

Neither the shell history nor the SSH keys are in this repo — they were excluded on purpose. Both
are still inside the Drive archives; treat `p3-home-igvc_-.bash_history_.tar.zst` and the `.ssh`
archives as secret-bearing.

---

## 9. Working notes for the next session

Practical things that cost time to rediscover:

- **The NUC is at `172.30.111.245`, user `igvc`**, SSH enabled, sleep/suspend masked so it stays
  reachable. Credentials are with the team lead, not in this repo.
- `C:\Users\peppe\nuc\nucx.py` is a paramiko helper for that machine. It exists because
  `ssh.exe` and `scp.exe` fail silently under the device bridge's restricted token — they exit 255
  with zero output. Paramiko works; OpenSSH binaries do not.
- Windows Python defaults to cp1252 and will crash on box-drawing characters in `lsblk` output.
  Set `PYTHONIOENCODING=utf-8` and `sys.stdout.reconfigure(encoding="utf-8", errors="replace")`.
  This was misdiagnosed as connection failures for about twenty minutes.
- PowerShell's `-Encoding utf8` writes a BOM, which mangles the first line of any shell script
  uploaded to Linux. Use `[System.IO.File]::WriteAllText(path, text, UTF8Encoding($false))`.
- **Don't use plain `rclone copy` to back up a Linux filesystem.** It silently skipped 56,530
  symlinks — including `/bin` and `/lib32` — and Drive stores no permissions or ownership. Use
  `tar | zstd | rclone rcat`, which is also ~6.5× faster.
- Windows ships `bsdtar` with zstd built in, so `.tar.zst` archives extract natively — no extra
  tooling needed.
- GitHub pushes run from the laptop (`C:\Users\peppe\igvc\`), not from a cloud session. Cloud
  sessions have no GitHub credentials and the device-code flow is blocked.
- `C:\Users\peppe\nuc\dl\` holds the 4 GB Downloads archive. Everything useful was extracted;
  it can be deleted.

## 10. Known-stale

- The "Ten Gates" HTML artifact from 6 September says the autonomy must be written from scratch and
  assumes a grass course. Both wrong. [`qualification-plan.md`](qualification-plan.md) supersedes it.
- `Old-Robot-` in the team org is behind this repo.
