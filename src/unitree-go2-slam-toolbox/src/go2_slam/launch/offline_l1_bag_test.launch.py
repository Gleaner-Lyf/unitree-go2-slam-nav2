from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory
import os


def generate_launch_description():
    go2_description_pkg = get_package_share_directory("go2_description")
    go2_slam_pkg = get_package_share_directory("go2_slam")

    use_sim_time = LaunchConfiguration("use_sim_time")
    cloud_topic = LaunchConfiguration("cloud_topic")
    cloud_frame = LaunchConfiguration("cloud_frame")
    publish_static_odom = LaunchConfiguration("publish_static_odom")

    use_sim_time_arg = DeclareLaunchArgument(
        "use_sim_time",
        default_value="true",
    )
    cloud_topic_arg = DeclareLaunchArgument(
        "cloud_topic",
        default_value="/unilidar/cloud",
    )
    cloud_frame_arg = DeclareLaunchArgument(
        "cloud_frame",
        default_value="unilidar_lidar",
    )
    publish_static_odom_arg = DeclareLaunchArgument(
        "publish_static_odom",
        default_value="true",
    )

    robot_description_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(go2_description_pkg, "launch", "display.launch.py")
        ),
        launch_arguments=[
            ("use_joint_state_publisher", "false"),
        ],
    )

    base_footprint_to_base_link = Node(
        package="tf2_ros",
        executable="static_transform_publisher",
        arguments=["0", "0", "0.30", "0", "0", "0", "base_footprint", "base_link"],
    )

    base_link_to_bag_lidar = Node(
        package="tf2_ros",
        executable="static_transform_publisher",
        arguments=["0.28945", "0", "-0.046825", "0", "2.8782", "0", "base_link", cloud_frame],
    )

    static_odom_to_base_footprint = Node(
        package="tf2_ros",
        executable="static_transform_publisher",
        arguments=["0", "0", "0", "0", "0", "0", "odom", "base_footprint"],
        condition=IfCondition(publish_static_odom),
    )

    pointcloud_to_laserscan = Node(
        package="go2_perception",
        executable="pointcloud_to_laserscan_node",
        name="pointcloud_to_laserscan_node",
        remappings=[
            ("cloud_in", cloud_topic),
            ("scan", "/scan"),
        ],
        parameters=[{
            "use_sim_time": use_sim_time,
            "target_frame": "base_footprint",
            "transform_tolerance": 0.05,
            "min_height": 0.1,
            "max_height": 0.5,
            "angle_min": -3.14,
            "angle_max": 3.14,
            "angle_increment": 0.0087,
            "scan_time": 0.1,
            "range_min": 0.0,
            "range_max": 10.0,
            "use_inf": True,
            "inf_epsilon": 1.0,
        }],
    )

    slam_toolbox_config = os.path.join(
        go2_slam_pkg,
        "config",
        "mapper_params_online_async.yaml",
    )
    slam_toolbox_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                get_package_share_directory("slam_toolbox"),
                "launch",
                "online_async_launch.py",
            )
        ),
        launch_arguments=[
            ("slam_params_file", slam_toolbox_config),
            ("use_sim_time", use_sim_time),
        ],
    )

    return LaunchDescription([
        use_sim_time_arg,
        cloud_topic_arg,
        cloud_frame_arg,
        publish_static_odom_arg,
        robot_description_launch,
        base_footprint_to_base_link,
        base_link_to_bag_lidar,
        static_odom_to_base_footprint,
        pointcloud_to_laserscan,
        slam_toolbox_launch,
    ])
