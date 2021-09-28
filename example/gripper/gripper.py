'''
气泵控制
'''
from wlkata_mirobot import WlkataMirobot
import time

arm = WlkataMirobot()
arm.home()

# 设置爪子的间距
spacing_mm = 20.0
arm.set_gripper_spacing(spacing_mm)
time.sleep(2)
# 爪子张开
arm.gripper_open()
time.sleep(2)
# 爪子闭合
arm.gripper_close()
time.sleep(2)