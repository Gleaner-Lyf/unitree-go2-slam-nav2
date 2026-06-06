# 02 网络与 CycloneDDS 配置

本文说明 PC 与 Unitree Go2 的网络连接、CycloneDDS 网卡配置和通信话题验证。

## 连接方式

推荐使用有线网络连接：

```text
Ubuntu 22.04 PC  <--- 网线 --->  Unitree Go2 EDU
```

确保：

- Go2 已开机
- L1 LiDAR 已正常工作
- PC 的有线网口连接到 Go2 网络
- PC 没有把 CycloneDDS 绑定到错误网卡

## 查看网卡

在 PC 上执行：

```bash
ip addr
```

常见网卡名示例：

```text
enp3s0
enp129s0
eth0
enx001122334455
wlp0s20f3
```

通常用于 Go2 通信的是有线网卡，不是 Wi-Fi 网卡。你需要找到连接 Go2 后处于 UP 状态并有对应 IP 的接口。

## 修改 env_go2_robot.sh

真实机器人通信环境脚本：

```bash
~/go2_ws_toolbox/scripts/env_go2_robot.sh
```

当前脚本中有示例网卡名：

```xml
<NetworkInterface name="enp129s0" priority="default" multicast="default" />
```

`enp129s0` 必须改成你电脑连接 Go2 的真实网卡名。

编辑：

```bash
gedit ~/go2_ws_toolbox/scripts/env_go2_robot.sh
```

例如你的网卡是 `enp3s0`，则改为：

```xml
<NetworkInterface name="enp3s0" priority="default" multicast="default" />
```

保存后，在每个连接 Go2 的新终端执行：

```bash
cd ~/go2_ws_toolbox
source scripts/env_go2_robot.sh
```

不要把这些内容写入 `~/.bashrc`，建议按需在终端手动 source。

## CycloneDDS 配置解释

`env_go2_robot.sh` 做了几件事：

```bash
source /opt/ros/humble/setup.bash
source ~/unitree_ros2/cyclonedds_ws/install/setup.bash
source ~/go2_ws_toolbox/install/setup.bash

export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
export CYCLONEDDS_URI='...'
```

如果你的项目或 Unitree underlay 不在 `~/go2_ws_toolbox`、`~/unitree_ros2`，请先修改 `scripts/env_go2_robot.sh` 中对应路径。

含义：

- 加载 ROS 2 Humble
- 加载 Unitree ROS 2 underlay
- 加载本项目 overlay
- 指定 ROS 2 使用 CycloneDDS
- 指定 CycloneDDS 只在连接 Go2 的网卡上通信

如果网卡名错了，常见表现是看不到 `/lf/lowstate`、`/lf/sportmodestate`、`/utlidar/cloud_deskewed` 等 Unitree 话题。

## 验证通信话题

先加载环境：

```bash
cd ~/go2_ws_toolbox
source scripts/env_go2_robot.sh
```

查看话题：

```bash
ros2 topic list
```

检查 Go2 底层状态：

```bash
ros2 topic echo /lf/lowstate --once
```

检查 L1 点云 header：

```bash
ros2 topic echo /utlidar/cloud_deskewed --once --field header
```

如果以上命令没有输出，优先检查：

- Go2 是否开机
- 网线是否连接正确
- `env_go2_robot.sh` 中网卡名是否正确
- Unitree underlay 是否已 source
- 防火墙或网络配置是否阻断 DDS 通信
