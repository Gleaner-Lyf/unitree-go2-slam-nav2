# 07 安全过滤器

本文说明 `go2_safety_filter` 的作用、话题链路、默认参数和调试方法。

## 作用

脚本路径：

```text
go2_navigation2/scripts/go2_safety_filter.py
```

`go2_safety_filter` 位于 Nav2 与 Go2 控制桥之间，用 `/scan` 检查机器人前方障碍距离，对 Nav2 输出的速度进行过滤。

导航链路：

```text
Nav2 controller / behavior
  -> /cmd_vel_nav
  -> go2_safety_filter
  -> /cmd_vel
  -> go2_twist_bridge
  -> /api/sport/request
```

## 订阅和发布

订阅：

```text
/cmd_vel_nav
/scan
```

发布：

```text
/cmd_vel
```

## 默认 launch 参数

`go2_nav2.launch.py` 中当前覆盖参数：

```yaml
front_angle_deg: 20.0
stop_distance: 0.45
slow_distance: 0.75
min_valid_range: 0.05
timeout_sec: 0.5
allow_turn_when_blocked: false
```

脚本自身默认值略保守：

```yaml
front_angle_deg: 30.0
stop_distance: 0.60
slow_distance: 1.00
```

实际通过 `go2_nav2.launch.py` 启动导航时，以 launch 中的参数为准。

## 安全逻辑

`CLEAR`：

- 前方最近有效障碍距离大于 `slow_distance`
- 原样发布 Nav2 速度

`SLOW`：

- 前方距离小于 `slow_distance` 但大于 `stop_distance`
- 只对正向 `linear.x` 限速
- 当前实现会把正向速度按距离缩放，并限制到最高 `0.15`

`STOP`：

- 前方距离小于 `stop_distance`
- 或前方没有有效 scan 点
- 发布零速度

`SCAN_TIMEOUT`：

- 超过 `timeout_sec` 没收到 `/scan`
- 发布零速度

当 `allow_turn_when_blocked` 为 `false` 时，前方阻挡会同时禁止转向和侧向运动，直接输出零速度。

## 如何测试

启动导航后，在不同终端观察：

```bash
ros2 topic echo /cmd_vel_nav
```

```bash
ros2 topic echo /cmd_vel
```

```bash
ros2 topic echo /api/sport/request
```

对比：

- `/cmd_vel_nav` 有速度，`/cmd_vel` 为零：安全过滤器正在 STOP 或 SCAN_TIMEOUT
- `/cmd_vel_nav` 有较大正向速度，`/cmd_vel` 正向速度变小：处于 SLOW
- `/cmd_vel` 有输出但 `/api/sport/request` 没有：检查 `go2_twist_bridge`

检查 `/scan`：

```bash
ros2 topic echo /scan --once --field header
```

## 如果一直 STOP

现象：

```text
go2_safety_filter 日志持续 STOP
```

可能原因：

- `/scan` 没有数据
- `/scan` 超时
- 前方确实有障碍物
- L1 点云中近距离噪声太多
- `stop_distance` 设置过大
- `front_angle_deg` 覆盖范围太宽
- `/scan` 坐标或 TF 异常

检查命令：

```bash
ros2 topic hz /scan
ros2 topic echo /scan --once
ros2 run tf2_ros tf2_echo odom base_footprint
ros2 run tf2_ros tf2_echo map odom
```

解决办法：

- 确认 `/scan` 持续发布
- 清理机器人前方障碍
- 在 RViz 中查看 `/scan` 是否有贴近机器人前方的异常点
- 适当减小 `stop_distance`
- 适当减小 `front_angle_deg`
- 检查 L1 点云高度过滤参数
- 确认 TF 树连通
