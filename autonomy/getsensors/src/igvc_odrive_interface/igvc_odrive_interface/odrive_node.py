import math
import time
from typing import Optional

import rclpy
from rclpy.node import Node
from std_msgs.msg import Bool, Float32
from sensor_msgs.msg import JointState
from diagnostic_msgs.msg import DiagnosticArray, DiagnosticStatus, KeyValue
from std_srvs.srv import SetBool, Trigger

from .safety import SafetyGate

try:
    import odrive
except Exception:  # pragma: no cover
    odrive = None


class ODriveNode(Node):
    def __init__(self):
        super().__init__('odrive_node')
        self.declare_parameter('serial_number', '')
        self.declare_parameter('axis', 'axis1')
        self.declare_parameter('joint_name', 'odrive_m1_joint')
        self.declare_parameter('telemetry_rate_hz', 10.0)
        self.declare_parameter('command_enabled', False)
        self.declare_parameter('safety_timeout_s', 1.0)
        self.declare_parameter('command_timeout_s', 0.5)

        self.vbus_pub = self.create_publisher(Float32, '/odrive/vbus_voltage', 10)
        self.pos_pub = self.create_publisher(Float32, '/odrive/m1/position', 10)
        self.vel_pub = self.create_publisher(Float32, '/odrive/m1/velocity', 10)
        self.iq_pub = self.create_publisher(Float32, '/odrive/m1/iq_measured', 10)
        self.joint_pub = self.create_publisher(JointState, '/joint_states', 10)
        self.diag_pub = self.create_publisher(DiagnosticArray, '/diagnostics', 10)
        self.create_subscription(Bool, '/safety/estop', self._estop_cb, 10)
        self.create_subscription(Float32, '/odrive/m1/cmd_vel', self._cmd_vel_cb, 10)
        self.create_service(SetBool, '/odrive/enable', self._enable_cb)
        self.create_service(Trigger, '/odrive/clear_errors', self._clear_errors_cb)

        self._odrv = None
        self._axis = None
        self._last_error = ''
        self._last_safety_time: Optional[float] = None
        self._estop_active = True
        self._last_command_time: Optional[float] = None
        period = 1.0 / max(float(self.get_parameter('telemetry_rate_hz').value), 0.1)
        self.timer = self.create_timer(period, self._tick)

    @staticmethod
    def _read_int(obj, *names, default=0):
        for name in names:
            try:
                return int(getattr(obj, name))
            except Exception:
                continue
        return default

    def _connect(self):
        if self._odrv is not None:
            return
        if odrive is None:
            self._last_error = 'Python odrive module is not installed'
            return
        try:
            serial = str(self.get_parameter('serial_number').value)
            kwargs = {'timeout': 1}
            if serial:
                kwargs['serial_number'] = serial
            self._odrv = odrive.find_any(**kwargs)
            self._axis = getattr(self._odrv, str(self.get_parameter('axis').value))
            self._last_error = ''
            self.get_logger().info('Connected to ODrive')
        except Exception as exc:
            self._odrv = None
            self._axis = None
            self._last_error = f'{type(exc).__name__}: {exc}'

    def _estop_cb(self, msg):
        self._estop_active = bool(msg.data)
        self._last_safety_time = time.monotonic()

    def _safety_gate(self):
        now = time.monotonic()
        timeout = float(self.get_parameter('safety_timeout_s').value)
        stale = self._last_safety_time is None or (now - self._last_safety_time) > timeout
        return SafetyGate(
            command_enabled=bool(self.get_parameter('command_enabled').value),
            stale=stale,
            estop_active=self._estop_active,
        )

    def _cmd_vel_cb(self, msg):
        allowed, reason = self._safety_gate().command_allowed()
        if not allowed:
            self.get_logger().warn(f'Ignoring ODrive velocity command: {reason}', throttle_duration_sec=1.0)
            self._request_idle()
            return
        if self._axis is None:
            return
        try:
            self._axis.controller.input_vel = float(msg.data)
            self._last_command_time = time.monotonic()
        except Exception as exc:
            self._last_error = f'{type(exc).__name__}: {exc}'

    def _enable_cb(self, request, response):
        self.set_parameters([rclpy.parameter.Parameter('command_enabled', rclpy.Parameter.Type.BOOL, bool(request.data))])
        response.success = True
        response.message = 'commands_enabled' if request.data else 'commands_disabled'
        if not request.data:
            self._request_idle()
        return response

    def _clear_errors_cb(self, request, response):
        if self._odrv is None:
            response.success = False
            response.message = 'odrive_not_connected'
            return response
        try:
            self._odrv.clear_errors()
            response.success = True
            response.message = 'clear_errors_requested'
        except Exception as exc:
            response.success = False
            response.message = f'{type(exc).__name__}: {exc}'
        return response

    def _request_idle(self):
        if self._axis is None:
            return
        try:
            self._axis.requested_state = 1
        except Exception:
            pass

    def _tick(self):
        self._connect()
        if self._axis is not None:
            try:
                self._publish_telemetry()
                self._enforce_timeouts()
            except Exception as exc:
                self._last_error = f'{type(exc).__name__}: {exc}'
                self._odrv = None
                self._axis = None
        self._publish_diagnostics()

    def _publish_telemetry(self):
        now_msg = self.get_clock().now().to_msg()
        self.vbus_pub.publish(Float32(data=float(self._odrv.vbus_voltage)))
        pos = float(self._axis.encoder.pos_estimate)
        vel = float(self._axis.encoder.vel_estimate)
        self.pos_pub.publish(Float32(data=pos))
        self.vel_pub.publish(Float32(data=vel))
        try:
            iq = float(self._axis.motor.current_control.Iq_measured)
            self.iq_pub.publish(Float32(data=iq))
        except Exception:
            pass
        joint = JointState()
        joint.header.stamp = now_msg
        joint.name = [str(self.get_parameter('joint_name').value)]
        joint.position = [pos]
        joint.velocity = [vel]
        joint.effort = []
        self.joint_pub.publish(joint)

    def _enforce_timeouts(self):
        allowed, _ = self._safety_gate().command_allowed()
        now = time.monotonic()
        command_timeout = float(self.get_parameter('command_timeout_s').value)
        command_stale = self._last_command_time is not None and (now - self._last_command_time) > command_timeout
        if not allowed or command_stale:
            self._request_idle()

    def _publish_diagnostics(self):
        status = DiagnosticStatus()
        status.name = 'igvc_odrive_interface/axis1'
        status.hardware_id = str(self.get_parameter('serial_number').value or 'odrive_any')
        if self._last_error:
            status.level = DiagnosticStatus.ERROR
            status.message = self._last_error
        elif self._axis is None:
            status.level = DiagnosticStatus.WARN
            status.message = 'not_connected'
        else:
            axis_error = self._read_int(self._axis, 'active_errors', 'error', default=-1)
            odrive_error = self._read_int(self._odrv, 'error', default=0)
            active_errors = axis_error | odrive_error if axis_error >= 0 else axis_error
            status.level = DiagnosticStatus.ERROR if active_errors else DiagnosticStatus.OK
            status.message = 'active_errors' if active_errors else 'ok'
            status.values = [
                KeyValue(key='axis_state', value=str(getattr(self._axis, 'current_state', 'unknown'))),
                KeyValue(key='axis_error_or_active_errors', value=str(axis_error)),
                KeyValue(key='odrive_error', value=str(odrive_error)),
                KeyValue(key='active_errors_combined', value=str(active_errors)),
                KeyValue(key='commands_allowed', value=str(self._safety_gate().command_allowed())),
            ]
        arr = DiagnosticArray()
        arr.header.stamp = self.get_clock().now().to_msg()
        arr.status = [status]
        self.diag_pub.publish(arr)


def main(args=None):
    rclpy.init(args=args)
    node = ODriveNode()
    try:
        rclpy.spin(node)
    finally:
        node._request_idle()
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
