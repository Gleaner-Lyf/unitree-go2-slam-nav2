#!/usr/bin/env python3
"""Unitree Go2 keyboard teleop node.

This node publishes one Twist message for each key press. It deliberately does
not keep publishing motion commands while no key is pressed.
"""

import argparse
import select
import sys
import termios
import tty

import rclpy
from geometry_msgs.msg import Twist
from rclpy.node import Node


DEFAULT_LINEAR_SPEED = 0.30
DEFAULT_ANGULAR_SPEED = 0.70
MAX_LINEAR_SPEED = 0.60
MAX_ANGULAR_SPEED = 1.00
SPEED_STEP = 0.05


HELP_TEXT = """
Unitree Go2 专用键盘控制节点

发布话题: /cmd_vel
消息类型: geometry_msgs/msg/Twist

按键说明:
  w  前进
  s  后退
  a  左移
  d  右移
  q  原地左转
  e  原地右转
  x  停止
  空格  急停
  + 或 =  提高速度
  - 或 _  降低速度
  r  恢复默认速度
  Ctrl+C  退出并发布停止

安全说明:
  每次按键只发布一次 Twist；没有按键时不会持续发布运动指令。
"""


class Go2KeyboardControl(Node):
    def __init__(self) -> None:
        super().__init__("go2_keyboard_control")
        self.publisher = self.create_publisher(Twist, "/cmd_vel", 10)
        self.linear_speed = DEFAULT_LINEAR_SPEED
        self.angular_speed = DEFAULT_ANGULAR_SPEED

    def make_twist(self, linear_x: float = 0.0, linear_y: float = 0.0, angular_z: float = 0.0) -> Twist:
        msg = Twist()
        msg.linear.x = float(linear_x)
        msg.linear.y = float(linear_y)
        msg.angular.z = float(angular_z)
        return msg

    def publish_twist(self, msg: Twist) -> None:
        self.publisher.publish(msg)

    def publish_stop(self, label: str | None = "停止") -> None:
        self.publish_twist(self.make_twist())
        if label:
            self.get_logger().info(label)

    def increase_speed(self) -> None:
        self.linear_speed = min(MAX_LINEAR_SPEED, self.linear_speed + SPEED_STEP)
        self.angular_speed = min(MAX_ANGULAR_SPEED, self.angular_speed + SPEED_STEP)
        self.print_speed("提高速度")

    def decrease_speed(self) -> None:
        self.linear_speed = max(0.0, self.linear_speed - SPEED_STEP)
        self.angular_speed = max(0.0, self.angular_speed - SPEED_STEP)
        self.print_speed("降低速度")

    def reset_speed(self) -> None:
        self.linear_speed = DEFAULT_LINEAR_SPEED
        self.angular_speed = DEFAULT_ANGULAR_SPEED
        self.print_speed("恢复默认速度")

    def print_speed(self, label: str = "当前速度") -> None:
        self.get_logger().info(
            f"{label}: linear_speed={self.linear_speed:.2f}, "
            f"angular_speed={self.angular_speed:.2f}"
        )

    def handle_key(self, key: str) -> None:
        # Unitree SportClient Move uses x/y/z for forward/lateral/yaw velocity.
        actions = {
            "w": ("前进", self.make_twist(linear_x=self.linear_speed)),
            "s": ("后退", self.make_twist(linear_x=-self.linear_speed)),
            "a": ("左移", self.make_twist(linear_y=self.linear_speed)),
            "d": ("右移", self.make_twist(linear_y=-self.linear_speed)),
            "q": ("原地左转", self.make_twist(angular_z=self.angular_speed)),
            "e": ("原地右转", self.make_twist(angular_z=-self.angular_speed)),
            "x": ("停止", self.make_twist()),
            " ": ("急停", self.make_twist()),
        }

        if key in actions:
            label, msg = actions[key]
            self.publish_twist(msg)
            if key in ("x", " "):
                self.get_logger().info(label)
        elif key in ("+", "="):
            self.increase_speed()
        elif key in ("-", "_"):
            self.decrease_speed()
        elif key == "r":
            self.reset_speed()
        else:
            self.get_logger().info(f"未绑定按键: {repr(key)}")


def read_key(timeout: float = 0.1) -> str | None:
    ready, _, _ = select.select([sys.stdin], [], [], timeout)
    if not ready:
        return None
    return sys.stdin.read(1)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Unitree Go2 专用键盘控制节点，按一次键发布一次 /cmd_vel。"
    )
    parser.add_argument(
        "--show-help-and-exit",
        action="store_true",
        help="打印键盘控制说明后退出，不启动 ROS 节点。",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    print(HELP_TEXT)
    if args.show_help_and_exit:
        return

    rclpy.init()
    node = Go2KeyboardControl()
    node.print_speed()

    old_settings = termios.tcgetattr(sys.stdin)
    try:
        tty.setcbreak(sys.stdin.fileno())
        while rclpy.ok():
            rclpy.spin_once(node, timeout_sec=0.0)
            key = read_key()
            if key is not None:
                node.handle_key(key)
    except KeyboardInterrupt:
        pass
    finally:
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
        if rclpy.ok():
            node.publish_stop(label=None)
            rclpy.spin_once(node, timeout_sec=0.1)
            node.get_logger().info("已发布停止指令，退出")
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
