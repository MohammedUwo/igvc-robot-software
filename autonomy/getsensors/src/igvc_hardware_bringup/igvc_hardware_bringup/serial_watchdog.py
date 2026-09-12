import glob
import os
from pathlib import Path
from typing import List

import rclpy
from diagnostic_msgs.msg import DiagnosticArray, DiagnosticStatus, KeyValue
from rclpy.node import Node


def _matches(patterns: List[str]) -> List[str]:
    found = []
    for pattern in patterns:
        for item in glob.glob(pattern):
            if item not in found:
                found.append(item)
    return sorted(found)


class SerialWatchdogNode(Node):
    def __init__(self):
        super().__init__('serial_watchdog')
        self.declare_parameter('expected_paths', [
            '/dev/igvc_estop',
            '/dev/igvc_rplidar',
            '/dev/igvc_gps',
        ])
        self.declare_parameter('publish_rate_hz', 2.0)
        self.diag_pub = self.create_publisher(DiagnosticArray, '/diagnostics', 10)
        period = 1.0 / max(float(self.get_parameter('publish_rate_hz').value), 0.1)
        self.timer = self.create_timer(period, self._tick)

    def _tick(self):
        statuses = []
        for expected in list(self.get_parameter('expected_paths').value):
            path = str(expected)
            status = DiagnosticStatus()
            status.name = f'igvc_hardware_bringup/serial_watchdog/{Path(path).name}'
            status.hardware_id = path
            exists = os.path.exists(path)
            realpath = os.path.realpath(path) if exists else ''
            readable = os.access(path, os.R_OK) if exists else False
            writable = os.access(path, os.W_OK) if exists else False
            status.values = [
                KeyValue(key='exists', value=str(exists)),
                KeyValue(key='realpath', value=realpath),
                KeyValue(key='readable', value=str(readable)),
                KeyValue(key='writable', value=str(writable)),
            ]
            if not exists:
                status.level = DiagnosticStatus.ERROR
                status.message = 'missing'
            elif not (readable and writable):
                status.level = DiagnosticStatus.ERROR
                status.message = 'permission_denied'
            else:
                status.level = DiagnosticStatus.OK
                status.message = 'ok'
            statuses.append(status)

        inventory = DiagnosticStatus()
        inventory.name = 'igvc_hardware_bringup/serial_watchdog/inventory'
        inventory.hardware_id = 'serial_by_id'
        by_id = _matches(['/dev/serial/by-id/*'])
        inventory.level = DiagnosticStatus.OK
        inventory.message = 'ok'
        inventory.values = [KeyValue(key='serial_by_id', value=';'.join(by_id))]
        statuses.append(inventory)

        msg = DiagnosticArray()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.status = statuses
        self.diag_pub.publish(msg)


def main(args=None):
    rclpy.init(args=args)
    node = SerialWatchdogNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
