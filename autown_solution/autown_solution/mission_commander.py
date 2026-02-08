import rclpy
from rclpy.node import Node
from px4_msgs.msg import OffboardControlMode, TrajectorySetpoint, VehicleCommand, VehicleStatus
from sensor_msgs.msg import Image

class MissionCommander(Node):
    def __init__(self):
        super().__init__('mission_commander')

        # --- PX4 Publishers ---
        self.offboard_control_mode_publisher_ = self.create_publisher(
            OffboardControlMode, '/fmu/in/offboard_control_mode', 10)
        self.trajectory_setpoint_publisher_ = self.create_publisher(
            TrajectorySetpoint, '/fmu/in/trajectory_setpoint', 10)
        self.vehicle_command_publisher_ = self.create_publisher(
            VehicleCommand, '/fmu/in/vehicle_command', 10)
        
        # Timer for control loop (PX4 needs > 2Hz, we use 10Hz)
        self.timer = self.create_timer(0.1, self.cmdloop_callback)
        self.offboard_setpoint_counter_ = 0

    def cmdloop_callback(self):
        # 1. Arm and switch to Offboard mode after a few seconds
        if self.offboard_setpoint_counter_ == 10:
            self.publish_vehicle_command(VehicleCommand.VEHICLE_CMD_DO_SET_MODE, 1., 6.)
            self.arm()

        # 2. Publish Heartbeat (Required to keep Offboard mode active)
        self.publish_offboard_control_mode()
        
        # 3. Publish Trajectory (Example: Hover at 0,0, -2m)
        if self.offboard_setpoint_counter_ < 110: # First 10 seconds
            self.publish_trajectory_setpoint(0.0, 0.0, -3.0, 0.0) # Takeoff
        elif self.offboard_setpoint_counter_ < 210: # Next 10 seconds
            self.publish_trajectory_setpoint(5.0, 0.0, -3.0, 0.0) # Move Forward
        elif self.offboard_setpoint_counter_ < 310: # Next 10 seconds
            self.publish_trajectory_setpoint(5.0, 5.0, -3.0, 0.0) # Move Right
        elif self.offboard_setpoint_counter_ == 500:
            self.land()
            self.disarm()

        self.offboard_setpoint_counter_ += 1

    def arm(self):
        self.publish_vehicle_command(VehicleCommand.VEHICLE_CMD_COMPONENT_ARM_DISARM, 1.0)
        self.get_logger().info("Arm command sent")

    def publish_offboard_control_mode(self):
        msg = OffboardControlMode()
        msg.position = True
        msg.velocity = False
        msg.acceleration = False
        msg.attitude = False
        msg.body_rate = False
        msg.timestamp = int(self.get_clock().now().nanoseconds / 1000)
        self.offboard_control_mode_publisher_.publish(msg)

    def publish_trajectory_setpoint(self, x, y, z, yaw):
        msg = TrajectorySetpoint()
        msg.position = [x, y, z]
        msg.yaw = yaw
        msg.timestamp = int(self.get_clock().now().nanoseconds / 1000)
        self.trajectory_setpoint_publisher_.publish(msg)

    def publish_vehicle_command(self, command, param1=0.0, param2=0.0):
        msg = VehicleCommand()
        msg.param1 = param1
        msg.param2 = param2
        msg.command = command
        msg.target_system = 1
        msg.target_component = 1
        msg.source_system = 1
        msg.source_component = 1
        msg.from_external = True
        msg.timestamp = int(self.get_clock().now().nanoseconds / 1000)
        self.vehicle_command_publisher_.publish(msg)

    def land(self):
        self.publish_vehicle_command(VehicleCommand.VEHICLE_CMD_NAV_LAND)
        self.get_logger().info("Landing command sent")
    
    def disarm(self):
        self.publish_vehicle_command(VehicleCommand.VEHICLE_CMD_COMPONENT_ARM_DISARM, 0.0)
        self.get_logger().info("Disarm command sent")

def main(args=None):
    rclpy.init(args=args)
    node = MissionCommander()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()
