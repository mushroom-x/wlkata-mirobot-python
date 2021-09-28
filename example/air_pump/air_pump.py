'''
气泵控制
'''
from wlkata_mirobot import WlkataMirobot
import time

arm = WlkataMirobot(portname='COM12')
arm.home()

# 气泵开启-吸气
arm.pump_suction()
# 等待5s
time.sleep(5)

# 气泵关闭
arm.pump_off()
# 等待5s
time.sleep(2)

# 气泵开启-吹气
arm.pump_blowing()
# 等待5s
time.sleep(5)

# 气泵关闭
arm.pump_off()
# 等待5s
time.sleep(2)