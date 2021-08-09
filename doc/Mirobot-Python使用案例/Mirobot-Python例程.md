# Mirobot-Python例程



## 机械臂回归机械零点与状态查询
**例程源码**
```python
'''
机械臂回归机械零点与状态查询
'''
from mirobot import Mirobot
import time

print("实例化Mirobot机械臂实例")
arm = Mirobot(portname='COM7', debug=False)

# 机械臂Home 多轴并行
print("机械臂Homing开始")
arm.home_simultaneous(wait=True)
print("机械臂Homing结束")

# 状态更新与查询
print("更新机械臂状态")
arm.update_status()
print(f"更新后的状态对象: {arm.status}")
print(f"更新后的状态名称: {arm.status.state}")
```

**输出日志**
```
实例化Mirobot机械臂实例
机械臂Homing开始
机械臂Homing结束
更新机械臂状态
更新后的状态对象: MirobotStatus(state='Idle', angle=MirobotAngles(a=0.0, b=0.0, c=0.0, x=0.0, y=0.0, z=0.0, d=0.0), cartesian=MirobotCartesians(x=198.67, y=0.0, z=230.72, a=0.0, b=0.0, c=0.0), pump_pwm=0, valve_pwm=0, motion_mode=True) 
更新后的状态名称: Idle
```
## 设置关节角度

**例程源码**
```python
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

```

**输出日志**

```
测试设置单个关节的角度
动作执行完毕
状态查询: ['<Idle,Angle(ABCDXYZ):0.000,0.000,0.000,0.000,100.000,0.000,0.000,Cartesian coordinate(XYZ RxRyRz):-34.499,195.652,230.720,0.000,0.000,100.000,Pump PWM:0,Valve PWM:0,Motion_MODE:0>', 'ok']
设置多个关节的角度
动作执行完毕
状态查询: ['<Idle,Angle(ABCDXYZ):10.000,19.982,45.005,0.000,90.005,30.001,-20.000,Cartesian coordinate(XYZ RxRyRz):-3.985,241.503,190.191,28.916,13.226,139.337,Pump PWM:0,Valve PWM:0,Motion_MODE:0>', 'ok']
```

## 设置机械臂末端的位姿(Point2Point)

**例程源码**
```python
'''
机械臂腕关节的位置控制, 点控 point to point
'''
from mirobot import Mirobot
import time
arm = Mirobot(portname='COM7', debug=False)
arm.home_simultaneous()

print("运动到目标点 A")
arm.set_wrist_pose(200,  20, 230, mode="p2p")
print(f"当前末端在机械臂坐标系下的位姿 {arm.pose}")
time.sleep(1)

print("运动到目标点 B")
arm.set_wrist_pose(200,  20, 150, mode="linear")
print(f"当前末端在机械臂坐标系下的位姿 {arm.pose}")
time.sleep(1)

print("运动到目标点 C, 指定末端的姿态角")
arm.set_wrist_pose(150,  -20,  230, roll=30.0, pitch=0, yaw=45.0)
print(f"当前末端在机械臂坐标系下的位姿 {arm.pose}")
```

**日志输出**

```
运动到目标点 A
当前末端在机械臂坐标系下的位姿 Pose(x=199.99,y=20.001,z=229.724,roll=-0.001,pitch=0.015,yaw=0.041)
运动到目标点 B
当前末端在机械臂坐标系下的位姿 Pose(x=199.987,y=20.001,z=149.696,roll=-0.002,pitch=0.019,yaw=0.041)
运动到目标点 C, 指定末端的姿态角
当前末端在机械臂坐标系下的位姿 Pose(x=149.858,y=-19.859,z=229.829,roll=44.991,pitch=-0.031,yaw=45.001)
```


## 气泵控制

**例程源码**
```python
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
```

