import math

import pytest

from igvc_estop_current.parser import parse_legacy_line, CurrentCalibration, convert_current


def test_parse_legacy_analog_line_extracts_raw_and_voltage():
    sample = "Changed pin state\tAnalog 3: 12345\t0.771\r\n"

    reading = parse_legacy_line(sample)

    assert reading.adc_raw == 12345
    assert reading.sensor_voltage_v == pytest.approx(0.771)
    assert reading.estop_active is None


def test_parse_structured_csv_line_extracts_estop_relay_adc_voltage_and_current():
    sample = "IGVC_ESTOP,ms=1200,estop=1,relay=0,adc=8500,voltage=0.531,current=-1.25"

    reading = parse_legacy_line(sample)

    assert reading.monotonic_ms == 1200
    assert reading.estop_active is True
    assert reading.relay_enabled is False
    assert reading.adc_raw == 8500
    assert reading.sensor_voltage_v == pytest.approx(0.531)
    assert reading.current_a == pytest.approx(-1.25)


def test_convert_current_uses_zero_offset_sensitivity_and_sign():
    calibration = CurrentCalibration(zero_offset_v=0.5, sensitivity_v_per_a=0.04, current_sign=-1.0)

    current = convert_current(sensor_voltage_v=0.62, calibration=calibration)

    assert current == pytest.approx(-3.0)


def test_unrecognized_line_returns_none():
    assert parse_legacy_line("Recieving. This ESP32's MAC adress is: 00:11:22") is None
