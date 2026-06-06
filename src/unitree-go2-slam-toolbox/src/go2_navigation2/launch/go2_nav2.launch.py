from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import DeclareLaunchArgument
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from ament_index_python.packages import get_package_share_directory
from launch.substitutions import LaunchConfiguration
from launch.conditions import IfCondition
import os

def generate_launch_description():
    get_nav2_pkg = get_package_share_directory("go2_navigation2")
    go2_description_pkg = get_package_share_directory("go2_description")
    go2_core_pkg = get_package_share_directory("go2_core")
    go2_driver_pkg = get_package_share_directory("go2_driver")

    declare_use_sim_time = DeclareLaunchArgument(
        'use_sim_time',
        default_value='false',
        description='Use simulation clock if true.',
    )
    declare_map = DeclareLaunchArgument(
        'map',
        default_value='/home/lyf/go2_maps/go2_latest_map.yaml',
        description='Full path to the map yaml loaded by map_server.',
    )
    declare_params_file = DeclareLaunchArgument(
        'params_file',
        default_value=os.path.join(get_nav2_pkg, 'config', 'nav2_params.yaml'),
        description='Full path to the Nav2 parameters file.',
    )
    declare_use_rviz = DeclareLaunchArgument(
        'use_rviz',
        default_value='true',
        description='Start RViz.',
    )
    declare_rviz_config = DeclareLaunchArgument(
        'rviz_config',
        default_value=os.path.join(get_nav2_pkg, 'rviz', 'go2_nav2.rviz'),
        description='Full path to the RViz config file.',
    )
    declare_enable_ekf = DeclareLaunchArgument(
        'enable_ekf',
        default_value='false',
        description='Start robot_localization EKF. Keep false when driver already publishes odom -> base_footprint.',
    )

    use_sim_time = LaunchConfiguration('use_sim_time')
    map_yaml_path = LaunchConfiguration('map')
    nav2_param_path = LaunchConfiguration('params_file')
    use_rviz = LaunchConfiguration('use_rviz')
    rviz_config = LaunchConfiguration('rviz_config')
    enable_ekf = LaunchConfiguration('enable_ekf')

    tf_remappings = [('/tf', 'tf'), ('/tf_static', 'tf_static')]

    map_server = Node(
        package='nav2_map_server',
        executable='map_server',
        name='map_server',
        output='screen',
        parameters=[{
            'yaml_filename': map_yaml_path,
            'use_sim_time': use_sim_time,
            'topic_name': 'map'
        }]
    )

    amcl = Node(
        package='nav2_amcl',
        executable='amcl',
        name='amcl',
        output='screen',
        parameters=[nav2_param_path, {'use_sim_time': use_sim_time}]
    )

    planner_server = Node(
        package='nav2_planner',
        executable='planner_server',
        name='planner_server',
        output='screen',
        parameters=[nav2_param_path, {'use_sim_time': use_sim_time}],
        remappings=tf_remappings,
    )

    controller_server = Node(
        package='nav2_controller',
        executable='controller_server',
        name='controller_server',
        output='screen',
        parameters=[nav2_param_path, {'use_sim_time': use_sim_time}],
        remappings=tf_remappings + [('cmd_vel', '/cmd_vel_nav')],
    )

    smoother_server = Node(
        package='nav2_smoother',
        executable='smoother_server',
        name='smoother_server',
        output='screen',
        parameters=[nav2_param_path, {'use_sim_time': use_sim_time}],
        remappings=tf_remappings,
    )

    behavior_server = Node(
        package='nav2_behaviors',
        executable='behavior_server',
        name='behavior_server',
        output='screen',
        parameters=[nav2_param_path, {'use_sim_time': use_sim_time}],
        remappings=tf_remappings + [('cmd_vel', '/cmd_vel_nav')],
    )

    bt_navigator = Node(
        package='nav2_bt_navigator',
        executable='bt_navigator',
        name='bt_navigator',
        output='screen',
        parameters=[nav2_param_path, {'use_sim_time': use_sim_time}],
        remappings=tf_remappings,
    )

    waypoint_follower = Node(
        package='nav2_waypoint_follower',
        executable='waypoint_follower',
        name='waypoint_follower',
        output='screen',
        parameters=[nav2_param_path, {'use_sim_time': use_sim_time}],
        remappings=tf_remappings,
    )

    lifecycle_manager_localization = Node(
        package='nav2_lifecycle_manager',
        executable='lifecycle_manager',
        name='lifecycle_manager_localization',
        output='screen',
        parameters=[{
            'use_sim_time': use_sim_time,
            'autostart': True,
            'node_names': ['map_server', 'amcl']
        }]
    )

    lifecycle_manager_navigation = Node(
        package='nav2_lifecycle_manager',
        executable='lifecycle_manager',
        name='lifecycle_manager_navigation',
        output='screen',
        parameters=[{
            'use_sim_time': use_sim_time,
            'autostart': True,
            'node_names': [
                'controller_server',
                'smoother_server',
                'planner_server',
                'behavior_server',
                'bt_navigator',
                'waypoint_follower',
            ]
        }]
    )

    # 里程计融合imu
    go2_robot_localization = IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(go2_core_pkg, "launch", "go2_robot_localization.launch.py")
            ),
            condition=IfCondition(enable_ekf)
        )
    
    rviz2 = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        arguments=['-d', rviz_config],
        parameters=[{'use_sim_time': use_sim_time}],
        output='screen',
        condition=IfCondition(use_rviz)
    )

    twist_bridge = Node(
        package='go2_twist_bridge',
        executable='twist_bridge',
        output='screen',
        remappings=[('cmd_vel', '/cmd_vel')],
    )

    safety_filter = Node(
        package='go2_navigation2',
        executable='go2_safety_filter',
        name='go2_safety_filter',
        output='screen',
        parameters=[{
            'front_angle_deg': 20.0,
            'stop_distance': 0.45,
            'slow_distance': 0.75,
            'min_valid_range': 0.05,
            'timeout_sec': 0.5,
            'allow_turn_when_blocked': False,
        }],
    )

    footprint_to_link = Node(
        package='go2_driver',
        executable='footprint_to_link',
        output='screen',
    )

    go2_driver = Node(
        package="go2_driver",
        executable="driver",
        output='screen',
        parameters=[os.path.join(go2_driver_pkg, 'params', 'driver.yaml')],
    )

    lowstate_to_imu = Node(
        package='go2_driver',
        executable='lowstate_to_imu',
        output='screen',
    )

    # 包含scan话题
    cloud_launch = IncludeLaunchDescription(
        launch_description_source=PythonLaunchDescriptionSource(
            launch_file_path=os.path.join(
                get_package_share_directory("go2_perception"),
                "launch",
                "go2_pointcloud.launch.py",
            )
        )
    )

    # 包含模型可视化
    go2_display_launch = IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(go2_description_pkg, "launch", "display.launch.py")
            ),
            launch_arguments=[("use_joint_state_publisher", "false")]
        )

    return LaunchDescription([
        declare_use_sim_time,
        declare_map,
        declare_params_file,
        declare_use_rviz,
        declare_rviz_config,
        declare_enable_ekf,
        safety_filter,
        twist_bridge,
        footprint_to_link,
        go2_driver,
        lowstate_to_imu,
        map_server,
        amcl,
        lifecycle_manager_localization,
        planner_server,
        controller_server,
        smoother_server,
        behavior_server,
        bt_navigator,
        waypoint_follower,
        lifecycle_manager_navigation,
        go2_robot_localization,
        rviz2,
        cloud_launch,
        go2_display_launch
    ])
