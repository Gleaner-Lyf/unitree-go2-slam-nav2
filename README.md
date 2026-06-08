# Unitree Go2 EDU + L1 LiDAR ROS 2 SLAM Toolbox

本项目面向 Ubuntu 22.04 + ROS 2 Humble 用户，提供 Unitree Go2 EDU 与 Unitree L1 LiDAR 的 2D 建图、地图保存、Nav2 自主导航、键盘控制和前向安全避障示例。

## 项目目的与最终效果

项目目的：

本项目旨在基于 Unitree Go2 EDU 和 Unitree L1 LiDAR，搭建一套可复现的 ROS 2 Humble 2D SLAM 与 Nav2 自主导航流程。项目重点不是重新设计底层机器人控制，而是把 Go2 的通信、雷达点云处理、2D 建图、地图保存、AMCL 定位、Nav2 导航、速度桥接和前向安全过滤整合成一个完整工作空间，方便学习、复现和二次开发。

最终效果：

按照本文档完成配置后，理论上可以实现：

- 连接 Unitree Go2 EDU 真机并读取 L1 LiDAR、里程计和机器人状态；
- 将 L1 3D 点云处理为 2D LaserScan；
- 使用 slam_toolbox 完成室内 2D 建图；
- 使用 nav2_map_server 保存地图；
- 使用 map_server + AMCL + Nav2 在已保存地图上进行自主导航；
- 在 RViz 中通过 2D Pose Estimate 初始化定位，通过 2D Goal Pose 发送目标点；
- 通过 `go2_twist_bridge` 将 Nav2 输出速度转换为 Unitree `/api/sport/request`；
- 通过 `go2_safety_filter` 在前方障碍物过近时进行减速或停止；
- 使用自定义键盘控制节点进行基础运动测试。

适用范围：

- 适合学习 Unitree Go2 ROS 2 开发、2D SLAM、Nav2、自主导航流程的用户；
- 适合在室内平整环境下做教学、实验和二次开发；
- 测试硬件为 Unitree Go2 EDU + Unitree L1 LiDAR + Ubuntu 22.04 + ROS 2 Humble。

当前限制：

- 本项目不是商用品质导航系统；
- 不包含 Unitree 官方通信 underlay，需要用户单独安装、准备并 source；
- 导航效果受地图质量、地面环境、网络配置、AMCL 初始化、Nav2 参数影响；
- 当前主要验证 2D 室内建图和短距离自主导航；
- 复杂动态避障、长距离稳定导航、室外导航、3D SLAM 尚未作为主要目标。

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

路径提示：脚本默认使用 `~/go2_ws_toolbox` 和 `~/unitree_ros2/cyclonedds_ws`。如果你的工作区或 Unitree underlay 安装位置不同，请修改 `scripts/env_toolbox.sh`、`scripts/env_go2_robot.sh`、`scripts/build_toolbox.sh` 中的 `WORKSPACE_DIR` 和 `UNITREE_WS` 默认值，或在执行前导出同名环境变量。

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

## 效果预览

![RViz 建图结果总览](docs/images/mapping_result_overview.png)

该图展示了 slam_toolbox 建图后的 RViz 地图效果。白色区域表示已探索可通行区域，黑色边界表示墙体或障碍物，灰绿色区域表示未知区域。

![Nav2 代价地图示意](docs/images/navigation_costmap_example.png)

该图展示了导航模式下的 Nav2 costmap。彩色区域是 inflation layer，表示障碍物周围的代价膨胀区域，机器人规划路径时会尽量远离高代价区域。

## 克隆仓库

从零开始时，先把仓库克隆到 `~/go2_ws_toolbox`：

```bash
cd ~
git clone https://github.com/Gleaner-Lyf/unitree-go2-slam-nav2.git go2_ws_toolbox
cd ~/go2_ws_toolbox
```

## 最小复现流程

下面命令是本项目的最小闭环流程：编译工作空间、source 环境、建图、保存地图、启动导航。

### Step 1：安装 ROS 2 依赖

```bash
sudo apt update
sudo apt install \
  python3-colcon-common-extensions \
  ros-humble-navigation2 \
  ros-humble-nav2-bringup \
  ros-humble-nav2-map-server \
  ros-humble-nav2-amcl \
  ros-humble-nav2-controller \
  ros-humble-nav2-planner \
  ros-humble-nav2-bt-navigator \
  ros-humble-nav2-behaviors \
  ros-humble-nav2-lifecycle-manager \
  ros-humble-slam-toolbox \
  ros-humble-robot-localization \
  ros-humble-rmw-cyclonedds-cpp \
  ros-humble-rviz2 \
  ros-humble-tf2-tools \
  ros-humble-laser-geometry \
  ros-humble-message-filters \
  ros-humble-tf2-sensor-msgs \
  ros-humble-xacro \
  ros-humble-robot-state-publisher \
  ros-humble-joint-state-publisher
```

### Step 2：克隆并编译 Unitree underlay

本仓库不包含 `unitree_go` / `unitree_api`。先安装 Unitree ROS 2 通信 underlay：

```bash
cd ~
git clone https://github.com/unitreerobotics/unitree_ros2.git
cd ~/unitree_ros2/cyclonedds_ws
source /opt/ros/humble/setup.bash
colcon build --symlink-install
source ~/unitree_ros2/cyclonedds_ws/install/setup.bash
ros2 pkg list | grep unitree
ros2 pkg list | grep rmw_cyclonedds_cpp
```

如果 `cyclonedds_ws/src` 中缺少 `cyclonedds` 或 `rmw_cyclonedds`，请按 Unitree 官方 ROS 2 SDK / `unitree_ros2` 教程补齐。本机检查到的来源包括：

```text
https://github.com/unitreerobotics/unitree_ros2
https://github.com/eclipse-cyclonedds/cyclonedds
https://github.com/ros2/rmw_cyclonedds
```

### Step 3：克隆本项目

```bash
cd ~
git clone https://github.com/Gleaner-Lyf/unitree-go2-slam-nav2.git go2_ws_toolbox
cd ~/go2_ws_toolbox
```

### Step 4：修改机器人网卡名

编辑：

```bash
gedit ~/go2_ws_toolbox/scripts/env_go2_robot.sh
```

把 `enp129s0` 改成你电脑连接 Go2 的真实有线网卡名。查看网卡：

```bash
ip addr
```

### Step 5：终端 1 编译本项目

```bash
cd ~/go2_ws_toolbox
bash scripts/build_toolbox.sh
source scripts/env_go2_robot.sh
```

### Step 6：连接检查

```bash
cd ~/go2_ws_toolbox
source scripts/env_go2_robot.sh
ros2 topic list
ros2 topic echo /lf/lowstate --once
ros2 topic echo /utlidar/cloud_deskewed --once --field header
```

### Step 7：终端 1 启动建图并保持运行

建图 launch 需要保持运行，直到地图保存完成。

```bash
cd ~/go2_ws_toolbox
source scripts/env_go2_robot.sh
ros2 launch go2_core go2_start.launch.py use_slamtoolbox:=true enable_ekf:=false
```

### Step 8：终端 2 保存地图

新开终端执行保存命令，不要关闭终端 1 的建图 launch。

```bash
cd ~/go2_ws_toolbox
source scripts/env_go2_robot.sh
mkdir -p ~/go2_maps
ros2 run nav2_map_server map_saver_cli -f ~/go2_maps/go2_latest_map
```

### Step 9：终端 1 关闭建图后启动导航

地图保存完成后，先在终端 1 停止建图 launch，再启动导航。不要让 `slam_toolbox` 和 AMCL 同时发布 `map -> odom`。

```bash
cd ~/go2_ws_toolbox
source scripts/env_go2_robot.sh
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
  python3-colcon-common-extensions \
  ros-humble-navigation2 \
  ros-humble-nav2-bringup \
  ros-humble-nav2-map-server \
  ros-humble-nav2-amcl \
  ros-humble-nav2-controller \
  ros-humble-nav2-planner \
  ros-humble-nav2-bt-navigator \
  ros-humble-nav2-behaviors \
  ros-humble-nav2-lifecycle-manager \
  ros-humble-slam-toolbox \
  ros-humble-robot-localization \
  ros-humble-rmw-cyclonedds-cpp \
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

## Step 1: 安装 Unitree ROS 2 underlay

本仓库不包含 Unitree 官方通信包，也不会自动安装：

- `unitree_go`
- `unitree_api`

用户必须先完成 Unitree ROS 2 通信包安装和编译。本文默认 underlay 路径为：

```bash
~/unitree_ros2/cyclonedds_ws/install/setup.bash
```

推荐从 Unitree 官方仓库克隆：

```bash
cd ~
git clone https://github.com/unitreerobotics/unitree_ros2.git
cd ~/unitree_ros2/cyclonedds_ws
```

编译 underlay：

```bash
source /opt/ros/humble/setup.bash
colcon build --symlink-install
```

source underlay 并验证：

```bash
source ~/unitree_ros2/cyclonedds_ws/install/setup.bash
ros2 pkg list | grep unitree
ros2 pkg list | grep rmw_cyclonedds_cpp
```

如果你的 Unitree underlay 不在 `~/unitree_ros2/cyclonedds_ws`，需要修改：

- `scripts/env_toolbox.sh`
- `scripts/env_go2_robot.sh`
- `scripts/build_toolbox.sh`

这三个脚本里的默认变量：

```bash
WORKSPACE_DIR="$HOME/go2_ws_toolbox"
UNITREE_WS="$HOME/unitree_ros2/cyclonedds_ws"
```

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

## 连接检查

确认 Unitree underlay、网卡和 CycloneDDS 配置后，连接 Go2 并在终端执行：

```bash
cd ~/go2_ws_toolbox
source scripts/env_go2_robot.sh
ros2 topic list
ros2 topic echo /lf/lowstate --once
ros2 topic echo /utlidar/cloud_deskewed --once --field header
```

如果看不到 `/lf/lowstate` 或 `/utlidar/cloud_deskewed`，优先检查 Unitree underlay 是否已安装、`env_go2_robot.sh` 中的网卡名是否正确、Go2 是否已开机并通过网线连接。

## 编译工作空间

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

如果你的路径不是默认值，请先修改脚本中的 `WORKSPACE_DIR` 和 `UNITREE_WS`，再执行。

编译完成后，每个新终端都需要 source 环境。连接真实 Go2 时使用：

```bash
cd ~/go2_ws_toolbox
source scripts/env_go2_robot.sh
```

只做本地查看或不连接机器人时可使用：

```bash
cd ~/go2_ws_toolbox
source scripts/env_toolbox.sh
```

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
