'''
获取机械臂的状态
'''
import time
from wlkata_mirobot import WlkataMirobot
# 创建机械臂对象
arm = WlkataMirobot(portname='COM12')
# 机械臂回归零点
arm.home()
# 等待15s
time.sleep(15)
# 打印机械臂当前的状态
print("获取机械臂的状态 ?")
print(arm.get_status())