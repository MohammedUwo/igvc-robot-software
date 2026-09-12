import time
from typing import Optional

import rclpy
from rclpy.node import Node
from std_msgs.msg import Bool, Float32, Int32
from diagnostic_msgs.msg import DiagnosticArray, DiagnosticStatus, KeyValue

from .parser import CurrentCalibration, parse_legacy_line

try:
    import serial
except Exception:  # pragma: no cover - exercised on robots missing pyserial
    serial = None


class EstopCurrentNode(Node):
    def __init__(self):
        super().__init__('estop_current_node')
        self.declare_parameter('port', '/dev/igvc_estop')
        self.declare_parameter('baud', 115200)
        self.declare_parameter('publish_rate_hz', 4.0)
        self.declare_parameter('stale_timeout_s', 1.5)
        self.declare_parameter('zero_offset_v', 0.5)
        self.declare_parameter('sensitivity_v_per_a', 0.04)
        self.declare_parameter('current_sign', 1.0)
        self.declare_parameter('nominal_bus_voltage_v', 24.0)

        self.estop_pub = self.create_publisher(Bool, '/safety/estop', 10)
        self.relay_pub = self.create_publisher(Bool, '/safety/relay_enabled', 10)
        self.raw_pub = self.create_publisher(Int32, '/power/odrive/current_raw_adc', 10)
        self.voltage_pub = self.create_publisher(Float32, '/power/odrive/current_sensor_voltage', 10)
        self.current_pub = self.create_publisher(Float32, '/power/odrive/current', 10)
        self.bus_pub = self.create_publisher(Float32, '/power/odrive/bus_voltage_nominal', 10)
        self.power_pub = self.create_publisher(Float32, '/power/odrive/power_estimate', 10)
        self.diag_pub = self.create_publisher(DiagnosticArray, '/diagnostics', 10)

        self._serial = None
        self._last_reading_time: Optional[float] = None
        self._last_error = ''
        period = 1.0 / max(float(self.get_parameter('publish_rate_hz').value), 0.1)
        self.timer = self.create_timer(period, self._tick)

    def _calibration(self):
        return CurrentCalibration(
            zero_offset_v=float(self.get_parameter('zero_offset_v').value),
            sensitivity_v_per_a=float(self.get_parameter('sensitivity_v_per_a').value),
            current_sign=float(self.get_parameter('current_sign').value),
        )

    def _connect(self):
        if self._serial is not None:
            return
        if serial is None:
            self._last_error = 'python3-serial is not installed'
            return
        port = str(self.get_parameter('port').value)
        baud = int(self.get_parameter('baud').value)
        try:
            self._serial = serial.Serial(port, baudrate=baud, timeout=0.05)
            self.get_logger().info(f'Connected to ESP32 current/e-stop serial port {port} at {baud}')
            self._last_error = ''
        except Exception as exc:
            self._serial = None
            self._last_error = f'{type(exc).__name__}: {exc}'

    def _tick(self):
        self._connect()
        if self._serial is not None:
            try:
                for _ in range(20):
                    raw = self._serial.readline()
                    if not raw:
                        break
                    line = raw.decode('utf-8', errors='replace').strip()
                    reading = parse_legacy_line(line, self._calibration())
                    if reading is not None:
                        self._publish_reading(reading)
                        self._last_reading_time = time.monotonic()
            except Exception as exc:
                self._last_error = f'{type(exc).__name__}: {exc}'
                try:
                    self._serial.close()
                except Exception:
                    pass
                self._serial = None
        self._publish_diagnostics()

    def _publish_reading(self, reading):
        if reading.estop_active is not None:
            self.estop_pub.publish(Bool(data=reading.estop_active))
        if reading.relay_enabled is not None:
            self.relay_pub.publish(Bool(data=reading.relay_enabled))
        if reading.adc_raw is not None:
            self.raw_pub.publish(Int32(data=reading.adc_raw))
        if reading.sensor_voltage_v is not None:
            self.voltage_pub.publish(Float32(data=float(reading.sensor_voltage_v)))
        if reading.current_a is not None:
            current = float(reading.current_a)
            nominal_bus = float(self.get_parameter('nominal_bus_voltage_v').value)
            self.current_pub.publish(Float32(data=current))
            self.bus_pub.publish(Float32(data=nominal_bus))
            self.power_pub.publish(Float32(data=current * nominal_bus))

    def _publish_diagnostics(self):
        now = time.monotonic()
        stale_timeout = float(self.get_parameter('stale_timeout_s').value)
        age = None if self._last_reading_time is None else now - self._last_reading_time
        stale = age is None or age > stale_timeout
        status = DiagnosticStatus()
        status.name = 'igvc_estop_current/serial'
        status.hardware_id = str(self.get_parameter('port').value)
        if self._last_error:
            status.level = DiagnosticStatus.ERROR
            status.message = self._last_error
        elif stale:
            status.level = DiagnosticStatus.WARN
            status.message = 'stale_or_no_reading'
        else:
            status.level = DiagnosticStatus.OK
            status.message = 'ok'
        status.values = [
            KeyValue(key='connected', value=str(self._serial is not None)),
            KeyValue(key='last_reading_age_s', value='none' if age is None else f'{age:.3f}'),
        ]
        arr = DiagnosticArray()
        arr.header.stamp = self.get_clock().now().to_msg()
        arr.status = [status]
        self.diag_pub.publish(arr)


def main(args=None):
    rclpy.init(args=args)
    node = EstopCurrentNode()
    try:
        rclpy.spin(node)
    finally:
        if node._serial is not None:
            node._serial.close()
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
