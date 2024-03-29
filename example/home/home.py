'''
机械臂回归机械零点与状态查询
'''
from wlkata_mirobot import WlkataMirobot
import time

print("实例化Mirobot机械臂实例")
debug = False # 调试模式 配置为True可以显示更多的日志信息
# 自动检索端口号
arm = WlkataMirobot(debug=debug)
# Ubuntu操作系统上， 指定设备名称
# arm = WlkataMirobot(debug=debug, portname="/dev/ttyUSB0")
# Windows操作系统上， 指定设备名称
# arm = WlkataMirobot(debug=debug, portname="COM5")

# 机械臂Home 多轴并行
print("机械臂Homing开始")
# 注: 
# - 一般情况，在无第七轴的时候， 直接执行 arm.home() 即可, 
# 参数has_slider默认为False。 
# - 如有有滑台(第七轴), 将has_slider设置为True
arm.home()
# arm.home(has_slider=False)
# arm.home(has_slider=True)
print("机械臂Homing结束")

# 状态更新与查询
print("更新机械臂状态")
arm.get_status()
print(f"更新后的状态对象: {arm.status}")
print(f"更新后的状态名称: {arm.status.state}")