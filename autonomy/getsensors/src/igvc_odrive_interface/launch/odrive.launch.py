from pathlib import Path
from launch import LaunchDescription
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():
    params = Path(get_package_share_directory('igvc_odrive_interface')) / 'config' / 'odrive.yaml'
    return LaunchDescription([
        Node(package='igvc_odrive_interface', executable='odrive_node', name='odrive_node', output='screen', parameters=[str(params)])
    ])
