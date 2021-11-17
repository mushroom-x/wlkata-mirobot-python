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


print("延时2s")
time.sleep(2)

print('设置传送带的位置 0mm')
arm.set_conveyor_posi(-200)

print("延时2s")
time.sleep(2)

print('设置传送带的位置 300mm')
arm.set_conveyor_posi(-300)

print("延时2s")
time.sleep(2)

print('设置传送带的位置 相对移动 +100mm')
arm.set_conveyor_posi(-100, is_relative=True)

# 更新机械臂的状态
arm.get_status()
print(f"当前的传送带的的位置 :{arm.conveyor} mm")