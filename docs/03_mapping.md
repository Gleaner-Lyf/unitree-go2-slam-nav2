# 03 2D 建图

本文说明使用 Unitree L1 LiDAR 点云、`go2_perception` 和 `slam_toolbox` 进行 2D 建图。

## 启动建图

确认已连接 Go2，并且 `scripts/env_go2_robot.sh` 中网卡名已经改成你的真实网卡。

```bash
cd ~/go2_ws_toolbox
source scripts/env_go2_robot.sh
ros2 launch go2_core go2_start.launch.py use_slamtoolbox:=true enable_ekf:=false
```

建图 launch 需要持续运行。保存地图时请新开终端执行保存命令，不要先关闭建图终端。

该 launch 会启动：

- Go2 driver
- robot_state_publisher
- `go2_twist_bridge`
- L1 点云处理
- `slam_toolbox`
- RViz

## 建图数据流

当前项目实际使用的数据流：

```text
Unitree L1
  -> /utlidar/cloud_deskewed
  -> go2_perception/cloud_accumulation
  -> /utlidar/cloud_accumulated
  -> remap 为 /trans_cloud
  -> go2_perception/pointcloud_to_laserscan_node
  -> /scan
  -> slam_toolbox
  -> /map
```

注意：本项目当前订阅的是 `/utlidar/cloud_deskewed`。如果你参考其他教程看到 `/utlidar/cloud`，需要以本项目当前 launch 和源码为准。

## 关键 launch

主入口：

```text
go2_core/launch/go2_start.launch.py
```

SLAM 子入口：

```text
go2_slam/launch/go2_slamtoolbox.launch.py
```

点云处理子入口：

```text
go2_perception/launch/go2_pointcloud.launch.py
```

slam_toolbox 参数：

```text
go2_slam/config/mapper_params_online_async.yaml
```

关键参数：

```yaml
odom_frame: odom
map_frame: map
base_frame: base_footprint
scan_topic: /scan
mode: mapping
```

## 检查命令

检查 `/scan`：

```bash
ros2 topic echo /scan --once --field header
```

检查 `/map`：

```bash
ros2 topic echo /map --once
```

检查 `/odom`：

```bash
ros2 topic echo /odom --once
```

检查里程计 TF：

```bash
ros2 run tf2_ros tf2_echo odom base_footprint
```

检查建图 TF：

```bash
ros2 run tf2_ros tf2_echo map odom
```

建图时：

- `odom -> base_footprint` 由 `go2_driver` 发布
- `map -> odom` 由 `slam_toolbox` 发布

## RViz 观察

RViz 的 Fixed Frame 应设为：

```text
map
```

观察重点：

- RobotModel 是否显示
- LaserScan `/scan` 是否稳定
- Map `/map` 是否逐渐生成
- TF 是否连通
- 机器人在地图中的位姿是否随 Go2 移动而变化

如果 RViz 提示 `Fixed Frame [map] does not exist`，通常表示 `slam_toolbox` 尚未发布 `map` 或 `map -> odom`。先检查 `/scan`、`/odom` 和 `map -> odom`。

## 建图操作建议

- 先在开阔区域确认 `/scan` 正常
- 用低风险速度移动 Go2
- 走廊和房间边界尽量完整走一圈
- 避免快速旋转和剧烈晃动
- 地图稳定后再保存
