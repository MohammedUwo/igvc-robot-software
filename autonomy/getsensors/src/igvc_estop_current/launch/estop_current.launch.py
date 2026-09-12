from launch import LaunchDescription
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory
from pathlib import Path


def generate_launch_description():
    params = Path(get_package_share_directory('igvc_estop_current')) / 'config' / 'estop_current.yaml'
    return LaunchDescription([
        Node(package='igvc_estop_current', executable='estop_current_node', name='estop_current_node', output='screen', parameters=[str(params)])
    ])
