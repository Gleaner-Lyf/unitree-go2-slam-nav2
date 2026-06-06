# Go2 Nav2 maps

The navigation launch defaults to the external map saved by the SLAM workflow:

```bash
/home/lyf/go2_maps/go2_latest_map.yaml
```

Override it at launch time when needed:

```bash
ros2 launch go2_navigation2 go2_nav2.launch.py map:=/absolute/path/to/map.yaml
```

Do not start slam_toolbox together with this navigation launch. During navigation,
AMCL is the only node in this package that should publish `map -> odom`.
