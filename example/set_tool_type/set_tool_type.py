'''
设置末端工具类型
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

# 更换工具-选择为吸头
arm.set_tool_type(WlkataMirobotTool.SUCTION_CUP)

# 状态更新与查询
print("更新机械臂状态")
arm.get_status()
print(f"机械臂工具位姿(气泵): {arm.cartesian}")
