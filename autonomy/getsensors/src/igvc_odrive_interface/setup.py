from setuptools import find_packages, setup

package_name = 'igvc_odrive_interface'

setup(
    name=package_name,
    version='0.1.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/config', ['config/odrive.yaml']),
        ('share/' + package_name + '/launch', ['launch/odrive.launch.py']),
        ('share/' + package_name + '/scripts', ['scripts/configure_db59_odrive.py']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='IGVC',
    maintainer_email='igvc@example.com',
    description='Safe ODrive V3.6 ROS 2 telemetry and command interface.',
    license='MIT',
    entry_points={'console_scripts': ['odrive_node = igvc_odrive_interface.odrive_node:main']},
)
