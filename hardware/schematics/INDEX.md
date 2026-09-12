# Rutgers IGVC — EasyEDA exports, organized

Organized 2026-09-08 from `Downloads\FilesFromEasyEda`, using `igvcexportindex.md` as the
starting point. Originals in Downloads are untouched; everything here is a verified
byte-identical copy (all 66 files checked by MD5 against their source).

One folder per EasyEDA project. Schematic zips have been extracted, so every schematic
page is a plain `.svg` you can open directly. PCB layouts are the 6-page EasyEDA
fabrication PDFs (designator placement, BOM, assembly drawings, drill drawing).

## Naming

| Pattern | Means |
| --- | --- |
| `<Project> - <Document>.svg` | single-page schematic |
| `<Project> - <Document> - p<N> <Page>.svg` | one page of a multi-page schematic |
| `<Project> - <Document> (<Page>).svg` | single page with its own name |
| `<Project> - <Board> - PCB fab.pdf` | PCB layout, 6-page fab drawing |

## ⚠️ Correction to `igvcexportindex.md`

The index says *Power Distribution Board → PCB1 was not exported because the board is empty*.
The board **is** empty, but Chrome did save a file for it — a 6,107-byte PDF with no content,
downloaded first in the Power Distribution Board block as `PCB_PCB1_2026-09-08.pdf`.

Because of that extra file, **every `PCB_PCB1_… (n).pdf` in the index is off by one.**
The index's `(1)` is really `(2)`, its `(2)` is really `(3)`, and so on through `(14)` → `(15)`.
`PCB2`, `PCB2_1`, `PCB3`, `PCB7`, `PCB8`, `PCB13`–`PCB15` and `PCB1_1` all match the index exactly.

The corrected mapping was confirmed two ways: file modification times (each project's schematic
zip downloads immediately before that project's PCBs, an unbroken pattern across all 57 files),
and the component designator lists inside each PDF (e.g. IMU Handler PCB1 is described in the
index as a real thermostat + inertia board, and only `(1)` — not the base file — has components).

## Not copied here

Nothing was deleted; these simply weren't brought over. All still in `Downloads\FilesFromEasyEda`.

**Empty boards (16 PDFs, 6,107 bytes each, no copper or outline):** Power Distribution Board PCB1 ·
LED Controller PCB3 (×2) · E-Stop Receiver Board PCB2 · E-stop remote PCB15 · E-Stop Diagram PCB1 and PCB2 ·
Reusable Schematics PCB1 · rak_tx PCB1 · IGVC_first_project PCB1 and PCB2 · yo PCB1 ·
the_best_project PCB2 · i love chance PCB1 · chopper PCB1 · CANboardMaybe PCB1

**Duplicates (2):**

- `SVG_Power Distribution Board_2026-09-08 (1).zip` — identical to the first zip; differs only in
  randomly generated SVG element IDs.
- `SCH_rak_tx_1-rak_tx_2026-09-08.svg` (loose, not listed in the index) — same page as the copy
  inside `SVG_rak_tx_2026-09-08.zip`; identical text and path geometry, different element order.

**Also noted:** `LED Controller - PCB2` and `LED Controller - PCB2_1` extract to identical text and
are the same byte size — very likely the same board saved under two document names. Both kept,
since the source project treats them as separate documents.

## Projects with schematics only

No PCB layout survived export (their boards are empty): **E-Stop Diagram**, **Reusable Schematics**,
**rak_tx**, **chopper**, **CANboardMaybe**, **i love chance**, **yo**.

## Full file map

New name (inside its project folder) ← original filename in Downloads.

### Power Distribution Board

| File here | Came from |
| --- | --- |
| `Power Distribution Board - PCB2 - 4-layer 12V 5V 3V3 - PCB fab.pdf` | `PCB_PCB2_2026-09-08.pdf` |
| `Power Distribution Board - PCB2_1 - PCB fab.pdf` | `PCB_PCB2_1_2026-09-08.pdf` |
| `Power Distribution Board - PCB8 - PCB fab.pdf` | `PCB_PCB8_2026-09-08.pdf` |
| `Power Distribution Board - Inputs Outputs.svg` | `SVG_Power Distribution Board_2026-09-08.zip → Inputs Outputs/SCH_Inputs Outputs_1-P1_2026-09-08.svg` |
| `Power Distribution Board - Schematic1 (improved_final).svg` | `SVG_Power Distribution Board_2026-09-08.zip → Schematic1/SCH_Schematic1_1-improved_final_2026-09-08.svg` |
| `Power Distribution Board - Schematic1_1 (improved_final).svg` | `SVG_Power Distribution Board_2026-09-08.zip → Schematic1_1/SCH_Schematic1_1_1-improved_final_2026-09-08.svg` |
| `Power Distribution Board - Schematic2.svg` | `SVG_Power Distribution Board_2026-09-08.zip → Schematic2/SCH_Schematic2_1-P1_2026-09-08.svg` |
| `Power Distribution Board - Schematic3.svg` | `SVG_Power Distribution Board_2026-09-08.zip → Schematic3/SCH_Schematic3_1-P1_2026-09-08.svg` |
| `Power Distribution Board - buck converter.svg` | `SVG_Power Distribution Board_2026-09-08.zip → buck converter/SCH_buck converter_1-P1_2026-09-08.svg` |

### IMU Handler

| File here | Came from |
| --- | --- |
| `IMU Handler - PCB1 - thermostat + inertia Rev 1 - PCB fab.pdf` | `PCB_PCB1_2026-09-08 (1).pdf` |
| `IMU Handler - PCB2 - PCB fab.pdf` | `PCB_PCB2_2026-09-08 (1).pdf` |
| `IMU Handler - Backup.svg` | `SVG_IMU Handler_2026-09-08.zip → Backup/SCH_Backup_1-P1_2026-09-08.svg` |
| `IMU Handler - Main Board - p1 Main.svg` | `SVG_IMU Handler_2026-09-08.zip → Main Board/SCH_Main Board_1-Main_2026-09-08.svg` |
| `IMU Handler - Main Board - p2 Sensors.svg` | `SVG_IMU Handler_2026-09-08.zip → Main Board/SCH_Main Board_2-Sensors_2026-09-08.svg` |
| `IMU Handler - Main Board - p3 Power.svg` | `SVG_IMU Handler_2026-09-08.zip → Main Board/SCH_Main Board_3-Power_2026-09-08.svg` |
| `IMU Handler - Main Board - p4 Fans.svg` | `SVG_IMU Handler_2026-09-08.zip → Main Board/SCH_Main Board_4-Fans_2026-09-08.svg` |
| `IMU Handler - Main Board - p5 NTC Arrays.svg` | `SVG_IMU Handler_2026-09-08.zip → Main Board/SCH_Main Board_5-NTC Arrays_2026-09-08.svg` |
| `IMU Handler - R2 - p1 Main.svg` | `SVG_IMU Handler_2026-09-08.zip → R2/SCH_R2_1-Main_2026-09-08.svg` |
| `IMU Handler - R2 - p2 Sensors.svg` | `SVG_IMU Handler_2026-09-08.zip → R2/SCH_R2_2-Sensors_2026-09-08.svg` |
| `IMU Handler - R2 - p3 Power.svg` | `SVG_IMU Handler_2026-09-08.zip → R2/SCH_R2_3-Power_2026-09-08.svg` |
| `IMU Handler - R2 - p4 Fans.svg` | `SVG_IMU Handler_2026-09-08.zip → R2/SCH_R2_4-Fans_2026-09-08.svg` |

### LED Controller

| File here | Came from |
| --- | --- |
| `LED Controller - PCB1 - PCB fab.pdf` | `PCB_PCB1_2026-09-08 (2).pdf` |
| `LED Controller - PCB2 - PCB fab.pdf` | `PCB_PCB2_2026-09-08 (2).pdf` |
| `LED Controller - PCB2_1 - PCB fab.pdf` | `PCB_PCB2_1_2026-09-08 (1).pdf` |
| `LED Controller - PCB8 - LED1-LED5 300mA - PCB fab.pdf` | `PCB_PCB8_2026-09-08 (1).pdf` |
| `LED Controller - Schematic1.svg` | `SVG_LED Controller_2026-09-08.zip → Schematic1/SCH_Schematic1_1-P1_2026-09-08.svg` |
| `LED Controller - Schematic2 - p1.svg` | `SVG_LED Controller_2026-09-08.zip → Schematic2/SCH_Schematic2_1-P1_2026-09-08.svg` |
| `LED Controller - Schematic2 - p2.svg` | `SVG_LED Controller_2026-09-08.zip → Schematic2/SCH_Schematic2_2-P2_2026-09-08.svg` |
| `LED Controller - Schematic3.svg` | `SVG_LED Controller_2026-09-08.zip → Schematic3/SCH_Schematic3_1-P1_2026-09-08.svg` |

### E-Stop Receiver Board

| File here | Came from |
| --- | --- |
| `E-Stop Receiver Board - igvc_2324 - PCB fab.pdf` | `PCB_1-PCB_PCB_igvc_2324_2026-09-08.pdf` |
| `E-Stop Receiver Board - Schematic1.svg` | `SVG_E-Stop Receiver Board_2026-09-08.zip → Schematic1/SCH_Schematic1_1-P1_2026-09-08.svg` |
| `E-Stop Receiver Board - igvc_2324 (Combined Schematic).svg` | `SVG_E-Stop Receiver Board_2026-09-08.zip → igvc_2324/SCH_igvc_2324_1-Combined Schematic_2026-09-08.svg` |

### E-stop remote

| File here | Came from |
| --- | --- |
| `E-stop remote - PCB13 - PCB fab.pdf` | `PCB_PCB13_2026-09-08.pdf` |
| `E-stop remote - PCB14 - BreakoutBoardRAK3172 - PCB fab.pdf` | `PCB_PCB14_2026-09-08.pdf` |
| `E-stop remote - PCB7 - PCB fab.pdf` | `PCB_PCB7_2026-09-08.pdf` |
| `E-stop remote - Schematic1.svg` | `SVG_E-stop remote_2026-09-08.zip → Schematic1/SCH_Schematic1_1-P1_2026-09-08.svg` |
| `E-stop remote - Schematic2.svg` | `SVG_E-stop remote_2026-09-08.zip → Schematic2/SCH_Schematic2_1-P1_2026-09-08.svg` |
| `E-stop remote - Schematic3.svg` | `SVG_E-stop remote_2026-09-08.zip → Schematic3/SCH_Schematic3_1-P1_2026-09-08.svg` |
| `E-stop remote - Schematic4.svg` | `SVG_E-stop remote_2026-09-08.zip → Schematic4/SCH_Schematic4_1-P1_2026-09-08.svg` |
| `E-stop remote - Schematic5.svg` | `SVG_E-stop remote_2026-09-08.zip → Schematic5/SCH_Schematic5_1-P1_2026-09-08.svg` |
| `E-stop remote - Schematic6.svg` | `SVG_E-stop remote_2026-09-08.zip → Schematic6/SCH_Schematic6_1-P1_2026-09-08.svg` |

### E-Stop Diagram

| File here | Came from |
| --- | --- |
| `E-Stop Diagram - Schematic1.svg` | `SVG_E-Stop Diagram_2026-09-08.zip → Schematic1/SCH_Schematic1_1-P1_2026-09-08.svg` |
| `E-Stop Diagram - Schematic2.svg` | `SVG_E-Stop Diagram_2026-09-08.zip → Schematic2/SCH_Schematic2_1-P1_2026-09-08.svg` |

### Nikita's testing ESTOP

| File here | Came from |
| --- | --- |
| `Nikita's testing ESTOP - PCB1 - RX board - PCB fab.pdf` | `PCB_PCB1_2026-09-08 (4).pdf` |
| `Nikita's testing ESTOP - PCB2 - TX board - PCB fab.pdf` | `PCB_PCB2_2026-09-08 (5).pdf` |
| `Nikita's testing ESTOP - Schematic1.svg` | `SVG_Nikita's testing ESTOP_2026-09-08.zip → Schematic1/SCH_Schematic1_1-P1_2026-09-08.svg` |
| `Nikita's testing ESTOP - Schematic2 (Main).svg` | `SVG_Nikita's testing ESTOP_2026-09-08.zip → Schematic2/SCH_Schematic2_1-Main_2026-09-08.svg` |

### Reusable Schematics

| File here | Came from |
| --- | --- |
| `Reusable Schematics - Schematic1.svg` | `SVG_Reusable Schematics_2026-09-08.zip → Schematic1/SCH_Schematic1_1-P1_2026-09-08.svg` |

### rak_tx

| File here | Came from |
| --- | --- |
| `rak_tx - rak_tx.svg` | `SVG_rak_tx_2026-09-08.zip → rak_tx/SCH_rak_tx_1-rak_tx_2026-09-08.svg` |

### IGVC_first_project

| File here | Came from |
| --- | --- |
| `IGVC_first_project - PCB1_1 - RX - PCB fab.pdf` | `PCB_PCB1_1_2026-09-08.pdf` |
| `IGVC_first_project - Schematic1.svg` | `SVG_IGVC_first_project_2026-09-08.zip → Schematic1/SCH_Schematic1_1-P1_2026-09-08.svg` |
| `IGVC_first_project - Schematic1_1.svg` | `SVG_IGVC_first_project_2026-09-08.zip → Schematic1_1/SCH_Schematic1_1_1-P1_2026-09-08.svg` |
| `IGVC_first_project - Schematic2.svg` | `SVG_IGVC_first_project_2026-09-08.zip → Schematic2/SCH_Schematic2_1-P1_2026-09-08.svg` |

### the_best_project

| File here | Came from |
| --- | --- |
| `the_best_project - PCB1 - PCB fab.pdf` | `PCB_PCB1_2026-09-08 (9).pdf` |
| `the_best_project - Schematic1.svg` | `SVG_the_best_project_2026-09-08.zip → Schematic1/SCH_Schematic1_1-P1_2026-09-08.svg` |
| `the_best_project - Schematic2.svg` | `SVG_the_best_project_2026-09-08.zip → Schematic2/SCH_Schematic2_1-P1_2026-09-08.svg` |

### testBoard

| File here | Came from |
| --- | --- |
| `testBoard - PCB1 - PCB fab.pdf` | `PCB_PCB1_2026-09-08 (11).pdf` |
| `testBoard - Schematic1.svg` | `SVG_testBoard_2026-09-08.zip → Schematic1/SCH_Schematic1_1-P1_2026-09-08.svg` |

### igcv pcbruh

| File here | Came from |
| --- | --- |
| `igcv pcbruh - PCB1 - PCB fab.pdf` | `PCB_PCB1_2026-09-08 (12).pdf` |
| `igcv pcbruh - Schematic1.svg` | `SVG_igcv pcbruh_2026-09-08.zip → Schematic1/SCH_Schematic1_1-P1_2026-09-08.svg` |

### chanceboard

| File here | Came from |
| --- | --- |
| `chanceboard - PCB1 - PCB fab.pdf` | `PCB_PCB1_2026-09-08 (13).pdf` |
| `chanceboard - Schematic1.svg` | `SVG_chanceboard_2026-09-08.zip → Schematic1/SCH_Schematic1_1-P1_2026-09-08.svg` |

### chopper

| File here | Came from |
| --- | --- |
| `chopper - Schematic1.svg` | `SVG_chopper_2026-09-08.zip → Schematic1/SCH_Schematic1_1-P1_2026-09-08.svg` |

### CANboardMaybe

| File here | Came from |
| --- | --- |
| `CANboardMaybe - Schematic1.svg` | `SVG_CANboardMaybe_2026-09-08.zip → Schematic1/SCH_Schematic1_1-P1_2026-09-08.svg` |

### i love chance

| File here | Came from |
| --- | --- |
| `i love chance - Schematic1.svg` | `SVG_i love chance_2026-09-08.zip → Schematic1/SCH_Schematic1_1-P1_2026-09-08.svg` |

### yo

| File here | Came from |
| --- | --- |
| `yo - Schematic1.svg` | `SVG_yo_2026-09-08.zip → Schematic1/SCH_Schematic1_1-P1_2026-09-08.svg` |

