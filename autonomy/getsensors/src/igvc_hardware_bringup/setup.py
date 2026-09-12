from glob import glob
from setuptools import find_packages, setup

package_name = 'igvc_hardware_bringup'

setup(
    name=package_name,
    version='0.1.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml', 'README.md']),
        ('share/' + package_name + '/launch', glob('launch/*.launch.py')),
        ('share/' + package_name + '/config', glob('config/*.yaml')),
        ('share/' + package_name + '/rviz', glob('rviz/*.rviz')),
        ('share/' + package_name + '/udev', glob('udev/*.rules')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='IGVC',
    maintainer_email='igvc@example.com',
    description='IGVC robot hardware bringup launch/config package.',
    license='MIT',
    entry_points={
        'console_scripts': [
            'serial_watchdog = igvc_hardware_bringup.serial_watchdog:main',
            'serial_permissions = igvc_hardware_bringup.serial_permissions:main',
        ],
    },
)
