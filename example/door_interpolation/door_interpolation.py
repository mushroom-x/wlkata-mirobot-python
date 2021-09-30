'''
机械臂工具位姿控制
插补算法: 门式插补(door interpolation.)
'''
from wlkata_mirobot import WlkataMirobot
import time
# 创建机械臂
arm = WlkataMirobot()
# Homing
arm.home()
# 设置门式轨迹规划抬升高度
arm.set_door_lift_distance(50)

print("运动到目标点 A")
arm.set_tool_pose(200,  40, 150)
print(f"当前末端在机械臂坐标系下的位姿 {arm.pose}")
time.sleep(2)


print("运动到目标点 B(门型插补)")
arm.door_interpolation(200, -40, 150)
print(f"当前末端在机械臂坐标系下的位姿 {arm.pose}")
time.sleep(2)

