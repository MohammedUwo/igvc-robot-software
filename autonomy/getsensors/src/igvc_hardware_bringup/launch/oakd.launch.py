from pathlib import Path
from launch import LaunchDescription
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():
    params = Path(get_package_share_directory('igvc_hardware_bringup')) / 'config' / 'oakd.yaml'
    return LaunchDescription([
        Node(package='depthai_ros_driver', executable='camera_node', name='oak', output='screen', parameters=[str(params)])
    ])
