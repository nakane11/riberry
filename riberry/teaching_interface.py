from kxr_controller.kxr_interface import KXRROSRobotInterface


class TeachingRobotInterface(KXRROSRobotInterface):
    def __init__(self, *args, **kwargs):
        super(TeachingRobotInterface, self).__init__(*args, **kwargs)
