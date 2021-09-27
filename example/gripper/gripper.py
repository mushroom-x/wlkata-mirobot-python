'''
气泵控制
'''
from wlkata_mirobot import WlkataMirobot
import time

arm = WlkataMirobot(portname='COM12', debug=False)
arm.home_simultaneous()

arm.set_valve(60)