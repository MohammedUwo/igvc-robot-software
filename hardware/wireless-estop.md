# Rutgers IGVC — Wireless Emergency-Stop (E-Stop)

A wireless safety cutoff for the IGVC ground vehicle. A handheld transmitter sends a
continuous "all clear" heartbeat over a LoRa radio link. The receiver on the robot
keeps the drive relay energized **only** while that heartbeat keeps arriving. Pressing
the E-stop button, losing the radio link, or losing power to either unit all result in
the relay de-energizing, which cuts motor power.

This is a **safety-critical system**. Read the [Safety](#safety) and
[Commissioning & Testing](#commissioning--testing) sections before relying on it.

---

## Contents

1. [How it works](#how-it-works)
2. [System architecture](#system-architecture)
3. [Hardware](#hardware)
4. [Pin assignments](#pin-assignments)
5. [LoRa radio settings](#lora-radio-settings)
6. [Wiring](#wiring)
7. [Software setup & flashing](#software-setup--flashing)
8. [Firmware](#firmware)
9. [Operating behavior (state logic)](#operating-behavior-state-logic)
10. [Commissioning & testing](#commissioning--testing)
11. [Troubleshooting](#troubleshooting)
12. [Safety](#safety)
13. [Open items / verify before competition](#open-items--verify-before-competition)

---

## How it works

- The **transmitter** sends a one-byte packet on a fixed cadence:
  - `0x01` — heartbeat ("safe / run"), every 200 ms while the E-stop is released.
  - `0x02` — E-stop ("stop"), sent continuously while the button is pressed.
- The **receiver** listens continuously and, after every packet, replies with `0xAA`
  ("pong") so the transmitter can confirm the link is alive.
- The receiver drives a single GPIO (`PA0`) that controls the drive relay through an
  on-board MOSFET. **HIGH = relay energized = motors enabled. LOW = relay
  de-energized = motors cut.**
- The receiver is **fail-safe**: it boots in the stopped state and only enables the
  motors while heartbeats keep arriving. Any of the following force it back to stop:
  E-stop pressed, radio link lost (no heartbeat within 750 ms), a broken button wire,
  or loss of power to either unit.

---

## System architecture

```
[ E-STOP BUTTON ]                         ON THE ROBOT
   (NC contact)                  ┌─────────────────────────────────────┐
        │                        │                                     │
        ▼                        │   RAK3172 RX board                  │
 ┌──────────────┐   915 MHz LoRa │   ┌──────────┐                      │
 │ Feather M0   │ ─────0x01─────► │   │ RAK3172  │ PA0 ──► Q1 (MOSFET) ─┼──► Relay module IN
 │ RFM9x (TX)   │ ◄────0xAA────── │   │  (RX)    │                      │      (SONGLE 12 V)
 │  + button    │      pong       │   └──────────┘                      │           │
 └──────────────┘                 └─────────────────────────────────────┘           ▼
                                                                            Relay contacts in
                                                                            the motor / ODrive
                                                                            power path
```

Two units:

- **Transmitter (handheld):** Adafruit Feather M0 RFM9x (900 MHz / US 915) + physical
  E-stop button. Arduino firmware using the Sandeep Mistry `LoRa` library.
- **Receiver (on robot):** Custom PCB *"RUTGERS IGVC ESTOP RX REV 1"* with a RAK3172
  LoRa module (RUI3 firmware). Drives the relay that gates motor power.

---

## Hardware

### Transmitter

| Item | Notes |
|---|---|
| Adafruit Feather M0 RFM9x LoRa, 900 MHz | US 915 MHz band; RFM95 (SX127x) radio |
| Antenna | ~78 mm (3.12") wire whip soldered into the **Ant** pad (quarter-wave for 915 MHz) |
| E-stop button | Using the **NC** contact (see wiring) |
| Power | USB, or a 3.7 V LiPo on the JST connector |

### Receiver (RX PCB)

The RAK3172 module is soldered to U1. For basic operation the following must be
populated:

| Block | Parts | Required? |
|---|---|---|
| RAK3172 module | U1 | Yes |
| Power input protection | D1 (SS14), F1 (MF-R050 PTC) | Yes |
| 3.3 V regulator | U2 (AP2112K-3.3) + C1 (10 µF), C3 (1 µF in), C2 (1 µF out) | Yes |
| RAK decoupling | C5 (100 nF), C6 (10 µF) | Yes |
| Boot select | R6 (10 kΩ BOOT0 pull-down); H1 jumper in **run** position | Yes |
| Reset | R5 (10 kΩ pull-up), C7 (100 nF); SW1 button optional | Recommended |
| Output stage | Q1 (IRLML0040), R7 (gate resistor), CN2 output | Yes |
| Status LEDs | LED1 (PA1, blue), LED2 (PA12, red) + R3/R4 | Optional but useful |
| USB-UART | U3 (CH340E), USB-C, R1/R2, C4 | **Not populated** (see note) |

> **Note — reflashing the RX:** Because the CH340E/USB-C is not populated, the RX board
> has no USB serial. To view its serial output or reflash it you need an **external
> USB-to-UART (3.3 V) adapter** on the RAK's UART2 pins, or use the SWD pins. The
> firmware lives in the RAK module's internal flash and **persists** even when the
> module is desoldered and moved to another board.

### Relay

| Item | Notes |
|---|---|
| SONGLE SLA-12VDC-SL-C on a YYG-2 module | **12 V coil**, 30 A contacts; module has its own driver + flyback diode |
| Coil supply | 12 V (from the buck converter) |
| Trigger | Module **IN** pin, driven from the RX control output |
| Contacts | COM/NO/NC wired into the motor / ODrive power path |

---

## Pin assignments

### Transmitter — Adafruit Feather M0 (printed on the board)

| Function | Pin |
|---|---|
| Radio chip-select (CS) | 8 |
| Radio reset (RST) | 4 |
| Radio interrupt (DIO0 / IRQ) | 3 |
| E-stop NC contact | 5 (other side to GND) |

### Receiver — RAK3172

| Function | Pin | Hardware |
|---|---|---|
| Relay / MOSFET control | PA0 | → Q1 gate → CN2 output |
| Link / pong LED | PA1 | LED1 (blue) |
| E-stop LED | PA12 | LED2 (red) |

### Protocol bytes

| Byte | Meaning | Direction |
|---|---|---|
| `0x01` | Heartbeat (safe / run) | TX → RX |
| `0x02` | E-stop (stop) | TX → RX |
| `0xAA` | Pong (link acknowledgment) | RX → TX |

---

## LoRa radio settings

**These must be identical on both ends or the radios will not talk.** They already
match in the firmware below.

| Parameter | Value | RAK (RUI3) | Feather (`LoRa` lib) |
|---|---|---|---|
| Frequency | 915 MHz | `pfreq.set(915000000)` | `LoRa.begin(915E6)` |
| Spreading factor | SF7 | `psf.set(7)` | `setSpreadingFactor(7)` |
| Bandwidth | 125 kHz | `pbw.set(125)` | `setSignalBandwidth(125E3)` |
| Coding rate | 4/5 | `pcr.set(0)` | `setCodingRate4(5)` |
| Preamble | 8 | `ppl.set(8)` | `setPreambleLength(8)` |
| Sync word | Private | default (`0x1424`) | `setSyncWord(0x12)` |
| CRC | On | default | `enableCrc()` |
| TX power | — | `ptp.set(14)` | `setTxPower(20)` |

Notes:

- **Sync word:** The RAK3172 uses an SX126x-class radio (private default `0x1424`); the
  Feather's RFM95 is an SX127x (private default `0x12`). These two values represent the
  **same** LoRa sync word and interoperate — this is expected, not a mismatch.
- **TX power does not need to match.** Each radio's transmit power is independent. The
  Feather is set to its maximum (20 dBm) for link margin.

### Serial / debug baud (independent of the radio)

The USB debug baud is only how each board prints text to a computer; it has nothing to
do with the radio link. The two can differ:

| Board | Serial baud |
|---|---|
| RAK3172 (RX) | 9600 |
| Feather M0 (TX) | 115200 |

---

## Wiring

### Transmitter

- **E-stop button:** use the **NC** (normally-closed) contact — *not* NO. NC is what
  makes it fail-safe: a pressed button **or** a broken/disconnected wire both open the
  circuit and read as "stop."
  - NC terminal → Feather **pin 5**
  - other NC terminal → Feather **GND**
  - (It's a switch contact, so there's no polarity.)
  - Verify the NC pair with a multimeter: continuity when **released**, open when
    pressed. NC is often marked `NC` or terminals `21–22`; NO is `13–14`.
- **Antenna:** ~78 mm wire soldered into the **Ant** pad. Never key the radio without an
  antenna.
- **Power:** USB or LiPo on the JST.

### Receiver board

- **Power input:** battery to the board's power input (through D1 → F1 → the 3.3 V
  regulator). Do **not** connect the battery to the output / CN2.
- **Relay (it's a module with an IN pin — do not switch the coil directly):**
  - Module coil supply (VCC / JD-VCC) → **12 V** (from the buck converter)
  - Module **GND** → common ground, shared with the RX board's GND
  - Module **IN** → the RX control output (from Q1 / CN2 — see Open Items for the
    active-high vs active-low jumper detail)
  - Relay **contacts (COM/NO/NC)** → in series with the motor / ODrive power path
- **Fail-safe contact choice:** route motor power through the contact that is **open
  when the coil is de-energized**, so a dead receiver (or pressed E-stop) cuts the
  motors. Confirm this on the bench.

---

## Software setup & flashing

### Feather M0 (transmitter) — Arduino IDE

1. **File → Preferences** → *Additional Boards Manager URLs*, add:
   ```
   https://adafruit.github.io/arduino-board-index/package_adafruit_index.json
   ```
2. **Tools → Board → Boards Manager** → search **Adafruit SAMD** → install
   *"Adafruit SAMD Boards."*
3. **Tools → Manage Libraries** → search **LoRa** → install *"LoRa"* by **Sandeep
   Mistry**.
4. **Tools → Board → Adafruit Feather M0**; select the COM port.
5. Paste the transmitter sketch and **Upload**.
   - If upload fails, **double-tap the RESET button** to force the bootloader (the LED
     pulses), then upload again.
6. Open the Serial Monitor at **115200**.

### RAK3172 (receiver) — Arduino IDE (RUI3)

1. Add the **RAKwireless RUI STM32** boards package (Boards Manager) per RAKwireless's
   guide.
2. Select the RAK3172 board and upload over UART. On this PCB (no on-board USB-UART),
   use an external USB-to-UART adapter on the RAK's UART2 pins, or program the module
   before installing it.
3. The firmware persists in the module's flash; you only need to reflash when changing
   the code.
4. Serial console runs at **9600**.

---

## Firmware

### Receiver — RAK3172 / RUI3 (serial 9600)

```cpp
// ESTOP RECEIVER (RAK3172 / RUI3) — fail-safe
// Boots STOPPED. Goes to RUN only while it keeps receiving 0x01 heartbeats.
// 0x02, or loss of the heartbeat for LINK_TIMEOUT_MS, forces STOP.
// MOSFET_PIN HIGH = relay energized = RUN.  LOW = relay de-energized = motors cut.
// Replies 0xAA after each packet so the transmitter can confirm the link.

#define MOSFET_PIN  PA0
#define LED_PONG    PA1      // blinks on every packet received
#define LED_ESTOP   PA12     // on when stopped

#define LINK_TIMEOUT_MS 750  // no heartbeat within this -> STOP

volatile bool got_packet = false;
volatile uint8_t rx_byte = 0;

unsigned long lastHeartbeat = 0;
bool stopped = true;         // start in the safe state

void recv_cb(rui_lora_p2p_recv_t data) {
    if (data.BufferSize >= 1) {
        rx_byte = data.Buffer[0];
        got_packet = true;
    }
}

void send_cb(void) {
    api.lora.precv(65534);   // pong sent, resume listening
}

void setStopped(bool s) {
    stopped = s;
    digitalWrite(MOSFET_PIN, s ? LOW : HIGH);
    digitalWrite(LED_ESTOP,  s ? HIGH : LOW);
}

void setup() {
    Serial.begin(9600);
    delay(2000);
    Serial.println("RX starting");

    pinMode(MOSFET_PIN, OUTPUT);
    pinMode(LED_PONG,   OUTPUT);
    pinMode(LED_ESTOP,  OUTPUT);
    digitalWrite(LED_PONG, LOW);
    setStopped(true);        // safe until a heartbeat arrives

    api.lora.nwm.set();
    api.lora.pfreq.set(915000000);
    api.lora.psf.set(7);
    api.lora.pbw.set(125);
    api.lora.pcr.set(0);
    api.lora.ppl.set(8);
    api.lora.ptp.set(14);

    api.lora.registerPRecvCallback(recv_cb);
    api.lora.registerPSendCallback(send_cb);
    api.lora.precv(65534);

    Serial.println("Listening");
    lastHeartbeat = millis();
}

void loop() {
    if (got_packet) {
        got_packet = false;

        if (rx_byte == 0x01) {           // heartbeat = link alive, run
            lastHeartbeat = millis();
            setStopped(false);
            Serial.println("RX: heartbeat -> RUN");
        } else if (rx_byte == 0x02) {    // commanded ESTOP
            lastHeartbeat = millis();
            setStopped(true);
            Serial.println("RX: ESTOP -> STOP");
        }

        // reply so the transmitter knows the link is good
        api.lora.precv(0);
        delay(10);
        uint8_t pong[1] = { 0xAA };
        api.lora.psend(1, pong);

        digitalWrite(LED_PONG, HIGH);
        delay(20);
        digitalWrite(LED_PONG, LOW);
    }

    // watchdog: lost the heartbeat -> fail safe to STOP
    if (!stopped && (millis() - lastHeartbeat > LINK_TIMEOUT_MS)) {
        setStopped(true);
        Serial.println("RX: LINK LOST -> STOP");
    }
}
```

### Transmitter — Adafruit Feather M0 RFM9x (serial 115200)

```cpp
// ESTOP TRANSMITTER (Adafruit Feather M0 RFM9x)
// Sends 0x01 heartbeat every 200 ms while safe; 0x02 continuously when the E-stop opens.
// E-stop NC contact wired between pin 5 and GND (opens when pressed or if a wire breaks).

#include <SPI.h>
#include <LoRa.h>

#define RFM95_CS    8
#define RFM95_RST   4
#define RFM95_INT   3        // DIO0
#define ESTOP_PIN   5        // E-stop NC contact -> this pin and GND

const unsigned long HEARTBEAT_MS = 200;
unsigned long lastBeat = 0;

void setup() {
  Serial.begin(115200);

  pinMode(ESTOP_PIN, INPUT_PULLUP);   // NC closed = LOW = run; open = HIGH = stop

  pinMode(RFM95_RST, OUTPUT);
  digitalWrite(RFM95_RST, HIGH); delay(10);
  digitalWrite(RFM95_RST, LOW);  delay(10);
  digitalWrite(RFM95_RST, HIGH); delay(10);

  LoRa.setPins(RFM95_CS, RFM95_RST, RFM95_INT);
  if (!LoRa.begin(915E6)) {
    Serial.println("LoRa init failed - check wiring");
    while (1);
  }

  // must match the RAK P2P settings
  LoRa.setSpreadingFactor(7);
  LoRa.setSignalBandwidth(125E3);
  LoRa.setCodingRate4(5);          // 4/5
  LoRa.setPreambleLength(8);
  LoRa.setTxPower(20);
  LoRa.setSyncWord(0x12);          // = RAK's default 0x1424
  LoRa.enableCrc();                // <-- if you get NO pong / RX never reacts, comment this out and re-upload

  Serial.println("TX ready");
}

void loop() {
  bool estop = (digitalRead(ESTOP_PIN) == HIGH);   // HIGH = pressed or wire broken

  static bool last = false;
  if (estop != last) { last = estop; Serial.println(estop ? "STOP" : "RUN"); }

  if (estop) {
    sendByte(0x02);
    delay(50);
  } else if (millis() - lastBeat >= HEARTBEAT_MS) {
    lastBeat = millis();
    sendByte(0x01);
  }

  if (LoRa.parsePacket()) {
    while (LoRa.available()) {
      if (LoRa.read() == 0xAA) Serial.println("pong");
    }
  }
}

void sendByte(uint8_t b) {
  LoRa.beginPacket();
  LoRa.write(b);
  LoRa.endPacket();        // blocks until sent
  LoRa.receive();          // listen for the pong
}
```

---

## Operating behavior (state logic)

| Condition | Transmitter sends | Receiver `PA0` | Relay | Motors |
|---|---|---|---|---|
| Power-on, before any heartbeat | — | LOW | de-energized | **stopped** |
| Button released, link good | `0x01` heartbeat | HIGH | energized | running |
| Button pressed | `0x02` continuously | LOW | de-energized | **stopped** |
| Button wire broken (NC opens) | `0x02` (reads as pressed) | LOW | de-energized | **stopped** |
| Radio link lost (>750 ms no heartbeat) | — | LOW | de-energized | **stopped** |
| Receiver loses power | — | LOW (gate pulled down) | de-energized | **stopped** |
| Button released again, link restored | `0x01` heartbeat | HIGH | energized | running |

> **Important:** The robot boots with motors **disabled**. The transmitter must be
> powered and within range (heartbeats arriving) before the drive relay will energize.
> This is intentional fail-safe behavior — don't mistake it for a fault.

---

## Commissioning & testing

Do these on the bench, with motors disconnected, before any drive test.

1. **Power the Feather**, open serial at 115200 → expect `TX ready`, then `RUN`
   (the `RUN/STOP` line prints on each state change). Press the button → `STOP`,
   release → `RUN`. This confirms the transmitter and button independently.
2. **Power the RAK** (serial 9600 if you have an adapter) → expect `RX starting`,
   `Listening`, then `RX: heartbeat -> RUN` repeating once the Feather is on.
3. **Confirm the link:** the Feather should print `pong` repeatedly, and the RX's
   LED1 (blue) should blink on each packet. If you see `RUN`/`STOP` but never `pong`,
   see Troubleshooting.
4. **Button test:** press the E-stop → RX prints `RX: ESTOP -> STOP`, PA0 goes LOW,
   relay drops. Release → returns to RUN.
5. **Fail-safe wire test:** with everything running, pull one of the button wires off →
   it must read as STOP. (Proves the NC fail-safe.)
6. **Link-loss test:** with everything running, power off the Feather → within ~0.75 s
   the RX prints `RX: LINK LOST -> STOP` and the relay drops.
7. **Range test:** with the final antennas and enclosure, verify reliable operation at
   your maximum operating distance **with margin to spare**. Treat datasheet ranges as
   optimistic.

---

## Troubleshooting

| Symptom | Likely cause / fix |
|---|---|
| Nothing on serial | Baud mismatch — RAK monitor = **9600**, Feather monitor = **115200**. Confirm the upload actually finished. The RX board has no USB serial unless you attach an external UART adapter. |
| Feather won't upload | Double-tap RESET to force the bootloader (LED pulses), then upload. |
| `RUN`/`STOP` on Feather but never `pong`, RX never reacts | The radios aren't linking. Confirm both are powered. Then on the Feather (easy to reflash) **comment out `LoRa.enableCrc();`** and re-upload — a CRC mismatch silently drops every packet. All other params already match. |
| RAK never prints / doesn't run firmware | BOOT0 must be low at boot: confirm R6 is populated and the H1 jumper is in the **run** position (not bridging BOOT0 to 3.3 V). |
| RAK powered but no 3.3 V | Confirm U2 (AP2112K) and its caps are populated; check 3.3 V is present and not shorted to GND; battery within the AP2112K's 6 V input limit. |
| Relay never switches | Confirm Q1 + R7 populated; relay module **IN** wired to the RX output; module VCC = 12 V; module GND common with the RX; check the H/L jumper polarity. |
| Relay chatters / false trips | Heartbeat being dropped — check antennas, range, and the 750 ms timeout vs the 200 ms heartbeat (3+ misses). Tune `LINK_TIMEOUT_MS` if needed. |
| `LoRa init failed` on the Feather | SPI/radio wiring — verify CS=8, RST=4, DIO0=3 (printed on the board). |

---

## Safety

- This is the vehicle's emergency cutoff. **Test the full fail-safe chain** (button,
  broken wire, link loss, power loss) before every drive session.
- The fail-safe relies on three things working together: the **NC** button wiring, the
  receiver's **heartbeat timeout**, and the **boot-stopped** default. Don't remove any
  of them.
- **MOSFET default state:** the gate must default OFF (off = motors stopped) when the
  receiver is unpowered. Confirm a gate-to-GND pull-down exists so an unpowered or
  resetting receiver fails to stop.
- **Antenna before power:** never transmit without the antenna attached — it can damage
  the radio's power amplifier.
- Use the relay contact that is **open when de-energized** for the motor power path, so
  loss of the coil drive cuts the motors.

---

## Open items / verify before competition

- [ ] Confirm what the RX board's **GATE** header pin connects to (PA0 logic vs Q1
      drain), and wire the relay module's **IN** accordingly. Set the module's **H/L**
      jumper to match (active-high vs active-low) so PA0 HIGH = relay energized = run.
- [ ] Confirm the relay **contact routing** (NO vs NC) gives motors-off when the coil
      is de-energized.
- [ ] Confirm a **gate pull-down** on Q1 (default-off when unpowered).
- [ ] Confirm the **buck converter** output feeding the relay module is 12 V.
- [ ] If the link won't establish, resolve the **CRC** setting (toggle on the Feather).
- [ ] Decide on a permanent **reflash path** for the RX (external UART header or SWD),
      since the on-board USB-UART is unpopulated.
- [ ] Final **range/interference test** with the competition antennas and enclosure.
