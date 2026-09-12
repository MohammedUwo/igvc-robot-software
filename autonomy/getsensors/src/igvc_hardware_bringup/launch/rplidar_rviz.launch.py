from pathlib import Path

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    package_share = Path(get_package_share_directory('igvc_hardware_bringup'))
    default_rviz_config = str(package_share / 'rviz' / 'rplidar.rviz')

    return LaunchDescription([
        DeclareLaunchArgument(
            'rviz_config',
            default_value=default_rviz_config,
            description='Path to the RViz config used to visualize the RPLIDAR /scan topic.',
        ),
        Node(
            package='rviz2',
            executable='rviz2',
            name='rplidar_rviz',
            output='screen',
            arguments=['-d', LaunchConfiguration('rviz_config')],
        ),
    ])
