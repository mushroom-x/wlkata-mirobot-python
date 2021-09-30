'''
机械臂工具位姿控制
插补算法: 直线插补(linear_interpolation.)
'''
from wlkata_mirobot import WlkataMirobot
import time
# 创建机械臂
arm = WlkataMirobot()
# Homing
arm.home()

print("运动到目标点 A")
arm.set_tool_pose(200,  50, 150, mode="linear")
print(f"当前末端在机械臂坐标系下的位姿 {arm.pose}")
time.sleep(2)


print("运动到目标点 B")
arm.set_tool_pose(200,  -50, 150, mode="linear")
print(f"当前末端在机械臂坐标系下的位姿 {arm.pose}")
time.sleep(2)
