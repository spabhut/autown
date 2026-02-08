#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy, DurabilityPolicy

from px4_msgs.msg import VehicleOdometry
from nav_msgs.msg import Odometry
from geometry_msgs.msg import TransformStamped
from tf2_ros import TransformBroadcaster
import numpy as np

class PX4OdomBridge(Node):
    def __init__(self):
        super().__init__('px4_odom_bridge')

        # 1. Configure QoS to match PX4's "Best Effort"
        qos_profile = QoSProfile(
            reliability=ReliabilityPolicy.BEST_EFFORT,
            durability=DurabilityPolicy.TRANSIENT_LOCAL,
            history=HistoryPolicy.KEEP_LAST,
            depth=1
        )

        # 2. Subscribe to PX4 Odometry
        self.sub = self.create_subscription(
            VehicleOdometry,
            '/fmu/out/vehicle_odometry',
            self.listener_callback,
            qos_profile
        )

        # 3. Publishers
        self.odom_pub = self.create_publisher(Odometry, '/odom', 10)
        self.tf_broadcaster = TransformBroadcaster(self)

        self.get_logger().info("PX4 to ROS Odometry Bridge Started (Fixed Float Types)...")

    def listener_callback(self, msg):
        timestamp = self.get_clock().now().to_msg()

        # --- FIX: Cast everything to float() explicitly ---
        # PX4 sends `numpy.float32`, but ROS 2 needs standard `float`
        
        # Position Conversion (NED -> ENU)
        # X (ROS) = Y (PX4)
        # Y (ROS) = X (PX4)
        # Z (ROS) = -Z (PX4)
        pos_x = float(msg.position[1])
        pos_y = float(msg.position[0])
        pos_z = float(-msg.position[2])

        # Orientation Conversion (NED -> ENU)
        # PX4 Quaternion is [w, x, y, z]
        # We need to map it to ENU. 
        # A common visualization mapping is: x=y, y=x, z=-z, w=w
        q_x = float(msg.q[2])
        q_y = float(msg.q[1])
        q_z = float(-msg.q[3])
        q_w = float(msg.q[0])

        # Velocity Conversion (Optional, but good for completeness)
        vel_x = float(msg.velocity[1])
        vel_y = float(msg.velocity[0])
        vel_z = float(-msg.velocity[2])
        
        # Angular Velocity
        ang_vel_x = float(msg.angular_velocity[1])
        ang_vel_y = float(msg.angular_velocity[0])
        ang_vel_z = float(-msg.angular_velocity[2])

        # --- PART A: Publish /odom Topic ---
        odom_msg = Odometry()
        odom_msg.header.stamp = timestamp
        odom_msg.header.frame_id = 'odom'
        odom_msg.child_frame_id = 'base_link'

        # Pose
        odom_msg.pose.pose.position.x = pos_x
        odom_msg.pose.pose.position.y = pos_y
        odom_msg.pose.pose.position.z = pos_z
        odom_msg.pose.pose.orientation.x = q_x
        odom_msg.pose.pose.orientation.y = q_y
        odom_msg.pose.pose.orientation.z = q_z
        odom_msg.pose.pose.orientation.w = q_w

        # Twist (Velocity)
        odom_msg.twist.twist.linear.x = vel_x
        odom_msg.twist.twist.linear.y = vel_y
        odom_msg.twist.twist.linear.z = vel_z
        odom_msg.twist.twist.angular.x = ang_vel_x
        odom_msg.twist.twist.angular.y = ang_vel_y
        odom_msg.twist.twist.angular.z = ang_vel_z
        
        self.odom_pub.publish(odom_msg)

        # --- PART B: Broadcast TF for RViz ---
        t = TransformStamped()
        t.header.stamp = timestamp
        t.header.frame_id = 'odom'
        t.child_frame_id = 'base_link'

        t.transform.translation.x = pos_x
        t.transform.translation.y = pos_y
        t.transform.translation.z = pos_z
        t.transform.rotation.x = q_x
        t.transform.rotation.y = q_y
        t.transform.rotation.z = q_z
        t.transform.rotation.w = q_w

        self.tf_broadcaster.sendTransform(t)

def main(args=None):
    rclpy.init(args=args)
    node = PX4OdomBridge()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()