'''
设置机械臂关节的角度, 单位°
'''
from mirobot import Mirobot
import time
arm = Mirobot(portname='COM7', debug=False)
arm.home_simultaneous()

# 设置单个关节的角度
print("测试设置单个关节的角度")
arm.set_joint_angle({1:100.0}, wait=True)
print("动作执行完毕")
# 状态查询
print(f"状态查询: {arm.get_status()}")
# 停顿2s
time.sleep(2)

# 设置多个关节的角度
print("设置多个关节的角度")
target_angles = {1:90.0, 2:30.0, 3:-20.0, 4:10.0, 5:0.0, 6:90.0}
arm.set_joint_angle(target_angles, wait=True)
print("动作执行完毕")
# 状态查询
print(f"状态查询: {arm.get_status()}")
# 停顿2s
time.sleep(2)
