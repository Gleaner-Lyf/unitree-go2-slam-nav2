# Unitree Go2 EDU + L1 LiDAR ROS 2 SLAM Toolbox

本项目面向 Ubuntu 22.04 + ROS 2 Humble 用户，提供 Unitree Go2 EDU 与 Unitree L1 LiDAR 的 2D 建图、地图保存、Nav2 自主导航、键盘控制和前向安全避障示例。

本仓库只包含 Go2 上层 ROS 2 功能包，不包含 Unitree 官方通信 underlay。使用前必须先准备并 source Unitree ROS 2 underlay。

外部参考教程：

- https://ztl3106742440-hub.github.io/go2-tutorial/04-perception/11-slam-2d/

## 硬件环境

- Unitree Go2 EDU
- Unitree L1 LiDAR
- Ubuntu 22.04 PC
- PC 与 Go2 之间的有线网络连接

建议先在空旷、平整、无人员靠近的环境中测试建图、键盘控制和导航。

## 软件环境

- Ubuntu 22.04
- ROS 2 Humble
- CycloneDDS / `rmw_cyclonedds_cpp`
- Unitree ROS 2 underlay，例如：

```bash
~/unitree_ros2/cyclonedds_ws/install/setup.bash
```

该 underlay 应提供 `unitree_go`、`unitree_api` 等通信消息包。本项目不会自动安装这些包。

注意：仓库中的 `scripts/env_toolbox.sh`、`scripts/env_go2_robot.sh`、`scripts/build_toolbox.sh` 目前使用了作者本机路径，例如 `/home/lyf/go2_ws_toolbox` 和 `/home/lyf/unitree_ros2`。如果你的用户名、工作区位置或 Unitree underlay 安装位置不同，需要先按自己的电脑修改这三个脚本。

## 项目结构

```text
~/go2_ws_toolbox
├── README.md
├── docs
├── scripts
│   ├── build_toolbox.sh
│   ├── env_go2_robot.sh
│   └── env_toolbox.sh
└── src/unitree-go2-slam-toolbox/src
    ├── base/go2_core
    ├── base/go2_driver
    ├── base/go2_twist_bridge
    ├── go2_description
    ├── go2_perception
    ├── go2_slam
    └── go2_navigation2
```

主要包说明：

- `go2_core`：总启动入口、键盘控制、可选 EKF。
- `go2_driver`：发布 `/odom`、`odom -> base_footprint`、`/joint_states`、`/imu`。
- `go2_twist_bridge`：将 `/cmd_vel` 转为 `/api/sport/request`。
- `go2_description`：URDF 和模型显示。
- `go2_perception`：L1 点云累积和 PointCloud2 到 LaserScan 转换。
- `go2_slam`：slam_toolbox 建图启动和参数。
- `go2_navigation2`：Nav2、AMCL、map_server、安全过滤器和导航启动。

## 最小复现流程

下面命令是本项目的最小闭环流程：编译、建图、保存地图、启动导航。

```bash
cd ~/go2_ws_toolbox
source scripts/env_go2_robot.sh
bash scripts/build_toolbox.sh

ros2 launch go2_core go2_start.launch.py use_slamtoolbox:=true enable_ekf:=false

mkdir -p ~/go2_maps
ros2 run nav2_map_server map_saver_cli -f ~/go2_maps/go2_latest_map

ros2 launch go2_navigation2 go2_nav2.launch.py \
  map:=$HOME/go2_maps/go2_latest_map.yaml \
  use_rviz:=true \
  enable_ekf:=false
```

流程提醒：

- 建图 launch 需要保持运行，直到地图保存完成。
- 保存地图需要新开一个终端执行，不要关闭正在建图的终端。
- 导航前必须关闭建图 launch。建图模式下 `slam_toolbox` 发布 `map -> odom`，导航模式下 AMCL 发布 `map -> odom`；两者同时运行会造成 TF 冲突。

## 依赖安装

先安装 ROS 2 apt 依赖：

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

然后确认 Unitree ROS 2 underlay 已经存在：

```bash
ls ~/unitree_ros2/cyclonedds_ws/install/setup.bash
```

如果该文件不存在，需要先按 Unitree 官方 ROS 2 通信教程安装并编译 underlay。

详细安装说明见 [docs/01_install.md](docs/01_install.md)。

## CycloneDDS 网卡配置

机器人通信使用 `scripts/env_go2_robot.sh`。该脚本中当前网卡名是示例值：

```xml
<NetworkInterface name="enp129s0" priority="default" multicast="default" />
```

`enp129s0` 必须改成你电脑上连接 Go2 的真实网卡名。先查看网卡：

```bash
ip addr
```

找到有线连接 Go2 的接口，例如 `enp3s0`、`eth0`、`enx...`，再编辑：

```bash
gedit ~/go2_ws_toolbox/scripts/env_go2_robot.sh
```

网络配置和通信检查见 [docs/02_network_setup.md](docs/02_network_setup.md)。

## 编译方法

```bash
cd ~/go2_ws_toolbox
source /opt/ros/humble/setup.bash
source ~/unitree_ros2/cyclonedds_ws/install/setup.bash
colcon build --symlink-install
```

也可以使用项目脚本：

```bash
cd ~/go2_ws_toolbox
bash scripts/build_toolbox.sh
```

如果脚本仍指向 `/home/lyf/...`，请先修改脚本中的工作区路径和 Unitree underlay 路径，再执行。

## 建图启动

启动建图：

```bash
cd ~/go2_ws_toolbox
source scripts/env_go2_robot.sh
ros2 launch go2_core go2_start.launch.py use_slamtoolbox:=true enable_ekf:=false
```

建图数据流：

```text
Unitree L1
  -> /utlidar/cloud_deskewed
  -> /trans_cloud
  -> /scan
  -> slam_toolbox
  -> /map
```

详细说明见 [docs/03_mapping.md](docs/03_mapping.md)。

## 地图保存

建图满意后，保持建图 launch 运行，并在新终端执行：

```bash
cd ~/go2_ws_toolbox
source scripts/env_go2_robot.sh
mkdir -p ~/go2_maps
ros2 run nav2_map_server map_saver_cli -f ~/go2_maps/go2_latest_map
```

输出文件：

```text
~/go2_maps/go2_latest_map.yaml
~/go2_maps/go2_latest_map.pgm
```

详细说明见 [docs/04_save_map.md](docs/04_save_map.md)。

## 导航启动

确认地图已保存后，必须先关闭建图 launch，再启动导航：

```bash
cd ~/go2_ws_toolbox
source scripts/env_go2_robot.sh
ros2 launch go2_navigation2 go2_nav2.launch.py \
  map:=$HOME/go2_maps/go2_latest_map.yaml \
  use_rviz:=true \
  enable_ekf:=false
```

导航链路：

```text
map_server -> AMCL -> Nav2
  -> /cmd_vel_nav
  -> go2_safety_filter
  -> /cmd_vel
  -> go2_twist_bridge
  -> /api/sport/request
  -> Go2
```

在 RViz 中必须先使用 `2D Pose Estimate` 初始化 AMCL，再使用 `2D Goal Pose` 发送目标点。`map -> odom` 由 AMCL 发布。

详细说明见 [docs/05_navigation.md](docs/05_navigation.md)。

## 键盘控制

先启动底层控制链路：

```bash
cd ~/go2_ws_toolbox
source scripts/env_go2_robot.sh
ros2 launch go2_core go2_start.launch.py use_slamtoolbox:=false enable_ekf:=false
```

再在新终端启动键盘控制：

```bash
cd ~/go2_ws_toolbox
source scripts/env_go2_robot.sh
ros2 run go2_core go2_keyboard_control
```

键盘控制会直接发布 `/cmd_vel`，不要和 Nav2 导航同时使用，避免抢占速度指令。详细说明见 [docs/06_keyboard_control.md](docs/06_keyboard_control.md)。

## 安全过滤器

导航模式中，Nav2 不直接发布 `/cmd_vel`，而是发布 `/cmd_vel_nav`。`go2_safety_filter` 同时读取 `/cmd_vel_nav` 和 `/scan`，根据前方障碍距离输出安全后的 `/cmd_vel`。

默认 launch 参数：

```yaml
front_angle_deg: 20.0
stop_distance: 0.45
slow_distance: 0.75
```

详细说明见 [docs/07_safety_filter.md](docs/07_safety_filter.md)。

## 常见问题

常见问题包括：

- RViz 显示 `Fixed Frame [map] does not exist`
- `/map` 不显示
- AMCL 不发布 `map -> odom`
- `/cmd_vel` 没有订阅者
- 机器狗只转不走或前倾但不走
- `safety_filter` 一直 STOP
- Unitree 通信话题不存在
- CycloneDDS 网卡配置错误

排查手册见 [docs/08_troubleshooting.md](docs/08_troubleshooting.md)。

## 系统架构

包结构、话题、节点、TF 树和建图/导航模式区别见 [docs/system_architecture.md](docs/system_architecture.md)。
