# 05 Nav2 自主导航

本文说明如何使用已保存地图启动 Nav2，并在 RViz 中完成 AMCL 初始化和目标点发送。

## 启动导航

启动导航前，必须先关闭建图 launch。导航时不要同时运行 `slam_toolbox` 建图模式，否则 `slam_toolbox` 和 AMCL 会同时发布 `map -> odom`。

```bash
cd ~/go2_ws_toolbox
source scripts/env_go2_robot.sh
ros2 launch go2_navigation2 go2_nav2.launch.py \
  map:=$HOME/go2_maps/go2_latest_map.yaml \
  use_rviz:=true \
  enable_ekf:=false
```

## go2_nav2.launch.py 参数

`go2_navigation2/launch/go2_nav2.launch.py` 支持：

- `map`：地图 yaml 完整路径。推荐显式传入 `map:=$HOME/go2_maps/go2_latest_map.yaml`
- `params_file`：Nav2 参数文件。默认 `go2_navigation2/config/nav2_params.yaml`
- `use_rviz`：是否启动 RViz。默认 `true`
- `rviz_config`：RViz 配置文件。默认 `go2_navigation2/rviz/go2_nav2.rviz`
- `enable_ekf`：是否启动 `robot_localization` EKF。默认 `false`
- `use_sim_time`：是否使用仿真时间。默认 `false`

示例：

```bash
ros2 launch go2_navigation2 go2_nav2.launch.py \
  map:=$HOME/go2_maps/go2_latest_map.yaml \
  params_file:=$HOME/go2_ws_toolbox/install/go2_navigation2/share/go2_navigation2/config/nav2_params.yaml \
  use_rviz:=true \
  enable_ekf:=false
```

如果你的工作区不在 `~/go2_ws_toolbox`，请把 `params_file` 路径改成自己的实际位置。

## 导航链路

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

关键点：

- `controller_server` 的 `cmd_vel` 被 remap 到 `/cmd_vel_nav`
- `go2_safety_filter` 根据 `/scan` 对 `/cmd_vel_nav` 做限速或停止
- `go2_twist_bridge` 将 `/cmd_vel` 转换成 Unitree `/api/sport/request`

## 为什么不能同时启动 slam_toolbox

建图模式：

```text
slam_toolbox 发布 map -> odom
```

导航模式：

```text
AMCL 发布 map -> odom
```

如果两者同时运行，会有两个节点争抢同一段 TF，造成定位跳变、地图和 scan 不重合、Nav2 行为异常。因此导航前应关闭建图 launch。

## RViz 操作顺序

在 RViz 中：

1. Fixed Frame 设为 `map`
2. 确认地图显示正常
3. 点击 `2D Pose Estimate`
4. 在地图上拖拽出 Go2 的当前真实位置和朝向
5. 等待 AMCL 收敛，确认 `/scan` 与地图墙体大致重合
6. 点击 `2D Goal Pose`
7. 在地图上拖拽目标位置和朝向

必须先 `2D Pose Estimate`，再 `2D Goal Pose`。未初始化 AMCL 时，Nav2 即使收到目标也可能无法正确规划或执行。

导航时 `map -> odom` 由 AMCL 发布。

## 检查命令

检查 AMCL 生命周期：

```bash
ros2 lifecycle get /amcl
```

检查 `map -> odom`：

```bash
ros2 run tf2_ros tf2_echo map odom
```

检查 Nav2 原始速度：

```bash
ros2 topic echo /cmd_vel_nav
```

检查安全过滤后速度：

```bash
ros2 topic echo /cmd_vel
```

检查发给 Unitree 的请求：

```bash
ros2 topic echo /api/sport/request
```

检查 `/scan`：

```bash
ros2 topic echo /scan --once --field header
```

## 当前 Go2 导航参数特点

当前 `nav2_params.yaml` 中 DWB 速度较保守但不低：

```yaml
min_vel_x: 0.30
max_vel_x: 0.35
min_speed_xy: 0.30
max_speed_xy: 0.35
```

这是因为 Go2 EDU 在较低速度如 `0.15` 或 `0.20` 时可能前倾但不迈步，`0.30` 左右更容易稳定运动。

目标角容差：

```yaml
yaw_goal_tolerance: 3.14
```

该设置减少到达目标后原地反复转向。不同场地仍需按实际表现调参。
