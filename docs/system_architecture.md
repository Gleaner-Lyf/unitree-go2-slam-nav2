# 系统架构

本文说明本项目的包结构、建图数据流、导航数据流、TF 树、主要话题和节点。

## 项目包结构

源码包位于：

```text
~/go2_ws_toolbox/src/unitree-go2-slam-toolbox/src
```

```text
base/go2_core
base/go2_driver
base/go2_twist_bridge
go2_description
go2_perception
go2_slam
go2_navigation2
```

各包职责：

| 包 | 作用 |
| --- | --- |
| `go2_core` | 总启动入口、键盘控制、EKF 启动入口 |
| `go2_driver` | Unitree 状态到 ROS 2 odom、TF、joint_states、imu |
| `go2_twist_bridge` | `/cmd_vel` 到 `/api/sport/request` |
| `go2_description` | Go2 URDF、mesh、robot_state_publisher |
| `go2_perception` | L1 点云累积、PointCloud2 到 LaserScan |
| `go2_slam` | slam_toolbox 建图 launch 和参数 |
| `go2_navigation2` | Nav2、AMCL、map_server、安全过滤器 |

## 建图数据流

```text
Unitree L1 LiDAR
  -> /utlidar/cloud_deskewed
  -> cloud_accumulation
  -> /utlidar/cloud_accumulated
  -> remap: /trans_cloud
  -> pointcloud_to_laserscan_node
  -> /scan
  -> slam_toolbox
  -> /map
```

建图主 launch：

```text
go2_core/launch/go2_start.launch.py
```

建图命令：

```bash
ros2 launch go2_core go2_start.launch.py use_slamtoolbox:=true enable_ekf:=false
```

建图时 `map -> odom` 由 `slam_toolbox` 发布。

## 导航数据流

```text
map_server
  -> /map
  -> AMCL
  -> map -> odom
  -> Nav2 planner/controller
  -> /cmd_vel_nav
  -> go2_safety_filter
  -> /cmd_vel
  -> go2_twist_bridge
  -> /api/sport/request
  -> Go2
```

导航主 launch：

```text
go2_navigation2/launch/go2_nav2.launch.py
```

导航命令：

```bash
ros2 launch go2_navigation2 go2_nav2.launch.py \
  map:=$HOME/go2_maps/go2_latest_map.yaml \
  use_rviz:=true \
  enable_ekf:=false
```

导航时 `map -> odom` 由 AMCL 发布。

## TF 树

目标 TF 树：

```text
map
  -> odom
    -> base_footprint
      -> base_link
        -> lidar
```

当前项目中：

- `odom -> base_footprint` 由 `go2_driver` 根据 `/utlidar/robot_pose` 发布
- `base_footprint -> base_link` 由 `go2_driver/footprint_to_link` 发布
- `base_link` 到 L1 相关 frame 来自 URDF 或静态外参
- 建图时 `map -> odom` 由 `slam_toolbox` 发布
- 导航时 `map -> odom` 由 AMCL 发布

检查：

```bash
ros2 run tf2_ros tf2_echo odom base_footprint
ros2 run tf2_ros tf2_echo map odom
ros2 run tf2_tools view_frames
```

## 主要话题

| 话题 | 类型/来源 | 作用 |
| --- | --- | --- |
| `/lf/lowstate` | Unitree underlay | Go2 底层状态 |
| `/lf/sportmodestate` | Unitree underlay | Go2 运动状态 |
| `/utlidar/cloud_deskewed` | Unitree L1 | 去畸变点云 |
| `/utlidar/robot_pose` | Unitree L1 | L1/机器人位姿输入 |
| `/utlidar/cloud_accumulated` | `cloud_accumulation` | 累积点云 |
| `/trans_cloud` | launch remap | 点云转 scan 输入 |
| `/scan` | `pointcloud_to_laserscan_node` | 2D LaserScan |
| `/odom` | `go2_driver` | 里程计 |
| `/map` | `slam_toolbox` 或 map_server | 栅格地图 |
| `/cmd_vel_nav` | Nav2 | 导航原始速度 |
| `/cmd_vel` | safety_filter 或 keyboard | 发给桥接器的速度 |
| `/api/sport/request` | `go2_twist_bridge` | Unitree 运动请求 |
| `/joint_states` | `go2_driver` | 关节状态 |
| `/imu` | `lowstate_to_imu` | 标准 IMU |

## 主要节点

| 节点/可执行文件 | 包 | 作用 |
| --- | --- | --- |
| `driver` | `go2_driver` | 发布 odom、TF、joint_states |
| `footprint_to_link` | `go2_driver` | 发布 `base_footprint -> base_link` |
| `lowstate_to_imu` | `go2_driver` | `/lf/lowstate` 转 `/imu` |
| `twist_bridge` | `go2_twist_bridge` | `/cmd_vel` 转 `/api/sport/request` |
| `cloud_accumulation` | `go2_perception` | 累积 L1 点云 |
| `pointcloud_to_laserscan_node` | `go2_perception` | 点云转 `/scan` |
| `slam_toolbox` | `slam_toolbox` | 在线建图 |
| `map_server` | `nav2_map_server` | 加载静态地图 |
| `amcl` | `nav2_amcl` | 基于地图定位 |
| `controller_server` | `nav2_controller` | 输出导航速度 |
| `go2_safety_filter` | `go2_navigation2` | 前方避障过滤 |
| `go2_keyboard_control` | `go2_core` | 键盘控制 |

## 建图模式和导航模式区别

建图模式：

- 启动 `slam_toolbox`
- 逐步生成 `/map`
- `slam_toolbox` 发布 `map -> odom`
- 用于探索环境和保存地图

导航模式：

- 启动 map_server 加载已有地图
- 启动 AMCL 进行定位
- AMCL 发布 `map -> odom`
- Nav2 根据目标点规划并输出 `/cmd_vel_nav`
- 安全过滤器输出 `/cmd_vel`

建图 launch 需要保持运行直到地图保存完成。保存地图应新开终端执行；保存完成后，导航前必须关闭建图 launch。不要同时运行建图模式和导航模式，因为 `slam_toolbox` 与 AMCL 会同时发布 `map -> odom`。
