# wlkata-mirobot-python 
勤牛智能 Mirobot六自由度机械臂 Python SDK

## 安装包

### Windows
通过pip安装
```bash
pip install wlkata-mirobot-python
```

从源码编译安装
```
python -m pip install .
```

### Ubuntu
通过pip安装
```bash
sudo pip3 install wlkata-mirobot-python
```
从源码编译安装
```
sudo python3 -m pip install .
```



## 准备工作

* 将机械臂上电并连接到电脑的USB端口处

* 电脑安装好了CH340的驱动

* 安装好了Mirobot的Python SDK

  

## 快速入手

```python
'''
机械臂腕关节的位置控制, 点控P2P(point to point)模式
'''
import time
from wlkata_mirobot import WlkataMirobot

# 创建机械臂 
arm = WlkataMirobot()
# 回归机械零点 Homing (同步模式)
arm.home()

print("运动到目标点 A")
arm.set_tool_pose(200,  20, 230)
print(f"当前末端在机械臂坐标系下的位姿 {arm.pose}")
time.sleep(1)

print("运动到目标点 B")
arm.set_tool_pose(200,  20, 150)
print(f"当前末端在机械臂坐标系下的位姿 {arm.pose}")
time.sleep(1)

print("运动到目标点 C, 指定末端的姿态角")
arm.set_tool_pose(150,  -20,  230, roll=30.0, pitch=0, yaw=45.0)
print(f"当前末端在机械臂坐标系下的位姿 {arm.pose}")
```

## 使用手册

详细的API说明与示例代码， 请参阅 `doc/WLKATA MIROBOT Python SDK使用手册/`

