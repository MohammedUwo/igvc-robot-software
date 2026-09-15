# Hardware

## wireless-estop.md

[`wireless-estop.md`](wireless-estop.md) — the LoRa heartbeat design that closes Gate 05. Handheld
Adafruit Feather M0 transmitter sends a continuous "all clear"; the RAK3172 receiver board holds the
drive relay closed only while that heartbeat keeps arriving. Covers hardware, pin assignments, radio
settings, wiring, both firmware sketches, the bench commissioning sequence, and the items still to
verify before competition.

Boards: [`schematics/E-Stop Receiver Board`](schematics/E-Stop%20Receiver%20Board) (RX, "RUTGERS
IGVC ESTOP RX REV 1") and [`schematics/E-stop remote`](schematics/E-stop%20remote) (TX).

## schematics/

EasyEDA exports for all 18 Rutgers IGVC PCB projects — schematics as `.svg`, board layouts as
6-page fabrication PDFs. See [`schematics/INDEX.md`](schematics/INDEX.md) for the naming
convention and per-project notes.

The projects that matter for qualification:

| Project | Why it matters |
|---|---|
| `E-Stop Receiver Board` | The board that cuts motor power. Gate 05. Rev 1 has a known hazard — do not power it from USB and the terminals at once. |
| `E-stop remote` | Transmitter, incl. the RAK3172 breakout. Needs the heartbeat rewrite. |
| `Nikita's testing ESTOP` | Alternate RX/TX pair from the LoRa investigation |
| `LED Controller` | Safety light. Gate 06. Four board revisions; reference code in `legacy/pathfinder-led/`. |
| `Power Distribution Board` | Replaces the wago/spaghetti wiring. 4-layer 12 V / 5 V / 3V3. |
| `IMU Handler` | IMU + thermostat board, two revisions |
| `CANboardMaybe` | From the CAN-vs-USB investigation — see the E-Stop Wireless Remote doc |

Firmware for these boards is not here: it lives in
[ozatyx/rutgers_igvc_electrical](https://github.com/ozatyx/rutgers_igvc_electrical).
