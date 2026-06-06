#!/usr/bin/env bash
set -e

cd /home/lyf/go2_ws_toolbox
source /opt/ros/humble/setup.bash
source /home/lyf/unitree_ros2/cyclonedds_ws/install/setup.bash
colcon build --symlink-install
