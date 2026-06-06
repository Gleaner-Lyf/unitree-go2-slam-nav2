# 04 保存地图

本文说明如何把 `slam_toolbox` 生成的 `/map` 保存为 Nav2 可加载的地图文件。

## 保存命令

建图 launch 正在运行且 `/map` 正常发布时，在新终端执行。不要先关闭建图 launch，否则保存命令可能拿不到当前地图。

```bash
cd ~/go2_ws_toolbox
source scripts/env_go2_robot.sh
mkdir -p ~/go2_maps
ros2 run nav2_map_server map_saver_cli -f ~/go2_maps/go2_latest_map
```

## 输出文件

保存成功后会生成：

```text
~/go2_maps/go2_latest_map.yaml
~/go2_maps/go2_latest_map.pgm
```

其中：

- `.yaml`：地图元信息，包括分辨率、原点、阈值和图像文件名
- `.pgm`：栅格地图图像

## 检查地图文件

```bash
ls -lh ~/go2_maps/go2_latest_map.*
cat ~/go2_maps/go2_latest_map.yaml
```

期望看到类似：

```yaml
image: go2_latest_map.pgm
resolution: 0.05
origin: [...]
occupied_thresh: ...
free_thresh: ...
```

如果没有生成文件，检查：

```bash
ros2 topic echo /map --once
ros2 node list | grep map
```

## 默认地图路径

本文推荐的默认地图路径是：

```text
~/go2_maps/go2_latest_map.yaml
```

使用 `~` 或 `$HOME` 时，推荐在命令行显式传入：

```bash
map:=$HOME/go2_maps/go2_latest_map.yaml
```

## 导航时指定地图

保存完成后，启动导航前请先关闭建图 launch，避免 `slam_toolbox` 和 AMCL 同时发布 `map -> odom`。

```bash
cd ~/go2_ws_toolbox
source scripts/env_go2_robot.sh
ros2 launch go2_navigation2 go2_nav2.launch.py \
  map:=$HOME/go2_maps/go2_latest_map.yaml \
  use_rviz:=true \
  enable_ekf:=false
```

如果你保存了其他地图，例如：

```text
~/go2_maps/lab_1f.yaml
```

则启动：

```bash
ros2 launch go2_navigation2 go2_nav2.launch.py \
  map:=$HOME/go2_maps/lab_1f.yaml \
  use_rviz:=true \
  enable_ekf:=false
```
