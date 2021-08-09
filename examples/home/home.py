'''
机械臂回归机械零点与状态查询
'''
from mirobot import Mirobot
import time

print("实例化Mirobot机械臂实例")
arm = Mirobot(portname='COM7', debug=False)

# 机械臂Home 多轴并行
print("机械臂Homing开始")
arm.home_simultaneous(wait=True)
print("机械臂Homing结束")

# 状态更新与查询
print("更新机械臂状态")
arm.update_status()
print(f"更新后的状态对象: {arm.status}")
print(f"更新后的状态名称: {arm.status.state}")