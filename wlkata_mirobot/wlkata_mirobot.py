"""
Mirobot主类
"""
import math
from collections import namedtuple
from enum import Enum
from typing import NamedTuple

from .wlkata_mirobot_gcode_protocol import WlkataMirobotGcodeProtocol
# from .wlkata_mirobot_end_relative_motion import MirobotEndRelativeMotion
from .wlkata_mirobot_status import MirobotAngles, MirobotCartesians

# # dim_splitter: NamedTuple = namedtuple('dim_spliter', ['cartesian', 'angle', 'rail'])
# # cartesian_type_splitter: NamedTuple = namedtuple('cartesian_type_splitter', ['ptp', 'lin'])
# left_right_splitter: NamedTuple = namedtuple('left_right_splitter', ['left', 'right'])
# upper_lower_splitter: NamedTuple = namedtuple('upper_lower_splitter', ['upper', 'lower'])
# four_way_splitter: NamedTuple = namedtuple('four_way_splitter', ['left', 'right', 'upper', 'lower'])
# forward_backward_splitter: NamedTuple = namedtuple('forward_backward_splitter', ['forward', 'backward'])
# rover_splitter: NamedTuple = namedtuple('rover_splitter', ['wheel', 'rotate', 'move'])


class WlkataMirobotTool(Enum):
    NO_TOOL = 0         # 没有工具
    SUCTION_CUP = 1     # 气泵吸头
    GRIPPER = 2         # 舵机爪子
    FLEXIBLE_CLAW = 3   # 三指柔爪

class WlkataMirobot(WlkataMirobotGcodeProtocol):
    """
    Wlkata Mirobot 机械臂Python SDK, 提供给用户使用。
    """
    def __init__(self, *base_mirobot_args, **base_mirobot_kwargs):
        """
        Initialization of the `Mirobot` class.

        Parameters
        ----------
        *base_mirobot_args : Any
            Arguments that are passed into `mirobot.wlkata_mirobot_gcode_protocol.WlkataMirobotGcodeProtocol`. See `mirobot.wlkata_mirobot_gcode_protocol.WlkataMirobotGcodeProtocol.__init__` for more details.

        **base_mirobot_kwargs : Any
            Keyword arguments that are passed into `mirobot.wlkata_mirobot_gcode_protocol.WlkataMirobotGcodeProtocol`. See `mirobot.wlkata_mirobot_gcode_protocol.WlkataMirobotGcodeProtocol.__init__` for more details.

        Returns
        -------
        class : `Mirobot`

        """
        super().__init__(*base_mirobot_args, **base_mirobot_kwargs)        
    @property
    def state(self):
        """ 
        The brief descriptor string for Mirobot's state. 
        获取Mirobot状态码介绍
        """
        return self.status.state

    @property
    def cartesian(self):
        """ Dataclass that holds the cartesian values and roll/pitch/yaw angles.
        获取Mirobot当前在笛卡尔坐标系下的位姿
        """
        return self.status.cartesian

    @property
    def angle(self):
        """ Dataclass that holds Mirobot's angular values including the rail position value. """
        return self.status.angle

    @property
    def slider(self):
        """ 
        Location of external slide rail module 
        获取滑台(Mirobot第七轴)的位置
        """
        return self.status.angle.d

    @property
    def valve_pwm(self):
        """ The current pwm of the value module. (eg. gripper) """
        return self.status.valve_pwm

    @property
    def pump_pwm(self):
        """ The current pwm of the pnuematic pump module. """
        return self.status.pump_pwm

    @property
    def motion_mode(self):
        """ Whether Mirobot is currently in coordinate mode (`False`) or joint-motion mode (`True`) """
        return self.status.motion_mode


    def go_to_cartesian_lin(self, x=None, y=None, z=None, a=None, b=None, c=None, speed=None, wait_ok=None):
        """
        Linear move to a position in cartesian coordinates. (Command: `M20 G90 G1`)

        Parameters
        ----------
        x : Union[float, mirobot.mirobot_status.MirobotCartesians]
            (Default value = `None`) If `float`, this represents the X-axis position.
                                     If of type `mirobot.mirobot_status.MirobotCartesians`, then this will be used for all positional values instead.
        y : float
            (Default value = `None`) Y-axis position.
        z : float
            (Default value = `None`) Z-axis position.
        a : float
            (Default value = `None`) Orientation angle: Roll angle
        b : float
            (Default value = `None`) Orientation angle: Pitch angle
        c : float
            (Default value = `None`) Orientation angle: Yaw angle
        speed : int
            (Default value = `None`) The speed in which the Mirobot moves during this operation. (mm/s)
         : bool
            (Default value = `None`) Whether to  for output to return from the Mirobot before returning from the function. This value determines if the function will block until the operation recieves feedback. If `None`, use class default `WlkataMirobotGcodeProtocol.` instead.

        Returns
        -------
        msg : List[str] or bool
            If `` is `True`, then return a list of strings which contains message output.
            If `` is `False`, then return whether sending the message succeeded.
        """
        if isinstance(x, MirobotCartesians):
            inputs = x.asdict()

        else:
            inputs = {'x': x, 'y': y, 'z': z, 'a': a, 'b': b, 'c': c}

        return super().go_to_cartesian_lin(**inputs,
                                           speed=speed, wait_ok=wait_ok)
    def set_tool_type(self, tool):
        '''选择末端工具'''
        self.tool = tool
        self.logger.info(f"Change Tool : {tool.name}")
        # 获取工具的ID
        tool_id = tool.value
        # 发送指令
        super().set_tool_type(tool_id)
        
    def set_tool_pose(self, x=None, y=None, z=None, roll=0.0, pitch=0.0, yaw=0.0, mode='p2p', speed=None, wait_ok=None):
        """
        设置工具的位姿
        Parameters
        ----------
        x : float
            (Default value = `None`) 腕关节在机械臂基坐标系下的x轴坐标
        y : float
            (Default value = `None`) 腕关节在机械臂基坐标系下的y轴坐标
        z : float
            (Default value = `None`) 腕关节在机械臂基坐标系下的z轴坐标
        roll : float
            (Default value = `None`) 腕关节在机械臂基坐标系下的横滚角(Roll angle)
        pitch : float
            (Default value = `None`) 腕关节在机械臂基坐标系下的俯仰角(Pitch angle) 
        yaw : float
            (Default value = `None`) 腕关节在机械臂基坐标系下的偏航角(Yaw angle) 
        mode : string
            (Default value = `p2p`) 运动控制的模式, 默认选择p2p
            `p2p`: 点到点的控制(Point to Point)
            `linear`: 直线插补(Linear Interpolation)
        speed : int
            (Default value = `None`) The speed in which the Mirobot moves during this operation. (mm/s)
         : bool
            (Default value = `None`) Whether to  for output to return from the Mirobot before returning from the function. This value determines if the function will block until the operation recieves feedback. If `None`, use class default `WlkataMirobotGcodeProtocol.` instead.

        Returns
        -------
        msg : List[str] or bool
            If `` is `True`, then return a list of strings which contains message output.
            If `` is `False`, then return whether sending the message succeeded.
        """
        if mode == "p2p":
            # 点控模式 Point To Point
            self.go_to_cartesian_ptp(x=x, y=y, z=z, a=yaw, b=pitch, c=yaw, speed=speed, wait_ok=wait_ok)
        elif mode == "linear":
            # 直线插补 Linera Interpolation
            self.go_to_cartesian_lin(x=x, y=y, z=z, a=yaw, b=pitch, c=yaw, speed=speed, wait_ok=wait_ok)
        else:
            # 默认是点到点
            self.go_to_cartesian_ptp(x=x, y=y, z=z, a=yaw, b=pitch, c=yaw, speed=speed, wait_ok=wait_ok)

    def go_to_cartesian_ptp(self, x=None, y=None, z=None, a=None, b=None, c=None, speed=None, wait_ok=None):
        """
        Point-to-point move to a position in cartesian coordinates. (Command: `M20 G90 G0`)

        Parameters
        ----------
        x : Union[float, mirobot.mirobot_status.MirobotCartesians]
            (Default value = `None`) If `float`, this represents the X-axis position.
                                     If of type `mirobot.mirobot_status.MirobotCartesians`, then this will be used for all positional values instead.
        y : float
            (Default value = `None`) Y-axis position.
        z : float
            (Default value = `None`) Z-axis position.
        a : float
            (Default value = `None`) Orientation angle: Roll angle
        b : float
            (Default value = `None`) Orientation angle: Pitch angle
        c : float
            (Default value = `None`) Orientation angle: Yaw angle
        speed : int
            (Default value = `None`) The speed in which the Mirobot moves during this operation. (mm/s)
         : bool
            (Default value = `None`) Whether to  for output to return from the Mirobot before returning from the function. This value determines if the function will block until the operation recieves feedback. If `None`, use class default `WlkataMirobotGcodeProtocol.` instead.

        Returns
        -------
        msg : List[str] or bool
            If `` is `True`, then return a list of strings which contains message output.
            If `` is `False`, then return whether sending the message succeeded.
        """

        if isinstance(x, MirobotCartesians):
            inputs = x.asdict()

        else:
            inputs = {'x': x, 'y': y, 'z': z, 'a': a, 'b': b, 'c': c}

        return super().go_to_cartesian_ptp(**inputs,
                                           speed=speed, wait_ok=wait_ok)

    def go_to_axis(self, x=None, y=None, z=None, a=None, b=None, c=None, d=None, speed=None, wait_ok=None):
        """
        Send all axes to a specific position in angular coordinates. (Command: `M21 G90`)

        Parameters
        ----------
        x : Union[float, mirobot.mirobot_status.MirobotAngles]
            (Default value = `None`) If `float`, this represents the angle of axis 1.
                                     If of type `mirobot.mirobot_status.MirobotAngles`, then this will be used for all positional values instead.
        y : float
            (Default value = `None`) Angle of axis 2.
        z : float
            (Default value = `None`) Angle of axis 3.
        a : float
            (Default value = `None`) Angle of axis 4.
        b : float
            (Default value = `None`) Angle of axis 5.
        c : float
            (Default value = `None`) Angle of axis 6.
        d : float
            (Default value = `None`) Location of slide rail module.
        speed : int
            (Default value = `None`) The speed in which the Mirobot moves during this operation. (mm/s)
         : bool
            (Default value = `None`) Whether to  for output to return from the Mirobot before returning from the function. This value determines if the function will block until the operation recieves feedback. If `None`, use class default `WlkataMirobotGcodeProtocol.` instead.

        Returns
        -------
        msg : List[str] or bool
            If `` is `True`, then return a list of strings which contains message output.
            If `` is `False`, then return whether sending the message succeeded.
        """
        if isinstance(x, MirobotAngles):
            inputs = x.asdict()

        else:
            inputs = {'x': x, 'y': y, 'z': z, 'a': a, 'b': b, 'c': c, 'd': d}

        return super().go_to_axis(**inputs,
                                  speed=speed, wait_ok=wait_ok)

    def increment_cartesian_lin(self, x=None, y=None, z=None, a=None, b=None, c=None, speed=None, wait_ok=None):
        """
        Linear increment in cartesian coordinates. (Command: `M20 G91 G1`)

        Parameters
        ----------
        x : Union[float, mirobot.mirobot_status.MirobotCartesians]
            (Default value = `None`) If `float`, this represents the X-axis position.
                                     If of type `mirobot.mirobot_status.MirobotCartesians`, then this will be used for all positional values instead.
        y : float
            (Default value = `None`) Y-axis position
        z : float
            (Default value = `None`) Z-axis position.
        a : float
            (Default value = `None`) Orientation angle: Roll angle
        b : float
            (Default value = `None`) Orientation angle: Pitch angle
        c : float
            (Default value = `None`) Orientation angle: Yaw angle
        speed : int
            (Default value = `None`) The speed in which the Mirobot moves during this operation. (mm/s)
         : bool
            (Default value = `None`) Whether to  for output to return from the Mirobot before returning from the function. This value determines if the function will block until the operation recieves feedback. If `None`, use class default `WlkataMirobotGcodeProtocol.` instead.

        Returns
        -------
        msg : List[str] or bool
            If `` is `True`, then return a list of strings which contains message output.
            If `` is `False`, then return whether sending the message succeeded.
        """
        if isinstance(x, MirobotCartesians):
            inputs = x.asdict()

        else:
            inputs = {'x': x, 'y': y, 'z': z, 'a': a, 'b': b, 'c': c}

        return super().increment_cartesian_lin(**inputs,
                                               speed=speed, wait_ok=wait_ok)

    def increment_cartesian_ptp(self, x=None, y=None, z=None, a=None, b=None, c=None, speed=None, wait_ok=None):
        """
        Point-to-point increment in cartesian coordinates. (Command: `M20 G91 G0`)

        Parameters
        ----------
        x : Union[float, mirobot.mirobot_status.MirobotCartesians]
            (Default value = `None`) If `float`, this represents the X-axis position.
                                     If of type `mirobot.mirobot_status.MirobotCartesians`, then this will be used for all positional values instead.
        y : float
            (Default value = `None`) Y-axis position.
        z : float
            (Default value = `None`) Z-axis position.
        a : float
            (Default value = `None`) Orientation angle: Roll angle
        b : float
            (Default value = `None`) Orientation angle: Pitch angle
        c : float
            (Default value = `None`) Orientation angle: Yaw angle
        speed : int
            (Default value = `None`) The speed in which the Mirobot moves during this operation. (mm/s)
         : bool
            (Default value = `None`) Whether to  for output to return from the Mirobot before returning from the function. This value determines if the function will block until the operation recieves feedback. If `None`, use class default `WlkataMirobotGcodeProtocol.` instead.

        Returns
        -------
        msg : List[str] or bool
            If `` is `True`, then return a list of strings which contains message output.
            If `` is `False`, then return whether sending the message succeeded.
        """
        if isinstance(x, MirobotCartesians):
            inputs = x.asdict()

        else:
            inputs = {'x': x, 'y': y, 'z': z, 'a': a, 'b': b, 'c': c}

        return super().increment_cartesian_ptp(**inputs,
                                               speed=speed, wait_ok=wait_ok)

    def increment_axis(self, x=None, y=None, z=None, a=None, b=None, c=None, d=None, speed=None, wait_ok=None):
        """
        Increment all axes a specified amount in angular coordinates. (Command: `M21 G91`)

        Parameters
        ----------
        x : Union[float, mirobot.mirobot_status.MirobotAngles]
            (Default value = `None`) If `float`, this represents the angle of axis 1.
                                     If of type `mirobot.mirobot_status.MirobotAngles`, then this will be used for all positional values instead.
        y : float
            (Default value = `None`) Angle of axis 2.
        z : float
            (Default value = `None`) Angle of axis 3.
        a : float
            (Default value = `None`) Angle of axis 4.
        b : float
            (Default value = `None`) Angle of axis 5.
        c : float
            (Default value = `None`) Angle of axis 6.
        d : float
            (Default value = `None`) Location of slide rail module.
        speed : int
            (Default value = `None`) The speed in which the Mirobot moves during this operation. (mm/s)
         : bool
            (Default value = `None`) Whether to  for output to return from the Mirobot before returning from the function. This value determines if the function will block until the operation recieves feedback. If `None`, use class default `WlkataMirobotGcodeProtocol.` instead.

        Returns
        -------
        msg : List[str] or bool
            If `` is `True`, then return a list of strings which contains message output.
            If `` is `False`, then return whether sending the message succeeded.
        """
        if isinstance(x, MirobotAngles):
            inputs = x.asdict()

        else:
            inputs = {'x': x, 'y': y, 'z': z, 'a': a, 'b': b, 'c': c, 'd': d}

        return super().increment_axis(**inputs,
                                      speed=speed, wait_ok=wait_ok)

    def set_slider_posi(self, d, speed=None, is_relative=False, wait_ok=True):
        '''设置滑台位置, 单位mm'''
        if not is_relative:
            return super().go_to_axis(d=d,
                                    speed=speed, wait_ok=wait_ok)
        else:
            return super().increment_axis(d=d,
                                      speed=speed, wait_ok=wait_ok)
    
    @property
    def pose(self):
        return self.cartesian