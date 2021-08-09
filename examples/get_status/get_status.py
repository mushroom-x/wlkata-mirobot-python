'''
获取机械臂的状态
'''
from mirobot import Mirobot
import time
arm = Mirobot(portname='COM7', debug=False)

# 注:一定要配置为wait=False,非阻塞式等待
# 要不然会卡死
arm.home_simultaneous(wait=False)
# 等待15s
time.sleep(15)
# 打印机械臂当前的状态
print("获取机械臂的状态 ?")
print(arm.get_status())