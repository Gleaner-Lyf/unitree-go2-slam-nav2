# 08 常见问题排查

每个问题按“现象、可能原因、检查命令、解决办法”组织。排查前先确认已在终端执行：

```bash
cd ~/go2_ws_toolbox
source scripts/env_go2_robot.sh
```

## RViz 显示 Fixed Frame [map] does not exist

现象：

RViz 顶部或 Displays 中提示 `Fixed Frame [map] does not exist`。

可能原因：

- 建图时 `slam_toolbox` 未启动或未发布 `map`
- 导航时 map_server/AMCL 未正常启动
- `/scan` 或 `/odom` 缺失，导致 SLAM/AMCL 无法工作

检查命令：

```bash
ros2 topic list | grep map
ros2 run tf2_ros tf2_echo map odom
ros2 topic echo /scan --once --field header
ros2 topic echo /odom --once
```

解决办法：

- 建图时确认使用 `use_slamtoolbox:=true`
- 导航时确认地图 yaml 路径正确
- 先修复 `/scan`、`/odom` 和 TF

## /map 不显示

现象：

RViz 中没有地图，或 `ros2 topic echo /map --once` 没有输出。

可能原因：

- 建图模式下 `/scan` 无数据
- `slam_toolbox` 没有启动
- 导航模式下 map 文件路径错误
- map_server 未 active

检查命令：

```bash
ros2 topic echo /scan --once --field header
ros2 node list | grep slam
ros2 node list | grep map_server
ros2 lifecycle get /map_server
ls -lh ~/go2_maps/go2_latest_map.yaml
```

解决办法：

- 建图模式重新启动 `go2_start.launch.py use_slamtoolbox:=true`
- 导航模式传入正确 `map:=...yaml`
- 确认 `.yaml` 和 `.pgm` 在同一目录

## AMCL 不发布 map -> odom

现象：

导航时：

```bash
ros2 run tf2_ros tf2_echo map odom
```

没有输出。

可能原因：

- 没有在 RViz 中使用 `2D Pose Estimate`
- `/scan` 不正常
- `/map` 不正常
- AMCL 生命周期未 active
- scan 和地图差异太大

检查命令：

```bash
ros2 lifecycle get /amcl
ros2 topic echo /scan --once --field header
ros2 topic echo /map --once
ros2 topic echo /initialpose --once
```

解决办法：

- 在 RViz 中先点击 `2D Pose Estimate`
- 给出正确的初始位置和朝向
- 确认 `/scan` 与地图墙体大致重合
- 重新启动导航 launch

## /cmd_vel 没有订阅者

现象：

键盘控制发布了 `/cmd_vel`，但 Go2 不动。

可能原因：

- `go2_twist_bridge` 未启动
- 没有启动底层控制链路
- 环境没有 source 本项目 install

检查命令：

```bash
ros2 topic info /cmd_vel
ros2 node list | grep twist
ros2 topic echo /api/sport/request
```

解决办法：

启动底层链路：

```bash
ros2 launch go2_core go2_start.launch.py use_slamtoolbox:=false enable_ekf:=false
```

再启动键盘控制。

## 机器狗只转不走

现象：

Nav2 发送目标后 Go2 原地转向，但不向前走。

可能原因：

- 局部路径认为前方不可通行
- `/scan` 与地图不重合
- DWB 轨迹评分偏向旋转
- safety_filter 阻止正向速度

检查命令：

```bash
ros2 topic echo /cmd_vel_nav
ros2 topic echo /cmd_vel
ros2 topic echo /scan --once
ros2 run tf2_ros tf2_echo map odom
```

解决办法：

- 重新用 `2D Pose Estimate` 初始化 AMCL
- 检查 local costmap 中是否有虚假障碍
- 确认 safety_filter 不是 STOP
- 在较开阔环境测试

## 机器狗前倾但不走

现象：

Go2 收到前进命令后身体前倾，但没有迈步。

可能原因：

- 速度太低，不足以触发稳定步态
- Go2 当前状态或模式不适合运动
- 地面摩擦或姿态异常

检查命令：

```bash
ros2 topic echo /cmd_vel
ros2 topic echo /api/sport/request
```

解决办法：

- 使用当前项目默认约 `0.30 m/s` 的速度
- 先在空旷环境用键盘控制验证
- 保持遥控器可接管

## 0.15/0.20 不走，0.30 才能走

现象：

`0.15` 或 `0.20` 速度下只前倾，`0.30` 左右才正常行走。

可能原因：

- Go2 EDU 实机低速运动存在起步阈值
- Nav2 速度过低导致实际没有稳定步态

检查命令：

```bash
ros2 topic echo /cmd_vel
```

解决办法：

- 保持 DWB 当前参数：

```yaml
min_vel_x: 0.30
max_vel_x: 0.35
min_speed_xy: 0.30
max_speed_xy: 0.35
```

- 在狭窄环境中不要简单降到过低速度，应同时调 costmap 和安全距离

## 狭窄走廊不敢走

现象：

Go2 在走廊入口停住或绕不过去。

可能原因：

- `robot_radius` 偏大
- `inflation_radius` 偏大
- `/scan` 把墙体打得过厚
- AMCL 定位偏移

检查命令：

```bash
ros2 topic echo /scan --once
ros2 run tf2_ros tf2_echo map odom
```

解决办法：

- 适当减小 `inflation_radius`
- 适当减小 `robot_radius`
- 检查 `/scan` 和地图墙体是否重合
- 重新建图或重新初始化 AMCL

## 到达目标后还原地转向

现象：

机器人到达目标附近后持续转向。

可能原因：

- 目标朝向要求太严格
- DWB RotateToGoal 权重过高
- AMCL yaw 抖动

检查命令：

```bash
grep -n "yaw_goal_tolerance\\|RotateToGoal.scale" \
  ~/go2_ws_toolbox/src/unitree-go2-slam-toolbox/src/go2_navigation2/config/nav2_params.yaml
```

解决办法：

- 当前项目已将 `yaw_goal_tolerance` 设为 `3.14`
- 如仍转向，检查是否使用了正确的 `params_file`
- 重新初始化 AMCL

## /scan 和地图墙体不重合

现象：

RViz 中 LaserScan 与地图墙体明显错位。

可能原因：

- AMCL 初始位姿不准
- 地图质量差
- TF 外参或 odom 有误
- 机器人实际位置与地图环境不一致

检查命令：

```bash
ros2 run tf2_ros tf2_echo odom base_footprint
ros2 run tf2_ros tf2_echo map odom
ros2 topic echo /scan --once --field header
```

解决办法：

- 重新使用 `2D Pose Estimate`
- 在已知位置初始化
- 检查 L1 安装和 TF
- 必要时重新建图

## safety_filter 一直 STOP

现象：

`go2_safety_filter` 日志持续 `STOP`，`/cmd_vel_nav` 有速度但 `/cmd_vel` 为零。

可能原因：

- `/scan` 没有数据或超时
- 前方有近距离障碍
- scan 近距离噪声
- `stop_distance` 过大
- `front_angle_deg` 过大

检查命令：

```bash
ros2 topic echo /cmd_vel_nav
ros2 topic echo /cmd_vel
ros2 topic hz /scan
ros2 topic echo /scan --once
```

解决办法：

- 确认 `/scan` 持续发布
- 在 RViz 中查看前方是否有异常近点
- 清空前方障碍
- 调小 `stop_distance` 或 `front_angle_deg`

## Unitree 通信话题不存在

现象：

`ros2 topic list` 看不到 `/lf/lowstate`、`/lf/sportmodestate`、`/utlidar/cloud_deskewed`。

可能原因：

- Unitree underlay 未 source
- CycloneDDS 网卡错误
- Go2 未连接或未开机
- PC 与 Go2 网络不通

检查命令：

```bash
source ~/unitree_ros2/cyclonedds_ws/install/setup.bash
ros2 pkg list | grep unitree
ip addr
ros2 topic list
```

解决办法：

- 确认 Unitree underlay 已安装
- 如果脚本仍使用 `/home/lyf/...`，按自己的用户名和安装位置修改 `scripts/env_toolbox.sh`、`scripts/env_go2_robot.sh`、`scripts/build_toolbox.sh`
- 修改 `scripts/env_go2_robot.sh` 中的网卡名
- 检查网线和 Go2 状态
- 重新 source `scripts/env_go2_robot.sh`

## CycloneDDS 网卡配置错误

现象：

本项目包可以启动，但完全看不到 Go2 和 L1 的实时话题。

可能原因：

- `env_go2_robot.sh` 中仍是示例网卡 `enp129s0`
- 选择了 Wi-Fi 网卡
- 连接 Go2 的有线网卡名变化

检查命令：

```bash
ip addr
grep -n "NetworkInterface" ~/go2_ws_toolbox/scripts/env_go2_robot.sh
```

解决办法：

编辑：

```bash
gedit ~/go2_ws_toolbox/scripts/env_go2_robot.sh
```

把：

```xml
<NetworkInterface name="enp129s0" priority="default" multicast="default" />
```

改成真实有线网卡名，例如：

```xml
<NetworkInterface name="enp3s0" priority="default" multicast="default" />
```

然后重新打开终端或重新 source：

```bash
cd ~/go2_ws_toolbox
source scripts/env_go2_robot.sh
ros2 topic list
```
