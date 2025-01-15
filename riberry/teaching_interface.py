import actionlib
from kxr_controller.kxr_interface import KXRROSRobotInterface
from hand_v3.msg import HandPoseAction, HandPoseGoal


class TeachingRobotInterface(KXRROSRobotInterface):
    def __init__(self, *args, **kwargs):
        super(TeachingRobotInterface, self).__init__(*args, **kwargs)
        self.hand_client = actionlib.SimpleActionClient('/hand_pose', HandPoseAction)
        self.hand_client.wait_for_server()

    def send_pose(self, pose):
        goal = HandPoseGoal(pose=pose)
        self.hand_client.send_goal(goal)
        self.hand_client.wait_for_result()
