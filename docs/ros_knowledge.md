ROS STUFF

important commands:
 source /opt/ros/humble/setup.bash
    cd /home/igvc/gz_ws/ros2_ws
    source install/setup.bash
    ros2 topic list ( or ros2 topic echo /topic [the topic u want])
    
    
SETTING CAM:
- ros2 launch realsense2_camera rs_launch.py
-
- 
ros2 launch diff_drive_robot robot.launch.py world:=/media/igvc/OS/dynamic_Gazebo_IGVC_Autonav_Course/generated/generated_world_42.sdf




-- launching gazebo + rviz
ros2 pkg prefix diff_drive_robot
ros2 launch diff_drive_robot robot.launch.py

-- launch diff worlds
 ros2 launch diff_drive_robot robot.launch.py world:=/home/igvc/gz_ws/ros2_ws/src/diff_drive_robot/worlds/obstacles.world (edit the world


-- python code
/home/igvc/gz_ws/ros2_ws/src/diff_drive_robot/diff_drive_robot/
behavior_node.py
detect_line.py
waypoint_driver.py
emlid_gps.py
odrive.py
path_trail.py
    process_image.py

   open vscode--> code .



--------------------------------------------------------------
 The ROS package is here:
    
    /home/igvc/gz_ws/ros2_ws/src/diff_drive_robot
    
    It is an ament_python ROS 2 package for a differential-drive robot. It combines Gazebo simulation, ROS-Gazebo bridging, robot description/URDF, autonomous behavior nodes, SLAM/localization, GPS waypoint driving, line detection, obstacle avoidance, and RViz visualization.
    
    High-level purpose:
    - Simulate or run a diff-drive robot.
    - Spawn the robot in Gazebo.
    - Bridge Gazebo topics into ROS 2.
    - Run perception/control nodes for:
      - line following
      - obstacle avoidance
      - waypoint driving
      - ODrive motor command output
      - Emlid GPS input
      - path visualization
    - Run SLAM Toolbox, robot_localization EKF, and a local Nav2 costmap.
    
    Top-level folder layout:
    
    /home/igvc/gz_ws/ros2_ws/src/diff_drive_robot
    ├── diff_drive_robot/
    │   Python ROS nodes
    ├── launch/
    │   ROS 2 launch files
    ├── config/
    │   YAML configs for controllers, SLAM, EKF, bridge, waypoints, costmap
    ├── urdf/
    │   robot description files
    ├── worlds/
    │   Gazebo world files
    ├── rviz/
    │   RViz configs
    ├── resource/
    │   ament package marker
    ├── package.xml
    ├── setup.py
    ├── README.md
    └── EMLID_ROS_INTEGRATION.md
    
    Main launch files:
    
    1. launch/robot.launch.py
    
    This is the main simulation launch. It:
    - Starts Gazebo server and client.
    - Loads the default world:
      /home/igvc/gz_ws/ros2_ws/src/diff_drive_robot/worlds/circle.world
    - Publishes the robot description through rsp.launch.py.
    - Spawns the robot into Gazebo as diff_bot.
    - Starts ros_gz_bridge using config/gz_bridge.yaml.
    - Starts RViz with rviz/bot.rviz and rviz/map_path.rviz.
    - Starts controller spawners:
      - joint_state_broadcaster
      - diff_drive_controller
    - Includes autonomous_drive.launch.py.
    
    Normal command:
    
    cd /home/igvc/gz_ws/ros2_ws
    source install/setup.bash
    ros2 launch diff_drive_robot robot.launch.py
    
    2. launch/autonomous_drive.launch.py
    
    This starts the autonomy stack without directly launching Gazebo. It launches:
    - odrive_node
    - detect_line
    - behavior_node
    - path_trail
    - robot_localization EKF
    - emlid_gps_node
    - waypoint_driver
    - slam_toolbox
    - nav2_costmap_2d local_costmap
    - RViz full view
    - RViz map/path view
    
    This is the newer navigation/autonomy-focused launch file.
    
    3. launch/rsp.launch.py
    
    Robot State Publisher launch. It publishes the URDF robot description.
    
    4. launch/rviz_map_path.launch.py
    
    Launches the dedicated map/path RViz view.
    
    Python ROS nodes:
    
    1. diff_drive_robot/behavior_node.py
    
    Main behavior arbitration node.
    
    Publishes:
    - /cmd_vel
    - /diff_drive_controller/cmd_vel_unstamped
    
    Subscribes:
    - /line_cmd_vel
    - /obstacle_cmd_vel
    - /waypoint_cmd_vel
    - /scan
    - /map
    
    Purpose:
    - Combines commands from line following, obstacle avoidance, waypoint navigation, lidar, and map/costmap info.
    - According to the Emlid integration doc, the behavior priority is:
      1. critical lidar obstacle avoidance
      2. camera-based obstacle avoidance
      3. waypoint navigation commands
      4. SLAM map avoidance
      5. line following
    
    2. diff_drive_robot/detect_line.py
    
    Camera line detection / line-following node.
    
    Publishes:
    - /filtered_white_mask
    - /line_cmd_vel
    - /obstacle_cmd_vel
    
    Subscribes:
    - /obstacle_cmd_vel
    
    Uses:
    - cv_bridge
    - OpenCV
    - NumPy
    
    Purpose:
    - Processes camera images.
    - Detects white lane/line features.
    - Produces velocity commands for line following.
    - Also appears to contribute obstacle-related command output.
    
    3. diff_drive_robot/waypoint_driver.py
    
    Waypoint-following node.
    
    Publishes:
    - /waypoint_cmd_vel
    
    Subscribes:
    - /odometry/filtered
    
    Uses:
    - config/waypoints.yaml
    
    Purpose:
    - Reads a list of x/y goals.
    - Uses EKF-filtered odometry.
    - Turns toward each waypoint.
    - Drives forward until within tolerance.
    - Pauses at goal, then advances to next waypoint.
    
    Current waypoint config:
    
    /home/igvc/gz_ws/ros2_ws/src/diff_drive_robot/config/waypoints.yaml
    
    Contains:
    - waypoints:
      - (1.0, 0.0)
      - (1.0, 1.0)
      - (0.0, 1.0)
    - goal_tolerance: 0.3
    - max_speed: 0.4
    - max_angular_speed: 1.0
    - yaw_gain: 1.5
    - pause_at_goal: 2.0
    
    4. diff_drive_robot/emlid_gps.py
    
    Emlid GPS integration node.
    
    Publishes:
    - /fix
    - /fix_status
    - /emlid/pose
    
    Purpose:
    - Connects to an Emlid Reach RS+ GNSS receiver.
    - Reads NMEA data over TCP/UDP.
    - Publishes standard NavSatFix data.
    - Converts latitude/longitude into a local ENU pose.
    
    Launch defaults in autonomous_drive.launch.py:
    - emlid_host: 192.168.1.100
    - emlid_port: 2101
    - protocol: tcp
    - frame_id: gps
    - origin_lat: 47.47895
    - origin_lon: 19.057785
    - origin_alt: 0.0
    
    5. diff_drive_robot/odrive.py
    
    ODrive motor interface node.
    
    Publishes:
    - odrive/motor_velocity
    
    Subscribes:
    - /diff_drive_controller/cmd_vel_unstamped
    
    Purpose:
    - Converts diff-drive velocity commands into motor velocity commands.
    - Interfaces with ODrive hardware using the odrive Python library.
    - Has parameters like velocity_scale and max_velocity.
    
    6. diff_drive_robot/path_trail.py
    
    Path visualization/tracking node.
    
    Publishes:
    - robot_path
    - robot_path_markers
    
    Subscribes:
    - odometry/filtered
    - odrive/motor_velocity
    
    Purpose:
    - Tracks the robot’s movement.
    - Publishes a nav_msgs/Path and visualization markers for RViz.
    
    7. diff_drive_robot/process_image.py
    
    Helper image-processing module.
    
    Purpose:
    - Contains OpenCV helper functions for line detection:
      - find_line
      - apply_search_window
      - draw_window2
      - tuning window helpers
      - coordinate normalization helpers
    
    8. diff_drive_robot/avoid_obstacle.py
    
    Exists, but from inspection it appears mostly empty or unused.
    
    Installed console scripts from setup.py:
    
    - detect_line
    - behavior_node
    - odrive_node
    - path_trail
    - emlid_gps_node
    - waypoint_driver
    
    Config files:
    
    config/costmap.yaml
    - Nav2 local costmap parameters.
    
    config/ekf.yaml
    - robot_localization EKF configuration.
    
    config/gaz_ros2_ctl_use_sim.yaml
    - Gazebo / ros2_control simulation config.
    
    config/gz_bridge.yaml
    - ROS-Gazebo topic bridge config.
    
    config/mapper_params_online_async.yaml
    - SLAM Toolbox async mapping config.
    
    config/my_controllers.yaml
    - ros2_control controller config.
    
    config/rtabmap_params.yaml
    - RTAB-Map parameters, although the active launch currently uses SLAM Toolbox.
    
    config/slam_toolbox.yaml
    - Another SLAM Toolbox config.
    
    config/waypoints.yaml
    - Waypoint navigation goals and motion parameters.
    
    Worlds:
    
    worlds/circle.world
    worlds/empty.world
    worlds/obstacles.world
    worlds/track.world
    worlds/world.sdf
    
    The default in robot.launch.py is:
    
    worlds/circle.world
    
    RViz configs:
    
    rviz/bot.rviz
    - Full visualization: robot, sensors, camera/map/lidar.
    
    rviz/map_path.rviz
    - Dedicated 2D map/path visualization.
    
    Important notes / possible issues I noticed:
    
    1. README says ROS 2 Jazzy / Ubuntu 24.04, but this machine appears to have ROS Humble-era paths elsewhere. You may need to confirm which ROS distro is actually sourced before building/running.
    
    2. package.xml still has placeholder metadata:
    - version: 0.0.0
    - description: TODO: Package description
    - maintainer: adoodevv
    
    But setup.py says:
    - maintainer: igvc
    - description: Autonomous diff drive robot
    - license: Apache-2.0
    
    So metadata is inconsistent.
    
    3. robot.launch.py imports this:
    
    from click import edit
    
    That looks accidental and probably unnecessary.
    
    4. robot.launch.py defines rviz2_map_path twice. The second definition overwrites the first. It is harmless but messy.
    
    5. autonomous_drive.launch.py starts RViz twice:
    - rviz_full
    - rviz_map_path
    
    robot.launch.py also starts RViz views, then includes autonomous_drive.launch.py, which starts more RViz windows. So launching robot.launch.py may open duplicate RViz windows.
    
    6. The Emlid node has hard-coded default device IP/origin coordinates inside autonomous_drive.launch.py. For real robot use, those should probably become launch arguments or YAML parameters.
    
    7. This package is not just “navigation”; it is a combined simulation + autonomy + hardware interface package. The most navigation-relevant parts are:
    - autonomous_drive.launch.py
    - behavior_node.py
    - waypoint_driver.py
    - emlid_gps.py
    - config/waypoints.yaml
    - config/ekf.yaml
    - config/costmap.yaml
    - config/mapper_params_online_async.yaml
    
    Most likely command to run the full stack:
    
    cd /home/igvc/gz_ws/ros2_ws
    source install/setup.bash
    ros2 launch diff_drive_robot robot.launch.py
    
    Most likely command to run only the autonomy/navigation stack:
    
    cd /home/igvc/gz_ws/ros2_ws
    source install/setup.bash
    ros2 launch diff_drive_robot autonomous_drive.launch.py



--------------------------------SKIP HERE-------------------------------------------


  No — running those ROS commands does not “open a window that navigates to the code.”
    
    There are two separate things:
    
    1. Editing the ROS files
       You open the package folder in an editor, like VS Code, nano, vim, etc.
    
    2. Running the ROS/Gazebo simulation
       You build the workspace, source it, then launch ROS nodes. Some launch files open GUI windows like Gazebo and RViz, but they do not open the source-code folder.
    
    Your package lives here:
    
    /home/igvc/gz_ws/ros2_ws/src/diff_drive_robot
    
    Your workspace root is:
    
    /home/igvc/gz_ws/ros2_ws
    
    The basic workflow is:
    
    cd /home/igvc/gz_ws/ros2_ws/src/diff_drive_robot
    edit files
    
    then:
    
    cd /home/igvc/gz_ws/ros2_ws
    colcon build --symlink-install --packages-select diff_drive_robot
    source install/setup.bash
    ros2 launch diff_drive_robot robot.launch.py
    
    That launches the simulation, not the code editor.
    
    If you want to open the source folder in VS Code, you would do:
    
    code /home/igvc/gz_ws/ros2_ws/src/diff_drive_robot
    
    If VS Code is installed and configured, that opens a window at the package folder.
    
    Full pipeline: editing code to running simulation
    ================================================
    
    1. Package/source location
    
    
    Your ROS package source is:
    
    /home/igvc/gz_ws/ros2_ws/src/diff_drive_robot
    
    This is where you edit:
    
    - Python nodes:
      /home/igvc/gz_ws/ros2_ws/src/diff_drive_robot/diff_drive_robot/
    
    - Launch files:
      /home/igvc/gz_ws/ros2_ws/src/diff_drive_robot/launch/
    
    - Config files:
      /home/igvc/gz_ws/ros2_ws/src/diff_drive_robot/config/
    
    - Robot model / URDF:
      /home/igvc/gz_ws/ros2_ws/src/diff_drive_robot/urdf/
    
    - Gazebo worlds:
      /home/igvc/gz_ws/ros2_ws/src/diff_drive_robot/worlds/
    
    - RViz configs:
      /home/igvc/gz_ws/ros2_ws/src/diff_drive_robot/rviz/
    
    2. Edit the files
    
    
    Example:
    
    cd /home/igvc/gz_ws/ros2_ws/src/diff_drive_robot
    
    Then open with your editor:
    
    code .
    
    or:
    
    nano launch/robot.launch.py
    
    or:
    
    nano diff_drive_robot/behavior_node.py
    
    or:
    
    nano worlds/circle.world
    
    Editing files here changes the source version of the package.
    
    3. Build the workspace
    
    
    After editing, go to the workspace root:
    
    cd /home/igvc/gz_ws/ros2_ws
    
    Build only this package:
    
    colcon build --symlink-install --packages-select diff_drive_robot
    
    The --symlink-install flag is important. It means many Python/config/launch changes are linked into the install space instead of copied. That makes iteration faster.
    
    However, you should still rebuild when you change:
    
    - setup.py
    - package.xml
    - installed file lists
    - new launch files
    - new config files
    - new Python entry points
    - new URDF/world files that were not previously installed
    
    4. Source the workspace
    
    
    After building, run:
    
    source install/setup.bash
    
    This tells ROS where to find your package.
    
    If you skip this, ROS may say:
    
    Package 'diff_drive_robot' not found
    
    or it may run an older version from another workspace.
    
    5. Launch simulation
    
    
    The main simulation launch is:
    
    ros2 launch diff_drive_robot robot.launch.py
    
    This does several things:
    
    - starts Gazebo server
    - starts Gazebo GUI/client
    - loads a world file
    - starts robot_state_publisher
    - spawns the robot into Gazebo
    - starts ros_gz_bridge
    - starts ROS controllers
    - launches the autonomous driving stack
    - opens RViz windows
    
    The default world is currently selected inside:
    
    /home/igvc/gz_ws/ros2_ws/src/diff_drive_robot/launch/robot.launch.py
    
    Specifically, this line chooses the default world:
    
    world_path = os.path.join(get_package_share_directory(package_name),'worlds', 'circle.world')
    
    So by default, it loads:
    
    worlds/circle.world
    
    You can also override the world from the command line if the launch argument works correctly:
    
    ros2 launch diff_drive_robot robot.launch.py world:=/home/igvc/gz_ws/ros2_ws/src/diff_drive_robot/worlds/obstacles.world
    
    6. Gazebo window vs RViz window
    
    
    When you launch robot.launch.py, you may see multiple windows.
    
    Gazebo:
    - Shows the 3D simulation world.
    - This is where the robot, ground, obstacles, sensors, and physics exist.
    
    RViz:
    - Shows ROS data.
    - This is where you visualize topics like:
      - laser scan
      - odometry
      - map
      - robot model
      - path
      - camera image
      - costmap
    
    Gazebo is the simulator.
    
    RViz is the ROS visualization/debugging tool.
    
    7. ROS-Gazebo bridge
    
    
    Gazebo and ROS do not automatically share every topic. This package uses ros_gz_bridge.
    
    The bridge config is:
    
    /home/igvc/gz_ws/ros2_ws/src/diff_drive_robot/config/gz_bridge.yaml
    
    That file decides what Gazebo topics are bridged into ROS and vice versa.
    
    For example, it may bridge things like:
    
    - camera image
    - lidar scan
    - clock
    - robot command velocity
    - odometry
    
    The launch file starts the bridge here:
    
    ros_gz_bridge = Node(
        package="ros_gz_bridge",
        executable="parameter_bridge",
        ...
    )
    
    If a ROS node is not receiving sensor data, the bridge config is one of the first places to check.
    
    8. Robot model pipeline
    
    
    The robot model lives in:
    
    /home/igvc/gz_ws/ros2_ws/src/diff_drive_robot/urdf/
    
    The main launch file points to:
    
    urdf/robot.urdf
    
    robot.launch.py starts robot_state_publisher using rsp.launch.py.
    
    That publishes the robot description to ROS.
    
    Then Gazebo spawns the robot using:
    
    ros_gz_sim create -topic robot_description -name diff_bot ...
    
    So the model pipeline is:
    
    URDF file
    → robot_state_publisher
    → robot_description topic
    → ros_gz_sim create
    → robot appears in Gazebo
    
    If you edit the robot body, wheels, sensors, lidar position, camera position, etc., you edit the URDF files.
    
    Then rebuild/source/launch again.
    
    9. Autonomy/navigation stack pipeline
    
    
    The main autonomy launch file is:
    
    /home/igvc/gz_ws/ros2_ws/src/diff_drive_robot/launch/autonomous_drive.launch.py
    
    This launches your control stack.
    
    Important nodes:
    
    behavior_node
    
    File:
    
    diff_drive_robot/behavior_node.py
    
    This is the command arbitration node.
    
    It receives possible movement commands from:
    
    - line following
    - obstacle avoidance
    - waypoint navigation
    - lidar/map logic
    
    It publishes final velocity commands to:
    
    - /cmd_vel
    - /diff_drive_controller/cmd_vel_unstamped
    
    This is basically the “decision combiner.”
    
    detect_line
    
    File:
    
    diff_drive_robot/detect_line.py
    
    This processes camera images and generates line-following commands.
    
    Publishes:
    
    - /line_cmd_vel
    - /obstacle_cmd_vel
    - /filtered_white_mask
    
    waypoint_driver
    
    File:
    
    diff_drive_robot/waypoint_driver.py
    
    This drives toward waypoints from:
    
    config/waypoints.yaml
    
    It subscribes to:
    
    /odometry/filtered
    
    and publishes:
    
    /waypoint_cmd_vel
    
    emlid_gps_node
    
    File:
    
    diff_drive_robot/emlid_gps.py
    
    This is for Emlid GPS input. It publishes:
    
    - /fix
    - /fix_status
    - /emlid/pose
    
    path_trail
    
    File:
    
    diff_drive_robot/path_trail.py
    
    This publishes path visualization:
    
    - robot_path
    - robot_path_markers
    
    odrive_node
    
    File:
    
    diff_drive_robot/odrive.py
    
    This converts velocity commands into ODrive motor commands.
    
    In simulation, this may not be needed unless you are also testing the real motor-control path.
    
    SLAM Toolbox
    
    Config:
    
    config/mapper_params_online_async.yaml
    
    Launched by:
    
    autonomous_drive.launch.py
    
    It builds/updates a map using sensor data.
    
    robot_localization EKF
    
    Config:
    
    config/ekf.yaml
    
    Publishes filtered odometry, usually:
    
    /odometry/filtered
    
    The waypoint driver depends on this.
    
    local_costmap
    
    Config:
    
    config/costmap.yaml
    
    Launched as:
    
    nav2_costmap_2d
    
    This creates a costmap from obstacle/sensor data.
    
    10. Typical data flow during simulation
    
    
    When the full simulation is running, the rough data flow is:
    
    Gazebo world
    → simulated robot sensors
    → ros_gz_bridge
    → ROS topics
    
    Then:
    
    camera image
    → detect_line.py
    → /line_cmd_vel
    
    lidar scan
    → behavior_node.py
    → obstacle avoidance decision
    
    odometry / localization
    → robot_localization EKF
    → /odometry/filtered
    → waypoint_driver.py
    → /waypoint_cmd_vel
    
    SLAM/lidar data
    → slam_toolbox
    → map
    
    costmap config + sensor data
    → nav2_costmap_2d
    → local costmap
    
    Then:
    
    /line_cmd_vel
    /obstacle_cmd_vel
    /waypoint_cmd_vel
    /scan
    /map
    → behavior_node.py
    → /diff_drive_controller/cmd_vel_unstamped
    → Gazebo/ros2_control/diff_drive_controller
    → robot moves
    
    So behavior_node.py is one of the most important files for actual driving behavior.
    
    11. Adding obstacles in Gazebo
    ==============================
    
    There are a few ways to add obstacles.
    
    Option A: Edit the world file directly
    
    
    World files are here:
    
    /home/igvc/gz_ws/ros2_ws/src/diff_drive_robot/worlds/
    
    For example:
    
    worlds/circle.world
    worlds/obstacles.world
    worlds/track.world
    worlds/world.sdf
    
    If robot.launch.py uses circle.world, edit:
    
    /home/igvc/gz_ws/ros2_ws/src/diff_drive_robot/worlds/circle.world
    
    A simple box obstacle in SDF looks like this:
    
    <model name="box_obstacle_1">
      <static>true</static>
      <pose>3 2 0.5 0 0 0</pose>
      <link name="link">
        <collision name="collision">
          <geometry>
            <box>
              <size>1 1 1</size>
            </box>
          </geometry>
        </collision>
        <visual name="visual">
          <geometry>
            <box>
              <size>1 1 1</size>
            </box>
          </geometry>
          <material>
            <ambient>1 0 0 1</ambient>
            <diffuse>1 0 0 1</diffuse>
          </material>
        </visual>
      </link>
    </model>
    
    Important parts:
    
    <pose>3 2 0.5 0 0 0</pose>
    
    means:
    
    x = 3 meters
    y = 2 meters
    z = 0.5 meters
    roll = 0
    pitch = 0
    yaw = 0
    
    The z value is 0.5 because the box is 1 meter tall, so its center should be half its height above the ground.
    
    If you make a 0.5 m tall box, use z = 0.25.
    
    Example smaller obstacle:
    
    <model name="small_obstacle">
      <static>true</static>
      <pose>2.0 1.0 0.25 0 0 0</pose>
      <link name="link">
        <collision name="collision">
          <geometry>
            <box>
              <size>0.5 0.5 0.5</size>
            </box>
          </geometry>
        </collision>
        <visual name="visual">
          <geometry>
            <box>
              <size>0.5 0.5 0.5</size>
            </box>
          </geometry>
          <material>
            <ambient>0 0 1 1</ambient>
            <diffuse>0 0 1 1</diffuse>
          </material>
        </visual>
      </link>
    </model>
    
    After editing the world:
    
    cd /home/igvc/gz_ws/ros2_ws
    colcon build --symlink-install --packages-select diff_drive_robot
    source install/setup.bash
    ros2 launch diff_drive_robot robot.launch.py
    
    Option B: Use a different world file
    
    
    Instead of editing circle.world, you can create a new one:
    
    /home/igvc/gz_ws/ros2_ws/src/diff_drive_robot/worlds/my_test.world
    
    Then launch it with:
    
    ros2 launch diff_drive_robot robot.launch.py world:=/home/igvc/gz_ws/ros2_ws/src/diff_drive_robot/worlds/my_test.world
    
    Or change robot.launch.py to make your new world the default:
    
    world_path = os.path.join(get_package_share_directory(package_name),'worlds', 'my_test.world')
    
    Option C: Add obstacles through Gazebo GUI
    
    
    Gazebo lets you insert models manually through the GUI, depending on your version/setup.
    
    But this is usually not ideal for repeatable testing because the obstacles are not saved unless you export/save the world.
    
    For development, editing the .world/.sdf file is better because it is reproducible.
    
    12. Adding obstacles that sensors can detect
    ===========================================
    
    For an obstacle to affect the robot properly, it should have both:
    
    1. visual geometry
       So you can see it in Gazebo.
    
    2. collision geometry
       So physics and sensors can interact with it.
    
    This is why the example has both:
    
    <visual name="visual">...</visual>
    
    and:
    
    <collision name="collision">...</collision>
    
    If you only add visual, the robot may see a pretty box, but physics/lidar may not treat it correctly.
    
    If you only add collision, it may block the robot but be invisible.
    
    13. Testing whether obstacles are seen by ROS
    =============================================
    
    After launching the sim, check topics:
    
    ros2 topic list
    
    Look for sensor topics like:
    
    /scan
    /camera/image
    /odom
    /cmd_vel
    /diff_drive_controller/cmd_vel_unstamped
    
    To inspect lidar:
    
    ros2 topic echo /scan
    
    To inspect camera:
    
    ros2 topic hz /camera/image
    
    To see command output:
    
    ros2 topic echo /diff_drive_controller/cmd_vel_unstamped
    
    To see the node graph:
    
    rqt_graph
    
    If rqt_graph is installed, this opens a graph of nodes and topics.
    
    14. Editing robot behavior
    ==========================
    
    If the robot does not avoid obstacles correctly, likely files are:
    
    /home/igvc/gz_ws/ros2_ws/src/diff_drive_robot/diff_drive_robot/behavior_node.py
    
    and possibly:
    
    /home/igvc/gz_ws/ros2_ws/src/diff_drive_robot/diff_drive_robot/detect_line.py
    
    Common things to tune in autonomous_drive.launch.py:
    
    behavior_node parameters:
    
    'obstacle_distance': 0.6,
    'avoid_strength': 1.5,
    'front_avoid_strength': 1.0,
    'forward_speed_scale': 0.75,
    'critical_distance': 1.5,
    'use_map_avoidance': False,
    
    line detection parameters:
    
    'kp': 0.004,
    'base_speed': 1.4,
    'lookahead_gain': 1.5,
    'angle_gain': 0.5,
    'min_contour_area': 300,
    'obstacle_threshold': 0.5,
    
    waypoint parameters are in:
    
    config/waypoints.yaml
    
    15. Editing waypoints
    =====================
    
    Waypoints are here:
    
    /home/igvc/gz_ws/ros2_ws/src/diff_drive_robot/config/waypoints.yaml
    
    Current format:
    
    waypoints:
      - x: 1.0
        y: 0.0
      - x: 1.0
        y: 1.0
      - x: 0.0
        y: 1.0
    goal_tolerance: 0.3
    max_speed: 0.4
    max_angular_speed: 1.0
    yaw_gain: 1.5
    pause_at_goal: 2.0
    
    You can change the x/y coordinates to drive to different places.
    
    Then rebuild/source/relaunch.
    
    Because this package uses --symlink-install, YAML edits may be picked up more easily, but relaunching is still required because ROS nodes usually load parameters only at startup.
    
    16. Editing the robot model
    ===========================
    
    Robot model files are in:
    
    /home/igvc/gz_ws/ros2_ws/src/diff_drive_robot/urdf/
    
    The launch file uses:
    
    urdf/robot.urdf
    
    Edit this if you want to change:
    
    - robot size
    - wheel placement
    - lidar placement
    - camera placement
    - sensor properties
    - collision geometry
    - visual geometry
    - plugin settings
    
    After editing URDF:
    
    cd /home/igvc/gz_ws/ros2_ws
    colcon build --symlink-install --packages-select diff_drive_robot
    source install/setup.bash
    ros2 launch diff_drive_robot robot.launch.py
    
    17. Build/run loop
    ==================
    
    The everyday development loop is:
    
    Step 1: Edit source
    
    cd /home/igvc/gz_ws/ros2_ws/src/diff_drive_robot
    code .
    
    Step 2: Build
    
    cd /home/igvc/gz_ws/ros2_ws
    colcon build --symlink-install --packages-select diff_drive_robot
    
    Step 3: Source
    
    source install/setup.bash
    
    Step 4: Launch
    
    ros2 launch diff_drive_robot robot.launch.py
    
    Step 5: Watch Gazebo and RViz
    
    - Gazebo: robot/world/obstacles/physics
    - RViz: ROS topics/map/path/sensors
    
    Step 6: Debug topics
    
    ros2 topic list
    ros2 topic echo /scan
    ros2 topic echo /cmd_vel
    ros2 topic echo /diff_drive_controller/cmd_vel_unstamped
    ros2 node list
    ros2 node info /behavior_node
    
    Step 7: Stop with Ctrl+C
    
    Step 8: Edit again
    
    Repeat.
    
    18. Simulation vs real robot pipeline
    =====================================
    
    Simulation pipeline:
    
    Gazebo world
    → simulated sensors
    → ros_gz_bridge
    → ROS nodes
    → velocity command
    → Gazebo diff-drive controller
    → simulated robot moves
    
    Real robot pipeline:
    
    real sensors / GPS / camera / lidar
    → ROS nodes
    → behavior_node
    → velocity command
    → odrive_node
    → ODrive motor controller
    → physical wheels move
    
    In simulation, Gazebo replaces the physical world, motors, and sensors.
    
    On the real robot, Gazebo is not involved. You would instead launch hardware drivers and the autonomy stack.
    
    Important difference:
    
    Simulation:
    - Use Gazebo world files.
    - Obstacles are SDF models.
    - Sensors are simulated.
    - Robot movement is physics-based.
    
    Real robot:
    - Obstacles are real.
    - Sensors produce real data.
    - ODrive controls real motors.
    - You must be careful with e-stop and hardware safety.
    
    19. Which launch file should you use?
    =====================================
    
    For full simulation:
    
    ros2 launch diff_drive_robot robot.launch.py
    
    This is the main one.
    
    For autonomy stack only:
    
    ros2 launch diff_drive_robot autonomous_drive.launch.py
    
    Use this only if Gazebo/robot/sensors are already running or if you are running on the real robot with real sensors.
    
    20. Quick mental model
    ======================
    
    Think of the package like this:
    
    worlds/
      What the robot drives in.
    
    urdf/
      What the robot is.
    
    launch/
      What starts up.
    
    config/
      Parameters for controllers, SLAM, localization, bridge, waypoints.
    
    diff_drive_robot/
      The actual robot behavior code.
    
    rviz/
      How you visualize ROS data.
    
    The command:
    
    ros2 launch diff_drive_robot robot.launch.py
    
    does not open the code. It starts the robot system.
    
    The command:
    
    code /home/igvc/gz_ws/ros2_ws/src/diff_drive_robot
    
    opens the code folder, if VS Code is installed.
    
    Most common workflow:
    
    cd /home/igvc/gz_ws/ros2_ws/src/diff_drive_robot
    code .
    
    edit files
    
    cd /home/igvc/gz_ws/ros2_ws
    colcon build --symlink-install --packages-select diff_drive_robot
    source install/setup.bash
    ros2 launch diff_drive_robot robot.launch.py












