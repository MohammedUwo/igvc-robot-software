from pathlib import Path
from launch import LaunchDescription
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():
    params = Path(get_package_share_directory('igvc_hardware_bringup')) / 'config' / 'serial_watchdog.yaml'
    return LaunchDescription([
        Node(
            package='igvc_hardware_bringup',
            executable='serial_watchdog',
            name='serial_watchdog',
            output='screen',
            parameters=[str(params)],
        )
    ])
