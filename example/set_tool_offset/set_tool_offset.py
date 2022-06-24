'''
手动设置工具坐标系的偏移量, 适用于自制末端的情况。
注: 如果是标准的末端工具，建议使用API `set_tool_type`。
'''
import time
from wlkata_mirobot import WlkataMirobot, WlkataMirobotTool

print("实例化Mirobot机械臂实例")
arm = WlkataMirobot()

# 机械臂Home 多轴并行
print("机械臂Homing开始")
arm.home()
print("机械臂Homing结束")

# 注: 默认工具为无
# 状态更新与查询
print("更新机械臂状态")
arm.get_status()
print(f"机械臂工具位姿: {arm.cartesian}")

# 偏移量定义，单位mm
offset_x = 0
offset_y = 0
offset_z = -20.0
print(f'手动设置工具坐标系的偏移量 ({offset_x}, {offset_y}, {offset_z}) ')
arm.set_tool_offset(offset_x, offset_y, offset_z)

# 状态更新与查询
print("更新机械臂状态")
arm.get_status()
print(f"机械臂工具位姿(气泵): {arm.cartesian}")
