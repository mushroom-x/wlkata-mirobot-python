# wlkata-mirobot-python
Wlkata Mirobot (6DoF Robot Arm) Python  SDK


## Install Package

**Windows**
```bash
pip install wlkata-mirobot-python
```

**Ubuntu**
```bash
pip3 install wlkata-mirobot-python
```

## Quick Start

```python
'''
Set robot arm wrist pose by P2P trajectory plan
P2P: point to point
'''
from wlkata_mirobot import WlkataMirobot
import time
# Create Robot Arm Object
# Remember to change portname.
# - Windows: COM + ID, exp: 'COM15'
# - Linux: /dev/ttyUSB + ID, exp: '/dev/ttyUSB0'
arm = WlkataMirobot(portname='COM15', debug=True)
# Robot Arm Homing
arm.home_simultaneous()

print("Move to point A (x, y, z)")
arm.set_wrist_pose(200,  20, 230)
print(f"Current robot arm end pose:  {arm.pose}")
time.sleep(1)

print("Move to point B (x, y, z)")
arm.set_wrist_pose(200,  20, 150)
print(f"Current robot arm end pose: {arm.pose}")
time.sleep(1)

print("Move to point C (x, y, z, roll, pitch, yaw)")
arm.set_wrist_pose(150,  -20,  230, roll=30.0, pitch=0, yaw=45.0)
print(f"Current robot arm end pose {arm.pose}")
```