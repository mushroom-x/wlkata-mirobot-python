'''
气泵控制
'''
from mirobot import Mirobot
import time
arm = Mirobot(portname='COM7', debug=False)
arm.home_simultaneous()

# 气泵开启
arm.pump_on()
# 等待5s
time.sleep(5)
# 气泵关闭
arm.pump_off()