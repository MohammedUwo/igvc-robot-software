from dataclasses import dataclass
import re
from typing import Optional


@dataclass(frozen=True)
class CurrentCalibration:
    zero_offset_v: float = 0.5
    sensitivity_v_per_a: float = 0.04
    current_sign: float = 1.0


@dataclass(frozen=True)
class EstopCurrentReading:
    adc_raw: Optional[int] = None
    sensor_voltage_v: Optional[float] = None
    current_a: Optional[float] = None
    estop_active: Optional[bool] = None
    relay_enabled: Optional[bool] = None
    monotonic_ms: Optional[int] = None


def convert_current(sensor_voltage_v: float, calibration: CurrentCalibration) -> float:
    return calibration.current_sign * (sensor_voltage_v - calibration.zero_offset_v) / calibration.sensitivity_v_per_a


def _parse_bool(value: str) -> Optional[bool]:
    value = value.strip().lower()
    if value in {'1', 'true', 'yes', 'active', 'on'}:
        return True
    if value in {'0', 'false', 'no', 'inactive', 'off'}:
        return False
    return None


def _parse_structured(line: str) -> Optional[EstopCurrentReading]:
    text = line.strip()
    if not text.startswith('IGVC_ESTOP,'):
        return None
    fields = {}
    for part in text.split(',')[1:]:
        if '=' in part:
            key, value = part.split('=', 1)
            fields[key.strip().lower()] = value.strip()
    def get_int(name):
        return int(fields[name]) if name in fields and fields[name] else None
    def get_float(name):
        return float(fields[name]) if name in fields and fields[name] else None
    return EstopCurrentReading(
        adc_raw=get_int('adc'),
        sensor_voltage_v=get_float('voltage'),
        current_a=get_float('current'),
        estop_active=_parse_bool(fields['estop']) if 'estop' in fields else None,
        relay_enabled=_parse_bool(fields['relay']) if 'relay' in fields else None,
        monotonic_ms=get_int('ms'),
    )


_LEGACY_ANALOG_RE = re.compile(r'Analog\s+3:\s*(-?\d+)\s+(-?\d+(?:\.\d+)?)')
_ESTOP_RE = re.compile(r'estop\s*[:=]\s*(true|false|0|1|active|inactive|on|off)', re.IGNORECASE)


def parse_legacy_line(line: str, calibration: Optional[CurrentCalibration] = None) -> Optional[EstopCurrentReading]:
    structured = _parse_structured(line)
    if structured is not None:
        return structured

    analog = _LEGACY_ANALOG_RE.search(line)
    estop = _ESTOP_RE.search(line)
    if analog is None and estop is None:
        return None

    adc_raw = int(analog.group(1)) if analog else None
    voltage = float(analog.group(2)) if analog else None
    current = convert_current(voltage, calibration) if voltage is not None and calibration is not None else None
    return EstopCurrentReading(
        adc_raw=adc_raw,
        sensor_voltage_v=voltage,
        current_a=current,
        estop_active=_parse_bool(estop.group(1)) if estop else None,
    )
