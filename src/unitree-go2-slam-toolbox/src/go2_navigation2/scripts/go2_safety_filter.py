#!/usr/bin/env python3

import math

import rclpy
from geometry_msgs.msg import Twist
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import LaserScan


class Go2SafetyFilter(Node):
    def __init__(self):
        super().__init__('go2_safety_filter')

        self.declare_parameter('front_angle_deg', 30.0)
        self.declare_parameter('stop_distance', 0.60)
        self.declare_parameter('slow_distance', 1.00)
        self.declare_parameter('min_valid_range', 0.05)
        self.declare_parameter('timeout_sec', 0.5)
        self.declare_parameter('allow_turn_when_blocked', False)

        self.front_angle_deg = self.get_parameter('front_angle_deg').value
        self.stop_distance = self.get_parameter('stop_distance').value
        self.slow_distance = self.get_parameter('slow_distance').value
        self.min_valid_range = self.get_parameter('min_valid_range').value
        self.timeout_sec = self.get_parameter('timeout_sec').value
        self.allow_turn_when_blocked = self.get_parameter('allow_turn_when_blocked').value

        if self.slow_distance <= self.stop_distance:
            self.get_logger().warn(
                'slow_distance must be greater than stop_distance; using stop_distance as hard stop only.'
            )

        self.front_min_range = None
        self.last_scan_time = None
        self.last_state = None

        self.cmd_pub = self.create_publisher(Twist, '/cmd_vel', 10)
        self.create_subscription(Twist, '/cmd_vel_nav', self.cmd_callback, 10)
        self.create_subscription(
            LaserScan,
            '/scan',
            self.scan_callback,
            qos_profile_sensor_data,
        )
        self.create_timer(0.1, self.timeout_check)

        self.get_logger().info(
            'go2_safety_filter started: /cmd_vel_nav + /scan -> /cmd_vel'
        )

    def scan_callback(self, msg):
        front_angle_rad = math.radians(float(self.front_angle_deg))
        valid_ranges = []

        for index, range_value in enumerate(msg.ranges):
            if not math.isfinite(range_value) or range_value < self.min_valid_range:
                continue

            angle = msg.angle_min + index * msg.angle_increment
            if abs(self.normalize_angle(angle)) <= front_angle_rad:
                valid_ranges.append(range_value)

        self.front_min_range = min(valid_ranges) if valid_ranges else None
        self.last_scan_time = self.get_clock().now()

    def cmd_callback(self, msg):
        filtered_cmd, state = self.filter_cmd(msg)
        self.log_state_change(state)
        self.cmd_pub.publish(filtered_cmd)

    def timeout_check(self):
        if self.is_scan_timeout():
            self.log_state_change('SCAN_TIMEOUT')
            self.cmd_pub.publish(Twist())

    def filter_cmd(self, cmd):
        if self.is_scan_timeout():
            return Twist(), 'SCAN_TIMEOUT'

        if self.front_min_range is None:
            return self.stop_cmd(cmd), 'STOP'

        if self.front_min_range < self.stop_distance:
            return self.stop_cmd(cmd), 'STOP'

        if self.front_min_range < self.slow_distance:
            return self.slow_cmd(cmd), 'SLOW'

        return cmd, 'CLEAR'

    def stop_cmd(self, cmd):
        if self.allow_turn_when_blocked:
            filtered = Twist()
            filtered.linear.x = min(cmd.linear.x, 0.0)
            filtered.linear.y = cmd.linear.y
            filtered.linear.z = cmd.linear.z
            filtered.angular.x = cmd.angular.x
            filtered.angular.y = cmd.angular.y
            filtered.angular.z = cmd.angular.z
            return filtered

        return Twist()

    def slow_cmd(self, cmd):
        filtered = Twist()
        filtered.linear.x = cmd.linear.x
        filtered.linear.y = cmd.linear.y
        filtered.linear.z = cmd.linear.z
        filtered.angular.x = cmd.angular.x
        filtered.angular.y = cmd.angular.y
        filtered.angular.z = cmd.angular.z

        if cmd.linear.x > 0.0 and self.slow_distance > self.stop_distance:
            scale = (
                (self.front_min_range - self.stop_distance)
                / (self.slow_distance - self.stop_distance)
            )
            scale = max(0.0, min(1.0, scale))
            filtered.linear.x = min(cmd.linear.x * scale, 0.15)

        return filtered

    def is_scan_timeout(self):
        if self.last_scan_time is None:
            return True

        age = (self.get_clock().now() - self.last_scan_time).nanoseconds * 1e-9
        return age > self.timeout_sec

    def log_state_change(self, state):
        if state == self.last_state:
            return

        self.last_state = state
        if state in ('CLEAR', 'SCAN_TIMEOUT'):
            self.get_logger().info(state)
        elif state == 'SLOW':
            self.get_logger().warn(
                f'SLOW: front_min_range={self.format_range(self.front_min_range)} m'
            )
        elif state == 'STOP':
            self.get_logger().warn(
                f'STOP: front_min_range={self.format_range(self.front_min_range)} m'
            )

    @staticmethod
    def normalize_angle(angle):
        return math.atan2(math.sin(angle), math.cos(angle))

    @staticmethod
    def format_range(range_value):
        if range_value is None:
            return 'none'
        return f'{range_value:.2f}'


def main(args=None):
    rclpy.init(args=args)
    node = Go2SafetyFilter()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
