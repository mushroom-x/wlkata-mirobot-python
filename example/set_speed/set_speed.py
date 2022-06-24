'''
设置机械臂末端的移动速度
'''
from wlkata_mirobot import WlkataMirobot
import time
# 创建机械臂
arm = WlkataMirobot()
# Homing
arm.home()

print("设置速度为 2000 mm/min, 移动到A点")
arm.set_speed(2000)
arm.set_tool_pose(100,  100, 230)
time.sleep(1)

print("设置速度为 3000 mm/min, 移动到B点")
arm.set_speed(3000)
arm.set_tool_pose(100,  -100, 230)
time.sleep(1)
