# NUC backup index

Full-fidelity `tar + zstd` archives of `igvc-NUC12DCMi9`, taken 3 September 2026 before the
machine was rebuilt. They live in the team Google Drive at `nuc-backup/tar/`.

**162 archives, 102.4 GiB total.** Both completion markers (`p3.ALLDONE`, `p5.ALLDONE`) were present,
so the set is complete.

| Partition | Archives | Size | Contents |
|---|---:|---:|---|
| p3 | 83 | 19.1 GiB | The live system — user `igvc`, Ubuntu 22.04.5, ROS 2 Humble |
| p5 | 77 | 83.3 GiB | Older install — user `rieee`, ROS 1 Noetic. Mostly non-IGVC bulk. |
| other | 2 | 14.2 MiB | EFI partition and the system manifest |

## Restoring one archive

```bash
rclone cat gdrive:nuc-backup/tar/<name>.tar.zst | zstd -d | tar -xv -C <dest>
```

Archives preserve permissions, ownership, symlinks and sparse files. An earlier plain
`rclone copy` of the same data did not — it silently skipped 56,530 symlinks, including
`/bin` and `/lib32`. Use these, not the `nuc-backup/p3/` file tree beside them.

## Notable archives

| Archive | Size | What it holds |
|---|---:|---|
| `p3-home-igvc_-gz_ws_.tar.zst` | 84.6 MiB | The autonomy stack. `ros2_ws/src/diff_drive_robot` is recovered into this repo. |
| `p3-home-igvc_-Downloads_.tar.zst` | 3.9 GiB | `IGVC-AUTONAV-2026/` and `GETSENSORS/` incl. an `igvc_hardware_bringup` package. Not yet examined. |
| `p3-home-igvc_-igvc_ws_.tar.zst` | 1.0 GiB | `lane_following` — a stub. Stock ROS 2 demo launch files plus one stray WhiteFilter node. |
| `p3-home-igvc_-dai_ws_.tar.zst` | 291.1 MiB | Upstream depthai-ros build. No custom work; reinstallable. |
| `p3-etc.tar.zst` | 1.5 MiB | System config incl. the udev rules copied into `system/udev/`. |
| `manifest.tar.zst` | 51.2 KiB | Partition table, fstabs, package lists, hardware inventory. Extracted into `system/manifest/`. |
| `p5-home-rieee_-IGVC21-22_.tar.zst` | 2.1 MiB | The 2021-22 robot's repo, incl. the safety-light code in `legacy/pathfinder-led/`. |
| `p5-home-rieee_-rutgers_igvc_electrical_.tar.zst` | 4.0 MiB | Clone of ozatyx/rutgers_igvc_electrical. Clean and already pushed upstream. |
| `p5-home-rieee_-vex_.tar.zst` | 54.9 GiB | 54.9 GiB of VEX material. Not IGVC. |

## Full listing

| Archive | Size |
|---|---:|
| `efi-system-partition.tar.zst` | 14.2 MiB |
| `manifest.tar.zst` | 51.2 KiB |
| `p3-boot.tar.zst` | 277.3 MiB |
| `p3-docker-images-save.tar.zst` | 514.2 MiB |
| `p3-etc.tar.zst` | 1.5 MiB |
| `p3-home-buildfarm_-Documents_.tar.zst` | 647 B |
| `p3-home-igvc_-.944123051220.20251006_171310.bin_.tar.zst` | 311.8 KiB |
| `p3-home-igvc_-.99-realsense-libusb.rules_.tar.zst` | 1.1 KiB |
| `p3-home-igvc_-.HelpWire_.tar.zst` | 20.9 MiB |
| `p3-home-igvc_-.InstallerGUI.lock_.tar.zst` | 96 B |
| `p3-home-igvc_-.Xilinx_.tar.zst` | 2.8 KiB |
| `p3-home-igvc_-.bash_history_.tar.zst` | 8.3 KiB |
| `p3-home-igvc_-.bash_logout_.tar.zst` | 230 B |
| `p3-home-igvc_-.bashrc_.tar.zst` | 1.9 KiB |
| `p3-home-igvc_-.camoufox_.tar.zst` | 87 B |
| `p3-home-igvc_-.cloudflared_.tar.zst` | 505 B |
| `p3-home-igvc_-.config_.tar.zst` | 542.9 MiB |
| `p3-home-igvc_-.copilot_.tar.zst` | 642 B |
| `p3-home-igvc_-.dotnet_.tar.zst` | 105.9 KiB |
| `p3-home-igvc_-.gazebo_.tar.zst` | 18.9 KiB |
| `p3-home-igvc_-.gnome_.tar.zst` | 330 B |
| `p3-home-igvc_-.gnupg_.tar.zst` | 184 B |
| `p3-home-igvc_-.gphoto_.tar.zst` | 83 B |
| `p3-home-igvc_-.hermes_.tar.zst` | 1.4 GiB |
| `p3-home-igvc_-.ignition_.tar.zst` | 26.3 MiB |
| `p3-home-igvc_-.ipython_.tar.zst` | 14.6 KiB |
| `p3-home-igvc_-.java_.tar.zst` | 4.9 KiB |
| `p3-home-igvc_-.joinnow_.tar.zst` | 1.6 KiB |
| `p3-home-igvc_-.local_.tar.zst` | 4.6 GiB |
| `p3-home-igvc_-.mozilla_.tar.zst` | 101 B |
| `p3-home-igvc_-.npm_.tar.zst` | 159.7 MiB |
| `p3-home-igvc_-.nv_.tar.zst` | 5.9 KiB |
| `p3-home-igvc_-.pki_.tar.zst` | 1.5 KiB |
| `p3-home-igvc_-.platformio_.tar.zst` | 279.5 MiB |
| `p3-home-igvc_-.profile_.tar.zst` | 493 B |
| `p3-home-igvc_-.python_history-04855.tmp_.tar.zst` | 92 B |
| `p3-home-igvc_-.python_history_.tar.zst` | 1.7 KiB |
| `p3-home-igvc_-.realsense-config.json_.tar.zst` | 963 B |
| `p3-home-igvc_-.ros_.tar.zst` | 9.3 MiB |
| `p3-home-igvc_-.rtabmap_.tar.zst` | 87 B |
| `p3-home-igvc_-.rviz2_.tar.zst` | 2.3 KiB |
| `p3-home-igvc_-.sdformat_.tar.zst` | 328 B |
| `p3-home-igvc_-.ssh_.tar.zst` | 206 B |
| `p3-home-igvc_-.sudo_as_admin_successful_.tar.zst` | 92 B |
| `p3-home-igvc_-.thunderbird_.tar.zst` | 229.4 KiB |
| `p3-home-igvc_-.vscode-shared_.tar.zst` | 2.8 KiB |
| `p3-home-igvc_-.vscode_.tar.zst` | 174.3 MiB |
| `p3-home-igvc_-.wget-hsts_.tar.zst` | 224 B |
| `p3-home-igvc_-.xsession_.tar.zst` | 95 B |
| `p3-home-igvc_-6.8.0-85-generic-uvc.ko_.tar.zst` | 51.7 KiB |
| `p3-home-igvc_-6.8.0-85-generic-uvcvideo.ko_.tar.zst` | 1.0 MiB |
| `p3-home-igvc_-6.8.0-85-generic-videodev.ko_.tar.zst` | 1.4 MiB |
| `p3-home-igvc_-Desktop_.tar.zst` | 679 B |
| `p3-home-igvc_-Documents_.tar.zst` | 497.7 MiB |
| `p3-home-igvc_-Downloads_.tar.zst` | 3.9 GiB |
| `p3-home-igvc_-Music_.tar.zst` | 84 B |
| `p3-home-igvc_-Pictures_.tar.zst` | 1.0 MiB |
| `p3-home-igvc_-Public_.tar.zst` | 85 B |
| `p3-home-igvc_-Templates_.tar.zst` | 88 B |
| `p3-home-igvc_-Videos_.tar.zst` | 85 B |
| `p3-home-igvc_-build_.tar.zst` | 26.1 KiB |
| `p3-home-igvc_-dai_ws_.tar.zst` | 291.1 MiB |
| `p3-home-igvc_-depth_.tar.zst` | 45.6 KiB |
| `p3-home-igvc_-depthai-python_.tar.zst` | 66.4 MiB |
| `p3-home-igvc_-external_.tar.zst` | 32.9 MiB |
| `p3-home-igvc_-frames_2025-11-17_12.26.02.gv_.tar.zst` | 130 B |
| `p3-home-igvc_-frames_2025-11-17_12.26.02.pdf_.tar.zst` | 5.0 KiB |
| `p3-home-igvc_-gz_ws_.tar.zst` | 84.6 MiB |
| `p3-home-igvc_-igvc_ws_.tar.zst` | 1.0 GiB |
| `p3-home-igvc_-install_.tar.zst` | 8.5 KiB |
| `p3-home-igvc_-log_.tar.zst` | 622.8 KiB |
| `p3-home-igvc_-monkey_.tar.zst` | 225.6 MiB |
| `p3-home-igvc_-oakd_cli_captures_.tar.zst` | 196.5 KiB |
| `p3-home-igvc_-ros2_humble_.tar.zst` | 604.2 MiB |
| `p3-home-igvc_-ros2_ws_.tar.zst` | 636.6 MiB |
| `p3-home-igvc_-ros_knowledge_.tar.zst` | 8.2 KiB |
| `p3-home-igvc_-snap_.tar.zst` | 705.5 MiB |
| `p3-home-igvc_-tutorial_.tar.zst` | 848.6 MiB |
| `p3-opt.tar.zst` | 714.9 MiB |
| `p3-root.tar.zst` | 141.1 KiB |
| `p3-srv.tar.zst` | 78 B |
| `p3-usr-local.tar.zst` | 187.4 MiB |
| `p3-var-lib-containerd.tar.zst` | 1010.2 MiB |
| `p3-var-lib-docker.tar.zst` | 1.2 MiB |
| `p3-var.tar.zst` | 411.1 MiB |
| `p5-boot.tar.zst` | 133.4 MiB |
| `p5-etc.tar.zst` | 1.3 MiB |
| `p5-home-rieee_-.944123051220.20240531_153510.bin_.tar.zst` | 452.4 KiB |
| `p5-home-rieee_-.944123051220.20250525_201520.bin_.tar.zst` | 445.1 KiB |
| `p5-home-rieee_-.99-realsense-libusb.rules_.tar.zst` | 1.1 KiB |
| `p5-home-rieee_-.Xauthority_.tar.zst` | 146 B |
| `p5-home-rieee_-.anydesk_.tar.zst` | 80.0 KiB |
| `p5-home-rieee_-.bash_history_.tar.zst` | 9.0 KiB |
| `p5-home-rieee_-.bash_logout_.tar.zst` | 231 B |
| `p5-home-rieee_-.bashrc_.tar.zst` | 2.1 KiB |
| `p5-home-rieee_-.conda_.tar.zst` | 157 B |
| `p5-home-rieee_-.config_.tar.zst` | 728.8 MiB |
| `p5-home-rieee_-.dbus_.tar.zst` | 437 B |
| `p5-home-rieee_-.dotnet_.tar.zst` | 82.4 KiB |
| `p5-home-rieee_-.gazebo_.tar.zst` | 4.1 MiB |
| `p5-home-rieee_-.gitconfig_.tar.zst` | 193 B |
| `p5-home-rieee_-.gnupg_.tar.zst` | 275 B |
| `p5-home-rieee_-.gphoto_.tar.zst` | 86 B |
| `p5-home-rieee_-.ignition_.tar.zst` | 396 B |
| `p5-home-rieee_-.ipython_.tar.zst` | 6.9 KiB |
| `p5-home-rieee_-.keras_.tar.zst` | 199 B |
| `p5-home-rieee_-.local_.tar.zst` | 1.5 GiB |
| `p5-home-rieee_-.mozilla_.tar.zst` | 46.8 MiB |
| `p5-home-rieee_-.nv_.tar.zst` | 288.4 KiB |
| `p5-home-rieee_-.nx_.tar.zst` | 2.7 MiB |
| `p5-home-rieee_-.pki_.tar.zst` | 1.4 KiB |
| `p5-home-rieee_-.profile_.tar.zst` | 494 B |
| `p5-home-rieee_-.python_history_.tar.zst` | 860 B |
| `p5-home-rieee_-.pyvim_.tar.zst` | 174 B |
| `p5-home-rieee_-.qt_.tar.zst` | 130 B |
| `p5-home-rieee_-.realsense-config.json_.tar.zst` | 902 B |
| `p5-home-rieee_-.ros_.tar.zst` | 2.0 MiB |
| `p5-home-rieee_-.rviz_.tar.zst` | 303 B |
| `p5-home-rieee_-.sdformat_.tar.zst` | 311 B |
| `p5-home-rieee_-.ssh_.tar.zst` | 1.0 KiB |
| `p5-home-rieee_-.sudo_as_admin_successful_.tar.zst` | 94 B |
| `p5-home-rieee_-.vcpkg_.tar.zst` | 287 B |
| `p5-home-rieee_-.vscode-server_.tar.zst` | 59.8 MiB |
| `p5-home-rieee_-.vscode_.tar.zst` | 172.9 MiB |
| `p5-home-rieee_-.wget-hsts_.tar.zst` | 568 B |
| `p5-home-rieee_-99-realsense-libusb.rules_.tar.zst` | 1.1 KiB |
| `p5-home-rieee_-Desktop_.tar.zst` | 520.5 KiB |
| `p5-home-rieee_-Documents_.tar.zst` | 8.5 MiB |
| `p5-home-rieee_-Downloads_.tar.zst` | 17.0 GiB |
| `p5-home-rieee_-IGVC21-22_.tar.zst` | 2.1 MiB |
| `p5-home-rieee_-Luxonis_.tar.zst` | 313.8 MiB |
| `p5-home-rieee_-Music_.tar.zst` | 84 B |
| `p5-home-rieee_-NVISII_.tar.zst` | 364.5 MiB |
| `p5-home-rieee_-Pictures_.tar.zst` | 4.5 MiB |
| `p5-home-rieee_-Public_.tar.zst` | 85 B |
| `p5-home-rieee_-Templates_.tar.zst` | 88 B |
| `p5-home-rieee_-Videos_.tar.zst` | 104 B |
| `p5-home-rieee_-anaconda3_.tar.zst` | 4.1 GiB |
| `p5-home-rieee_-build_.tar.zst` | 41.3 KiB |
| `p5-home-rieee_-catkin_ws_.tar.zst` | 180.6 MiB |
| `p5-home-rieee_-comp_.tar.zst` | 2.4 KiB |
| `p5-home-rieee_-cython-hidapi_.tar.zst` | 7.1 MiB |
| `p5-home-rieee_-devel_.tar.zst` | 5.9 KiB |
| `p5-home-rieee_-install_ros.sh_.tar.zst` | 531 B |
| `p5-home-rieee_-intel_.tar.zst` | 192 B |
| `p5-home-rieee_-ka123_.tar.zst` | 7.5 KiB |
| `p5-home-rieee_-librealsense_.tar.zst` | 475.8 MiB |
| `p5-home-rieee_-reach_ros_node_.tar.zst` | 55.8 KiB |
| `p5-home-rieee_-realsenseview.py_.tar.zst` | 477 B |
| `p5-home-rieee_-requirements.txt_.tar.zst` | 570 B |
| `p5-home-rieee_-rutgers_igvc_electrical_.tar.zst` | 4.0 MiB |
| `p5-home-rieee_-rutgers_igvc_electrical_old_.tar.zst` | 3.2 MiB |
| `p5-home-rieee_-snap_.tar.zst` | 66.4 MiB |
| `p5-home-rieee_-src_.tar.zst` | 145 B |
| `p5-home-rieee_-vcpkg_.tar.zst` | 610.4 MiB |
| `p5-home-rieee_-vex_.tar.zst` | 54.9 GiB |
| `p5-opt.tar.zst` | 606.1 MiB |
| `p5-root.tar.zst` | 20.5 KiB |
| `p5-srv.tar.zst` | 78 B |
| `p5-usr-local.tar.zst` | 13.8 MiB |
| `p5-var-lib-docker.tar.zst` | 1.8 GiB |
| `p5-var.tar.zst` | 326.9 MiB |

## Excluded on purpose

`.bash_history` and `.ssh` from both users are in the Drive archives but are **not** in this
repo. The history contained a live Cloudflare tunnel token and a plaintext password typed at
a `sudo` prompt. Treat those two archives as secret-bearing.
