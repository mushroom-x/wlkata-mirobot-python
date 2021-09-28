'''
机械臂回归机械零点与状态查询
'''
from wlkata_mirobot import WlkataMirobot
import time

print("实例化Mirobot机械臂实例")
arm = WlkataMirobot(portname='COM12', debug=False)

# 机械臂Home 多轴并行
print("机械臂Homing开始")
# 注: 
# - 一般情况，在无第七轴的时候， 直接执行 arm.home() 即可, 参数has_slider默认为False。 
# - 如有有滑台(第七轴), 将has_slider设置为True
arm.home(has_slider=False)
print("机械臂Homing结束")

# 状态更新与查询
print("更新机械臂状态")
arm.update_status()
print(f"更新后的状态对象: {arm.status}")
print(f"更新后的状态名称: {arm.status.state}")