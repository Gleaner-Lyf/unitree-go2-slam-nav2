#!/usr/bin/env bash

source /opt/ros/humble/setup.bash
source /home/lyf/unitree_ros2/cyclonedds_ws/install/setup.bash
source /home/lyf/go2_ws_toolbox/install/setup.bash

export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp

# Change enp129s0 to the network interface connected to the Unitree Go2.
export CYCLONEDDS_URI='<CycloneDDS><Domain><General><Interfaces>
  <NetworkInterface name="enp129s0" priority="default" multicast="default" />
</Interfaces></General></Domain></CycloneDDS>'
