'''
机械臂工具位姿控制
插补算法: 点到点快速移动(p2p point-to-point)
'''
from wlkata_mirobot import WlkataMirobot
import time
# 创建机械臂
arm = WlkataMirobot()
# Homing
arm.home()

print("运动到目标点 A")
arm.p2p_interpolation(100,  100, 150)
print(f"当前末端在机械臂坐标系下的位姿 {arm.pose}")
time.sleep(2)


print("运动到目标点 B")
x, y, z = 100,  -100, 150
roll, pitch, yaw = 30.0, 0, 45.0
arm.p2p_interpolation(x, y, z, roll, pitch, yaw)
print(f"当前末端在机械臂坐标系下的位姿 {arm.pose}")
time.sleep(2)
