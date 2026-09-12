from pathlib import Path
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.substitutions import FindPackageShare
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():
    params = Path(get_package_share_directory('igvc_hardware_bringup')) / 'config' / 'realsense.yaml'
    rs_launch = PythonLaunchDescriptionSource([
        FindPackageShare('realsense2_camera'), '/launch/rs_launch.py'
    ])
    return LaunchDescription([
        IncludeLaunchDescription(rs_launch, launch_arguments={
            'config_file': str(params),
            'camera_name': 'camera',
            'serial_no': "'_939622074571'",
        }.items())
    ])
