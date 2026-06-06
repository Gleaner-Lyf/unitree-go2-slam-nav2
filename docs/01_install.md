# 01 安装与编译

本文说明从 Ubuntu 22.04 + ROS 2 Humble 环境准备到本项目编译的最小步骤。

## 系统要求

- Ubuntu 22.04
- ROS 2 Humble
- 已安装 `colcon`
- 已准备 Unitree Go2 EDU 与 Unitree L1 LiDAR

确认 ROS 2：

```bash
source /opt/ros/humble/setup.bash
ros2 --version
```

## 安装 apt 依赖

```bash
sudo apt update
sudo apt install \
  ros-humble-navigation2 \
  ros-humble-nav2-bringup \
  ros-humble-slam-toolbox \
  ros-humble-robot-localization \
  ros-humble-rviz2 \
  ros-humble-tf2-tools \
  ros-humble-laser-geometry \
  ros-humble-message-filters \
  ros-humble-tf2-sensor-msgs \
  ros-humble-xacro \
  ros-humble-robot-state-publisher \
  ros-humble-joint-state-publisher
```

如果系统没有 colcon：

```bash
sudo apt install python3-colcon-common-extensions
```

## Unitree ROS 2 underlay

本项目依赖 Unitree ROS 2 通信 underlay，而不是仓库自带通信包。推荐把 Unitree underlay 放在：

```bash
~/unitree_ros2/cyclonedds_ws/install/setup.bash
```

注意：当前项目脚本可能仍写着作者本机路径 `/home/lyf/unitree_ros2/cyclonedds_ws/install/setup.bash`。如果你的用户名或安装位置不同，需要修改 `scripts/env_toolbox.sh`、`scripts/env_go2_robot.sh`、`scripts/build_toolbox.sh`。

该 underlay 需要提供：

- `unitree_go`
- `unitree_api`
- `rmw_cyclonedds_cpp`
- CycloneDDS 相关包

检查：

```bash
ls ~/unitree_ros2/cyclonedds_ws/install/setup.bash
source ~/unitree_ros2/cyclonedds_ws/install/setup.bash
ros2 pkg list | grep unitree
```

期望至少看到：

```text
unitree_api
unitree_go
```

如果没有这些包，请先参考 Unitree 官方教程安装并编译 Unitree ROS 2 underlay。

## 编译本项目

推荐使用项目脚本：

```bash
cd ~/go2_ws_toolbox
bash scripts/build_toolbox.sh
```

等价手动命令：

```bash
cd ~/go2_ws_toolbox
source /opt/ros/humble/setup.bash
source ~/unitree_ros2/cyclonedds_ws/install/setup.bash
colcon build --symlink-install
```

编译完成后加载环境：

```bash
cd ~/go2_ws_toolbox
source scripts/env_toolbox.sh
```

如果要连接真实 Go2，请使用：

```bash
cd ~/go2_ws_toolbox
source scripts/env_go2_robot.sh
```

## 常见编译问题

### 找不到 unitree_go 或 unitree_api

现象：

```text
Could not find a package configuration file provided by "unitree_go"
```

可能原因：

- 没有安装 Unitree ROS 2 underlay
- 编译前没有 source underlay
- underlay 路径不是脚本中写的路径
- 脚本还保留作者本机路径 `/home/lyf/...`

检查命令：

```bash
source ~/unitree_ros2/cyclonedds_ws/install/setup.bash
ros2 pkg list | grep unitree
```

解决办法：

- 先安装并编译 Unitree ROS 2 underlay
- 确认 `scripts/build_toolbox.sh` 中 underlay 路径符合你的电脑
- 同步检查 `scripts/env_toolbox.sh` 和 `scripts/env_go2_robot.sh` 中的路径

### 找不到 slam_toolbox 或 Nav2

检查：

```bash
ros2 pkg list | grep slam_toolbox
ros2 pkg list | grep nav2_map_server
```

解决：

```bash
sudo apt update
sudo apt install ros-humble-slam-toolbox ros-humble-navigation2 ros-humble-nav2-bringup
```

### 找不到 laser_geometry、message_filters、tf2_sensor_msgs

解决：

```bash
sudo apt install \
  ros-humble-laser-geometry \
  ros-humble-message-filters \
  ros-humble-tf2-sensor-msgs
```

### 构建后 ros2 找不到本项目包

检查是否 source：

```bash
cd ~/go2_ws_toolbox
source install/setup.bash
ros2 pkg list | grep go2
```

如果仍找不到，重新编译：

```bash
cd ~/go2_ws_toolbox
source /opt/ros/humble/setup.bash
source ~/unitree_ros2/cyclonedds_ws/install/setup.bash
colcon build --symlink-install
source install/setup.bash
```
