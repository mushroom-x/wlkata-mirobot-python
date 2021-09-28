'''
机械臂回归机械零点与状态查询
'''
from wlkata_mirobot import WlkataMirobot
import time

print("实例化Mirobot机械臂实例")
arm = WlkataMirobot(portname='COM12', debug=True)

# 机械臂Home 多轴并行
print("机械臂Homing")
# 机械臂本体归零
arm.home()
print("滑台Homing")
# 滑台归零
arm.home_slider()

# 上述两行可以替换为下面一行
# 本体跟滑台同时归零
# arm.home(has_slider=True)

# 设置滑台行程
# arm.set_slider_range()