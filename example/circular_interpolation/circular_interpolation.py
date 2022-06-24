'''
机械臂工具位姿控制
插补算法: 圆弧插补(circular interpolation.)
'''
from wlkata_mirobot import WlkataMirobot
import time
# 创建机械臂
arm = WlkataMirobot()
# Homing
arm.home()

print("运动到目标点 A")
arm.set_tool_pose(200,  40, 150)
print(f"当前末端在机械臂坐标系下的位姿 {arm.pose}")
time.sleep(2)


print("运动到目标点 B(圆弧插补)")
ex, ey = (0, -80) 	# 末端目标坐标, 单位mm(相对于当前点)
radius = 100		# 半径, 单位mm
is_cw = False		# 运动方向 True: 顺时针, False: 逆时针
arm.circular_interpolation(ex, ey, radius, is_cw=is_cw)
print(f"当前末端在机械臂坐标系下的位姿 {arm.pose}")
time.sleep(2)

