'''
机械臂滑台示例
'''
import time
from wlkata_mirobot import WlkataMirobot

print("实例化Mirobot机械臂实例")
arm = WlkataMirobot()

# 机械臂本体与滑台是否同时Homing
is_home_simultaneously = True
# 归零
if is_home_simultaneously:
	print("本体跟滑台同时归零")
	arm.home(has_slider=True)
else:
	print("机械臂本体Homing")
	arm.home()
	print("滑台Homing")
	arm.home_slider()

print("延时2s")
time.sleep(2)

print('设置滑台的位置 300mm, 速度 2000 mm/min')
arm.set_slider_posi(300, speed=2000)

print("延时2s")
time.sleep(2)

print('设置滑台的位置 100mm')
arm.set_slider_posi(100)

print('设置滑台的位置 相对移动 +50mm')
arm.set_slider_posi(50, is_relative=True)

# 更新机械臂的状态
arm.get_status()
print(f"当前的滑台的位置 :{arm.slider} mm")
