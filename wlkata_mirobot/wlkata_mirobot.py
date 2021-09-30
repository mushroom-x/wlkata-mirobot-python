"""
Mirobot主类
"""
import math
from collections import namedtuple
from enum import Enum
from typing import NamedTuple

from .wlkata_mirobot_gcode_protocol import WlkataMirobotGcodeProtocol
from .wlkata_mirobot_status import MirobotAngles, MirobotCartesians

class WlkataMirobotTool(Enum):
    NO_TOOL = 0         # 没有工具
    SUCTION_CUP = 1     # 气泵吸头
    GRIPPER = 2         # 舵机爪子
    FLEXIBLE_CLAW = 3   # 三指柔爪

class WlkataMirobot(WlkataMirobotGcodeProtocol):
    '''
    Wlkata Mirobot 机械臂Python SDK, 提供给用户使用。
    '''
    def __init__(self, *base_mirobot_args, **base_mirobot_kwargs):
        '''初始化'''
        super().__init__(*base_mirobot_args, **base_mirobot_kwargs)        
        self.tool = WlkataMirobotTool.NO_TOOL
    
    @property
    def state(self):
        '''获取Mirobot状态码'''
        return self.status.state

    @property
    def pose(self):
        '''末端位姿6dof'''
        return self.cartesian
    
    @property
    def cartesian(self):
        '''末端位姿6dof'''
        return self.status.cartesian

    @property
    def angle(self):
        '''关节角度'''
        return self.status.angle

    @property
    def slider(self):
        '''获取滑台(Mirobot第七轴)的位置'''
        return self.status.angle.d

    @property
    def valve_pwm(self):
        '''电磁阀的PWM'''
        return self.status.valve_pwm

    @property
    def pump_pwm(self):
        '''气泵的PWM'''
        return self.status.pump_pwm

    @property
    def gripper_pwm(self):
        '''爪子的PWM'''
        return self.status.pump_pwm
    
    @property
    def motion_mode(self):
        '''运动模式'''
        return self.status.motion_mode

    def set_tool_type(self, tool):
        '''选择末端工具'''
        self.tool = tool
        self.logger.info(f"Change Tool : {tool.name}")
        # 获取工具的ID
        tool_id = tool.value
        # 发送指令
        super().set_tool_type(tool_id)
        
    def set_tool_pose(self, x=None, y=None, z=None, roll=0.0, pitch=0.0, yaw=0.0, mode='p2p', speed=None, wait_ok=None):
        '''设置工具位姿'''
        if mode == "p2p":
            # 点控模式 Point To Point
            self.super().ptp_interpolation(x=x, y=y, z=z, a=yaw, b=pitch, c=yaw, speed=speed, wait_ok=wait_ok)
        elif mode == "linear":
            # 直线插补 Linera Interpolation
            self.super().linear_interpolation(x=x, y=y, z=z, a=yaw, b=pitch, c=yaw, speed=speed, wait_ok=wait_ok)
        else:
            # 默认是点到点
            self.super().ptp_interpolation(x=x, y=y, z=z, a=yaw, b=pitch, c=yaw, speed=speed, wait_ok=wait_ok)
    
    def set_slider_posi(self, d, speed=None, is_relative=False, wait_ok=True):
        '''设置滑台位置, 单位mm'''
        if not is_relative:
            return super().go_to_axis(d=d,
                                    speed=speed, wait_ok=wait_ok)
        else:
            return super().increment_axis(d=d,
                                      speed=speed, wait_ok=wait_ok)
    
    