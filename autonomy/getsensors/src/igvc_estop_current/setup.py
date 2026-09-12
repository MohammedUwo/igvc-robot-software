from setuptools import find_packages, setup

package_name = 'igvc_estop_current'

setup(
    name=package_name,
    version='0.1.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/config', ['config/estop_current.yaml']),
        ('share/' + package_name + '/launch', ['launch/estop_current.launch.py']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='IGVC',
    maintainer_email='igvc@example.com',
    description='ESP32 e-stop/current serial bridge for ROS 2.',
    license='MIT',
    entry_points={'console_scripts': ['estop_current_node = igvc_estop_current.serial_node:main']},
)
