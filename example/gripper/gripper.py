'''
气泵控制
'''
from wlkata_mirobot import WlkataMirobot
import time

arm = WlkataMirobot(portname='COM12', debug=False)
arm.home_simultaneous()

# 设置爪子的间距
spacing_mm = 30.0
arm.set_gripper_spacing(spacing_mm)