# 06 键盘控制

本文说明如何使用本项目自带键盘控制节点控制 Go2。

## 启动底层控制链路

键盘控制节点只发布 `/cmd_vel`。要让 Go2 真正收到运动请求，必须先启动底层驱动和 `go2_twist_bridge`。

推荐启动：

```bash
cd ~/go2_ws_toolbox
source scripts/env_go2_robot.sh
ros2 launch go2_core go2_start.launch.py use_slamtoolbox:=false enable_ekf:=false
```

该命令会启动：

- Go2 driver
- `go2_twist_bridge`
- TF 和模型发布
- 点云处理
- RViz

## 启动键盘控制

新终端：

```bash
cd ~/go2_ws_toolbox
source scripts/env_go2_robot.sh
ros2 run go2_core go2_keyboard_control
```

## 按键表

| 按键 | 功能 |
| --- | --- |
| `w` | 前进 |
| `s` | 后退 |
| `a` | 左移 |
| `d` | 右移 |
| `q` | 原地左转 |
| `e` | 原地右转 |
| `x` | 停止 |
| 空格 | 急停 |
| `+` 或 `=` | 提高速度 |
| `-` 或 `_` | 降低速度 |
| `r` | 恢复默认速度 |

默认速度：

- 线速度 `0.30`
- 角速度 `0.70`

键盘节点每按一次键只发布一次 `/cmd_vel`，不会在松手后持续发布运动指令。

## 不要和 Nav2 同时抢 /cmd_vel

Nav2 导航链路中：

```text
Nav2 -> /cmd_vel_nav -> go2_safety_filter -> /cmd_vel -> go2_twist_bridge
```

键盘控制会直接发布：

```text
go2_keyboard_control -> /cmd_vel -> go2_twist_bridge
```

因此键盘控制和 Nav2 不应该同时运行，否则会抢占 `/cmd_vel`，造成运动指令混乱，也可能绕过导航安全过滤逻辑。

## 急停命令

在键盘控制窗口按：

```text
空格
```

或：

```text
x
```

也可以单独发布零速度：

```bash
ros2 topic pub --once /cmd_vel geometry_msgs/msg/Twist '{}'
```

注意：该命令只是 ROS 速度层面的停止，不替代 Unitree 官方遥控器或实体急停措施。实机测试时应保持遥控器可接管。

## 检查链路

检查 `/cmd_vel` 是否有人订阅：

```bash
ros2 topic info /cmd_vel
```

检查 Unitree 请求：

```bash
ros2 topic echo /api/sport/request
```
