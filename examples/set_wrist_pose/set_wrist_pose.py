'''
机械臂腕关节的位置控制, 点控 point to point
'''
from mirobot import Mirobot
import time
arm = Mirobot(portname='COM7', debug=True)
arm.home_simultaneous()

print("运动到目标点 A")
arm.set_wrist_pose(200,  20, 230)
print(f"当前末端在机械臂坐标系下的位姿 {arm.pose}")
time.sleep(1)

print("运动到目标点 B")
arm.set_wrist_pose(200,  20, 150)
print(f"当前末端在机械臂坐标系下的位姿 {arm.pose}")
time.sleep(1)

print("运动到目标点 C, 指定末端的姿态角")
arm.set_wrist_pose(150,  -20,  230, roll=30.0, pitch=0, yaw=45.0)
print(f"当前末端在机械臂坐标系下的位姿 {arm.pose}")