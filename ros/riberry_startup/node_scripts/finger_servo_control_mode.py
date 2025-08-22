#!/usr/bin/env python3

from kxr_controller.kxr_interface import KXRROSRobotInterface
from kxr_controller.msg import ServoOnOff
import rospy
from skrobot.model import RobotModel
from skrobot.utils.urdf import no_mesh_load_mode
from std_msgs.msg import Int32

from riberry.com.base import PacketType
from riberry.mode import Mode
from riberry.utils.ros.namespace import get_base_namespace


class FingerServoControlMode(Mode):
    def __init__(self):
        super().__init__()
        self.finger_to_joints = {"thumb": ["THUMB0", "THUMB1", "THUMB2"],
                                 "index": ["INDEX0", "INDEX1", "INDEX2", "INDEX3"],
                                 "middle": ["MIDDLE0", "MIDDLE1", "MIDDLE2", "MIDDLE3"],
                                 "ring": ["RING0", "RING1", "RING2", "RING3"],
                                 "little": ["LITTLE0", "LITTLE1", "LITTLE2", "LITTLE3"]}
        self.finger_states = {"thumb": False, "index": False, "middle": False, "ring": False, "little": False}
        self.fingers = ["thumb", "index", "middle", "ring", "little"]
        self.target_finger_idx = 0
        # Create timer callback first to send string even if self.ri cannot be generated
        self.init_finished = False
        rospy.Timer(rospy.Duration(0.1), self.timer_callback)

        # Create robot model to control servo
        robot_model = RobotModel()
        namespace = get_base_namespace()
        with no_mesh_load_mode():
            robot_model.load_urdf_from_robot_description(
                namespace + "/robot_description_viz")
        self.ri = KXRROSRobotInterface(
            robot_model, namespace=namespace, controller_timeout=60.0
        )

        # Button and mode callback
        rospy.Subscriber(
            "atom_s3_button_state", Int32, callback=self.button_cb, queue_size=1
        )

        self.init_finished = True

    def button_cb(self, msg):
        """
        When AtomS3 is FingerServoControlMode and single-click pressed,
        toggle servo control.
        """
        if self.mode == "FingerServoControlMode" and msg.data == 1:
            self.target_finger_idx = (self.target_finger_idx + 1) % len(self.target_finger_idx)

        elif self.mode == "FingerServoControlMode" and msg.data == 2:
            rospy.loginfo(
                "AtomS3 is FingerServoControlMode and double-click-pressed."
                + " Toggle servo control."
            )
            self.toggle_servo_on_off(self.fingers[self.target_finger_idx])

    def toggle_servo_on_off(self, finger_name):
        """
        If one of the servos is on, turn the entire servo off.
        If all of the servos is off, turn the entire servo on.
        """
        if self.ri is None:
            rospy.logwarn("KXRROSRobotInterface instance is not created.")
            return
        if self.finger_states[finger_name] is True:
            self.ri.servo_off(self.finger_to_joints[finger_name])
            self.finger_states[finger_name] = False
        else:
            self.ri.servo_on(self.finger_to_joints[finger_name])
            self.finger_states[finger_name] = True

    def timer_callback(self, event):
        if self.mode != "FingerServoControlMode":
            return
        # Send message on AtomS3 LCD
        target_name = self.fingers[self.target_finger_idx]
        if self.init_finished is False:
            sent_str = chr(PacketType.SERVO_CONTROL_MODE)
            sent_str += "Finger Servo Control Mode\n\n"
            sent_str += "Wait for servo response"
            self.write(sent_str)
            return
        sent_str = chr(PacketType.SERVO_CONTROL_MODE)
        sent_str += f"Finger servo control mode\n\ntarget:{target_name}\n\nstate:{self.finger_states[target_name]}"
        self.write(sent_str)


if __name__ == "__main__":
    rospy.init_node("finger_servo_control_mode")
    fscm = FingerServoControlMode()
    rospy.spin()
