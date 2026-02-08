import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, ExecuteProcess, TimerAction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node

def generate_launch_description():
    # --- Configuration ---
    # UPDATED: Points to ~/Documents/autown/PX4-Autopilot
    px4_dir = os.path.join(os.getenv('HOME'), 'Documents', 'autown', 'PX4-Autopilot')

    qgc_path = os.path.join(os.getenv('HOME'), 'Documents', 'autown', 'QGroundControl-x86_64.AppImage')

    rviz_config_file = os.path.join(os.getenv('HOME'), 'Documents', 'autown', 'autown_solution', 'src', 'autown_solution', 'rviz', 'autown.rviz')


    # --- 1. QGroundControl (New!) ---
    qgc_process = ExecuteProcess(
        cmd=[qgc_path],
        output='screen'
    )


    # --- 2. MicroXRCEAgent (Communication) ---
    micro_xrce_agent = ExecuteProcess(
        cmd=['MicroXRCEAgent', 'udp4', '-p', '8888'],
        output='screen'
    )

# --- 3. PX4 SITL Simulation (Modified to open new window) ---
    px4_sitl = ExecuteProcess(
        # We wrap the command in gnome-terminal
        cmd=[
            'gnome-terminal', '--', 
            'make', 'px4_sitl', 'gz_x500_depth'
        ],
        cwd=px4_dir,
        additional_env={
            'PX4_GZ_WORLD': 'maze_harmonic',
            'PX4_GZ_MODEL_POSE': '-5,-5,6'
        },
        output='screen'
    )

    # --- 4. ROS - GZ Bridge ---
    ros_gz_bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        name='ros_gz_bridge',
        arguments=[
            '/world/maze_harmonic/model/x500_depth_0/link/camera_link/sensor/IMX214/image@sensor_msgs/msg/Image[gz.msgs.Image',
            '/depth_camera@sensor_msgs/msg/Image[gz.msgs.Image',
            '/world/maze_harmonic/model/x500_depth_0/link/camera_link/sensor/IMX214/camera_info@sensor_msgs/msg/CameraInfo[gz.msgs.CameraInfo',
            '/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock'
        ],
        output='screen'
    )
    
    odom_converter = Node(
		package='autown_solution',      # Your package name
		executable='odom_converter',   # The name you defined in setup.py
		name='odom_converter',
		output='screen',
		parameters=[{'use_sim_time': True}]
    )

    camera_tf = Node(
            package='tf2_ros',
            executable='static_transform_publisher',
            name='camera_static_tf',
            arguments = [
                '--x', '0.15',
                '--y', '0.03',
                '--z', '0.242',
                '--roll', '0',
                '--pitch', '0.733',
                '--yaw', '0',
                '--frame-id', 'base_link',
                '--child-frame-id', 'camera_link'
            ],
            # If using simulation time, uncomment the line below
            # parameters=[{'use_sim_time': True}]
    )

    rviz = Node(
            package='rviz2',
            executable='rviz2',
            name='rviz2',
            arguments=['-d', rviz_config_file],
            output='screen'
    )

    return LaunchDescription([
        qgc_process,
        micro_xrce_agent,
        px4_sitl,
        ros_gz_bridge,
        odom_converter,
        camera_tf,
        rviz
    ])
