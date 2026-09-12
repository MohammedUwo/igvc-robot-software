#!/usr/bin/env python3
"""Configure an ODrive V3.6 for two Nanotec DB59L024035R-B motors.

This script writes only persistent .config parameters and idles both axes before
saving. It does not run calibration, enter closed-loop control, or command
motion. After save_configuration(), the ODrive normally reboots/disconnects.
"""

import argparse
import sys
import time

import odrive
from odrive.enums import (
    AXIS_STATE_IDLE,
    CONTROL_MODE_VELOCITY_CONTROL,
    INPUT_MODE_PASSTHROUGH,
    MOTOR_TYPE_PMSM_CURRENT_CONTROL,
)

# Nanotec DB59L024035R-B datasheet values.
POLE_PAIRS = 3                 # datasheet: 6 poles
TORQUE_CONSTANT_NM_PER_A = 0.05
RATED_CURRENT_A = 9.4
RATED_SPEED_TURN_PER_S = 3500.0 / 60.0

# Conservative calibration/settings choices for bringup.
CALIBRATION_CURRENT_A = 5.0    # below rated current; enough for 0.22 ohm phase resistance
RESISTANCE_CALIB_MAX_VOLTAGE = 4.0
REQUESTED_CURRENT_RANGE_A = 30.0  # above motor peak 28 A, below ODrive default 60 A range


def configure_axis(axis, name: str) -> None:
    axis.requested_state = AXIS_STATE_IDLE

    axis.motor.config.motor_type = MOTOR_TYPE_PMSM_CURRENT_CONTROL
    axis.motor.config.pole_pairs = POLE_PAIRS
    axis.motor.config.torque_constant = TORQUE_CONSTANT_NM_PER_A
    axis.motor.config.current_lim = RATED_CURRENT_A
    axis.motor.config.calibration_current = CALIBRATION_CURRENT_A
    axis.motor.config.resistance_calib_max_voltage = RESISTANCE_CALIB_MAX_VOLTAGE
    axis.motor.config.requested_current_range = REQUESTED_CURRENT_RANGE_A

    axis.controller.config.control_mode = CONTROL_MODE_VELOCITY_CONTROL
    axis.controller.config.input_mode = INPUT_MODE_PASSTHROUGH
    axis.controller.config.vel_limit = RATED_SPEED_TURN_PER_S

    # Never start motion/calibration automatically on boot. Bringup should remain explicit.
    axis.config.startup_motor_calibration = False
    axis.config.startup_encoder_offset_calibration = False
    axis.config.startup_closed_loop_control = False

    print(
        f"{name}: pole_pairs={POLE_PAIRS}, torque_constant={TORQUE_CONSTANT_NM_PER_A}, "
        f"current_lim={RATED_CURRENT_A}, calibration_current={CALIBRATION_CURRENT_A}, "
        f"vel_limit={RATED_SPEED_TURN_PER_S:.3f} turn/s"
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--serial", default="315B32623431", help="ODrive serial, uppercase hex without 0x")
    parser.add_argument("--timeout", type=float, default=10.0)
    args = parser.parse_args()

    print(f"Connecting to ODrive serial {args.serial}...")
    odrv = odrive.find_any(serial_number=args.serial, timeout=args.timeout)
    print(
        f"Connected: serial=0x{odrv.serial_number:x}, "
        f"fw={odrv.fw_version_major}.{odrv.fw_version_minor}.{odrv.fw_version_revision}, "
        f"vbus={odrv.vbus_voltage:.2f} V"
    )

    configure_axis(odrv.axis0, "axis0/M0")
    configure_axis(odrv.axis1, "axis1/M1")

    print("Saving configuration. ODrive will reboot/disconnect; a DeviceLostException here can be normal.")
    try:
        odrv.save_configuration()
    except Exception as exc:
        if exc.__class__.__name__ != "DeviceLostException":
            raise
        print("ODrive disconnected during save/reboot (expected).")

    time.sleep(3.0)
    print("Done. Reconnect or rerun verification after the ODrive re-enumerates.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
