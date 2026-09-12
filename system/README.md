# NUC system reference

Captured from `igvc-NUC12DCMi9` on 3 September 2026, ahead of a planned rebuild that has not
happened yet. The machine is still running this configuration.

## udev rules

Copy to `/etc/udev/rules.d/`, then `sudo udevadm control --reload-rules && sudo udevadm trigger`.

| File | Device | ID |
|---|---|---|
| `rplidar.rules` | RPLIDAR A1 | `10c4:ea60` → symlink `/dev/rplidar` |
| `91-odrive.rules` | ODrive | `1209:0d3x`, DFU `0483:df11` |
| `80-movidius.rules` | OAK-D / Myriad X | `03e7` |
| `60-reach-devices.rules` | Emlid Reach | vendor `3032` |
| `60-reach-edison.rules` | Emlid Reach (Edison) | `8087:0a99` |

## manifest/

- `partition-table.sfdisk`, `fstab-p3.txt`, `fstab-p5.txt`, `lsblk.txt`, `blkid.txt` — disk layout.
  The NUC held **two** Ubuntu installs: p3 (`/`, user `igvc`, ROS 2 Humble) and
  p5 (`/mnt/p5`, user `rieee`, ROS 1 Noetic).
- `apt-manual-p3.txt` — packages explicitly installed; the shortest path to rebuilding the environment.
- `dpkg-selections-p3.txt` / `-p5.txt` — complete package lists.
- `pip-freeze-igvc.txt` — Python environment.
- `lspci.txt`, `lsusb.txt`, `dmidecode.txt`, `snap-list.txt`, `systemd-enabled-p3.txt` — hardware and services.

Full disk images (162 archives, 102 GiB) live in the team Google Drive under `nuc-backup/tar/`.
