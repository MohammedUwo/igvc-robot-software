import glob
import os
from pathlib import Path

import rclpy
from diagnostic_msgs.msg import DiagnosticArray, DiagnosticStatus, KeyValue
from rclpy.node import Node


class SerialPermissions(Node):
    def __init__(self):
        super().__init__('serial_permissions')
        self.declare_parameter('expected_paths', [
            '/dev/ttyUSB0',
            '/dev/ttyUSB1',
            '/dev/ttyACM0',
            '/dev/ttyACM1',
        ])
        self.declare_parameter('publish_rate_hz', 1.0)
        self.pub = self.create_publisher(DiagnosticArray, '/diagnostics', 10)
        period = 1.0 / max(float(self.get_parameter('publish_rate_hz').value), 0.1)
        self.timer = self.create_timer(period, self._tick)

    def _status_for_path(self, path: str) -> DiagnosticStatus:
        status = DiagnosticStatus()
        status.name = f'igvc_hardware_bringup/serial_permissions/{path}'
        status.hardware_id = path
        exists = os.path.exists(path)
        realpath = os.path.realpath(path) if exists else ''
        can_read = os.access(path, os.R_OK) if exists else False
        can_write = os.access(path, os.W_OK) if exists else False
        can_rw = can_read and can_write
        if not exists:
            status.level = DiagnosticStatus.ERROR
            status.message = 'missing'
        elif not can_rw:
            status.level = DiagnosticStatus.ERROR
            status.message = 'permission_denied'
        else:
            status.level = DiagnosticStatus.OK
            status.message = 'ok'
        status.values = [
            KeyValue(key='exists', value=str(exists)),
            KeyValue(key='realpath', value=realpath),
            KeyValue(key='can_read', value=str(can_read)),
            KeyValue(key='can_write', value=str(can_write)),
        ]
        try:
            stat = os.stat(path)
            status.values.extend([
                KeyValue(key='mode_octal', value=oct(stat.st_mode & 0o777)),
                KeyValue(key='uid', value=str(stat.st_uid)),
                KeyValue(key='gid', value=str(stat.st_gid)),
            ])
        except Exception as exc:
            status.values.append(KeyValue(key='stat_error', value=f'{type(exc).__name__}: {exc}'))
        return status

    def _tick(self):
        paths = list(self.get_parameter('expected_paths').value)
        arr = DiagnosticArray()
        arr.header.stamp = self.get_clock().now().to_msg()
        arr.status = [self._status_for_path(str(path)) for path in paths]
        self.pub.publish(arr)


def main(args=None):
    rclpy.init(args=args)
    node = SerialPermissions()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
