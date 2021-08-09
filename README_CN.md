# wlkata-mirobot-python 
勤牛智能 Mirobot六自由度机械臂 Python SDK

## 安装包

**Windows**
```bash
pip install wlkata-mirobot-python
```

**Ubuntu**
```bash
pip3 install wlkata-mirobot-python
```

## 快速入手

```python
'''
机械臂腕关节的位置控制, 点控P2P(point to point)模式
'''
from wlkata_mirobot import WlkataMirobot
import time
# 创建机械臂
# 注: 需要修改这里的端口号
# - Windows: COM+编号, 举例 'COM15'
# - Linux: /dev/ttyUSB+编号, 举例 '/dev/ttyUSB0'
arm = WlkataMirobot(portname='COM15', debug=True)
# 回归机械零点 Homing (同步模式)
arm.home_simultaneous()

print("运动到目标点 A")
arm.set_wrist_pose(200,  20, 230)
print(f"当前末端在机械臂坐标系下的位姿 {arm.pose}")
time.sleep(1)

print("运动到目标点 B")
arm.set_wrist_pose(200,  20, 150)
print(f"当前末端在机械臂坐标系下的位姿 {arm.pose}")
time.sleep(1)

print("运动到目标点 C, 指定末端的姿态角")
arm.set_wrist_pose(150,  -20,  230, roll=30.0, pitch=0, yaw=45.0)
print(f"当前末端在机械臂坐标系下的位姿 {arm.pose}")
```