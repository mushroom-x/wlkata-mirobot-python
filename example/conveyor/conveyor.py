'''
机械臂传送带示例
'''
import time
from wlkata_mirobot import WlkataMirobot

print("实例化Mirobot机械臂实例")
arm = WlkataMirobot()

# 机械臂本体与滑台是否同时Homing
is_home_simultaneously = True

# 注: 机械臂不需要Homing
print("机械臂本体Homing")
arm.home()

# 设置传动带的运动范围
arm.set_conveyor_range(-30000, 30000)
print("延时2s")
time.sleep(2)

print('设置传送带的位置 1000mm')
arm.set_conveyor_posi(1000)

print("延时2s")
time.sleep(2)

print('设置传送带的位置 -3000mm')
arm.set_conveyor_posi(-3000)

print("延时2s")
time.sleep(2)

print('设置传送带的位置 相对移动 -1000mm')
arm.set_conveyor_posi(-1000, is_relative=True)

# 更新机械臂的状态
arm.get_status()
print(f"当前的传送带的的位置 :{arm.conveyor} mm")
