import os
from pathlib import Path

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    params = Path(get_package_share_directory('igvc_hardware_bringup')) / 'config' / 'gps.yaml'
    env = dict(os.environ)
    # User-site NumPy >= 1.24 breaks Ubuntu Jammy transforms3d via deprecated np.float.
    # Keep this driver on distro Python packages until that user-site conflict is removed.
    env['PYTHONNOUSERSITE'] = '1'
    return LaunchDescription([
        Node(
            package='nmea_navsat_driver',
            executable='nmea_serial_driver',
            name='nmea_navsat_driver',
            output='screen',
            parameters=[str(params)],
            remappings=[('fix', '/gps/fix')],
            additional_env=env,
        )
    ])
