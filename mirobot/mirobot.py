from collections import namedtuple
from typing import NamedTuple

from .base_mirobot import BaseMirobot
from .base_rover import BaseRover
from .mirobot_status import MirobotAngles, MirobotCartesians

dim_splitter: NamedTuple = namedtuple('dim_spliter', ['cartesian', 'angle', 'rail'])
cartesian_type_splitter: NamedTuple = namedtuple('cartesian_type_splitter', ['ptp', 'lin'])
left_right_splitter: NamedTuple = namedtuple('left_right_splitter', ['left', 'right'])
upper_lower_splitter: NamedTuple = namedtuple('upper_lower_splitter', ['upper', 'lower'])
four_way_splitter: NamedTuple = namedtuple('four_way_splitter', ['left', 'right', 'upper', 'lower'])
forward_backward_splitter: NamedTuple = namedtuple('forward_backward_splitter', ['forward', 'backward'])
rover_splitter: NamedTuple = namedtuple('rover_splitter', ['wheel', 'rotate', 'move'])


class Mirobot(BaseMirobot):
    """ A class for managing and maintaining known Mirobot operations."""

    def __init__(self, *base_mirobot_args, **base_mirobot_kwargs):
        """
        Initialization of the `Mirobot` class.

        Parameters
        ----------
        *base_mirobot_args : Any
            Arguments that are passed into `mirobot.base_mirobot.BaseMirobot`. See `mirobot.base_mirobot.BaseMirobot.__init__` for more details.

        **base_mirobot_kwargs : Any
            Keyword arguments that are passed into `mirobot.base_mirobot.BaseMirobot`. See `mirobot.base_mirobot.BaseMirobot.__init__` for more details.

        Returns
        -------
        class : `Mirobot`

        """
        super().__init__(*base_mirobot_args, **base_mirobot_kwargs)

        self._rover = BaseRover(self)

        self.move = dim_splitter(cartesian=cartesian_type_splitter(ptp=self.go_to_cartesian_ptp,
                                                                   lin=self.go_to_cartesian_lin),
                                 angle=self.go_to_axis,
                                 rail=self.go_to_slide_rail)
        """ The root of the move alias. Uses `go_to_...` methods. Can be used as `mirobot.move.ptp(...)` or `mirobot.move.angle(...)` """

        self.increment = dim_splitter(cartesian=cartesian_type_splitter(ptp=self.increment_cartesian_ptp,
                                                                        lin=self.increment_cartesian_lin),
                                      angle=self.increment_axis,
                                      rail=self.increment_slide_rail)
        """ The root of the increment alias. Uses `increment_...` methods. Can be used as `mirobot.increment.ptp(...)` or `mirobot.increment.angle(...)` """

        self.wheel = four_way_splitter(upper=left_right_splitter(left=self._rover.move_upper_left,
                                                                 right=self._rover.move_upper_right),
                                       lower=left_right_splitter(left=self._rover.move_bottom_left,
                                                                 right=self._rover.move_bottom_right),
                                       left=upper_lower_splitter(upper=self._rover.move_upper_left,
                                                                 lower=self._rover.move_bottom_left),
                                       right=upper_lower_splitter(upper=self._rover.move_upper_right,
                                                                  lower=self._rover.move_bottom_right))

        self.rover = rover_splitter(wheel=self.wheel,
                                    rotate=left_right_splitter(left=self._rover.rotate_left,
                                                               right=self._rover.rotate_right),
                                    move=forward_backward_splitter(forward=self._rover.move_forward,
                                                                   backward=self._rover.move_backward))
        """ The root of the rover alias. Uses methods from `mirobot.base_rover.BaseRover`. Can be used as `mirobot.rover.wheel.upper.right(...)` or `mirobot.rover.rotate.left(...)` or `mirobot.rover.move.forward(...)`"""

    @property
    def state(self):
        """ The brief descriptor string for Mirobot's state. """
        return self.status.state

    @property
    def cartesian(self):
        """ Dataclass that holds the cartesian values and roll/pitch/yaw angles. """
        return self.status.cartesian

    @property
    def angle(self):
        """ Dataclass that holds Mirobot's angular values including the rail position value. """
        return self.status.angle

    @property
    def rail(self):
        """ Location of external slide rail module """
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

    def go_to_zero(self, speed=None, wait=None):
        """
        Send all axes to their respective zero positions.

        Parameters
        ----------
        speed : int
            (Default value = `None`) The speed in which the Mirobot moves during this operation. (mm/s)
        wait : bool
            (Default value = `None`) Whether to wait for output to return from the Mirobot before returning from the function. This value determines if the function will block until the operation recieves feedback. If `None`, use class default `BaseMirobot.wait` instead.

        Returns
        -------
        msg : List[str] or bool
            If `wait` is `True`, then return a list of strings which contains message output.
            If `wait` is `False`, then return whether sending the message succeeded.
        """
        return self.go_to_axis(0, 0, 0, 0, 0, 0, 0, speed=speed, wait=wait)

    def go_to_cartesian_lin(self, x=None, y=None, z=None, a=None, b=None, c=None, speed=None, wait=None):
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
        wait : bool
            (Default value = `None`) Whether to wait for output to return from the Mirobot before returning from the function. This value determines if the function will block until the operation recieves feedback. If `None`, use class default `BaseMirobot.wait` instead.

        Returns
        -------
        msg : List[str] or bool
            If `wait` is `True`, then return a list of strings which contains message output.
            If `wait` is `False`, then return whether sending the message succeeded.
        """
        if isinstance(x, MirobotCartesians):
            inputs = x.asdict()

        else:
            inputs = {'x': x, 'y': y, 'z': z, 'a': a, 'b': b, 'c': c}

        return super().go_to_cartesian_lin(**inputs,
                                           speed=speed, wait=wait)
    
    def set_wrist_pose(self, x=None, y=None, z=None, roll=0.0, pitch=0.0, yaw=0.0, mode='p2p', speed=None, wait=None):
        """
        设置腕关节的位姿

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
        wait : bool
            (Default value = `None`) Whether to wait for output to return from the Mirobot before returning from the function. This value determines if the function will block until the operation recieves feedback. If `None`, use class default `BaseMirobot.wait` instead.

        Returns
        -------
        msg : List[str] or bool
            If `wait` is `True`, then return a list of strings which contains message output.
            If `wait` is `False`, then return whether sending the message succeeded.
        """
        if mode == "p2p":
            # 点控模式 Point To Point
            self.go_to_cartesian_ptp(x=x, y=y, z=z, a=yaw, b=pitch, c=yaw, speed=speed, wait=wait)
        elif mode == "linear":
            # 直线插补 Linera Interpolation
            self.go_to_cartesian_lin(x=x, y=y, z=z, a=yaw, b=pitch, c=yaw, speed=speed, wait=wait)
        else:
            # 默认是点到点
            self.go_to_cartesian_ptp(x=x, y=y, z=z, a=yaw, b=pitch, c=yaw, speed=speed, wait=wait)

    def go_to_cartesian_ptp(self, x=None, y=None, z=None, a=None, b=None, c=None, speed=None, wait=None):
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
        wait : bool
            (Default value = `None`) Whether to wait for output to return from the Mirobot before returning from the function. This value determines if the function will block until the operation recieves feedback. If `None`, use class default `BaseMirobot.wait` instead.

        Returns
        -------
        msg : List[str] or bool
            If `wait` is `True`, then return a list of strings which contains message output.
            If `wait` is `False`, then return whether sending the message succeeded.
        """

        if isinstance(x, MirobotCartesians):
            inputs = x.asdict()

        else:
            inputs = {'x': x, 'y': y, 'z': z, 'a': a, 'b': b, 'c': c}

        return super().go_to_cartesian_ptp(**inputs,
                                           speed=speed, wait=wait)

    def go_to_axis(self, x=None, y=None, z=None, a=None, b=None, c=None, d=None, speed=None, wait=None):
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
        wait : bool
            (Default value = `None`) Whether to wait for output to return from the Mirobot before returning from the function. This value determines if the function will block until the operation recieves feedback. If `None`, use class default `BaseMirobot.wait` instead.

        Returns
        -------
        msg : List[str] or bool
            If `wait` is `True`, then return a list of strings which contains message output.
            If `wait` is `False`, then return whether sending the message succeeded.
        """
        if isinstance(x, MirobotAngles):
            inputs = x.asdict()

        else:
            inputs = {'x': x, 'y': y, 'z': z, 'a': a, 'b': b, 'c': c, 'd': d}

        return super().go_to_axis(**inputs,
                                  speed=speed, wait=wait)

    def increment_cartesian_lin(self, x=None, y=None, z=None, a=None, b=None, c=None, speed=None, wait=None):
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
        wait : bool
            (Default value = `None`) Whether to wait for output to return from the Mirobot before returning from the function. This value determines if the function will block until the operation recieves feedback. If `None`, use class default `BaseMirobot.wait` instead.

        Returns
        -------
        msg : List[str] or bool
            If `wait` is `True`, then return a list of strings which contains message output.
            If `wait` is `False`, then return whether sending the message succeeded.
        """
        if isinstance(x, MirobotCartesians):
            inputs = x.asdict()

        else:
            inputs = {'x': x, 'y': y, 'z': z, 'a': a, 'b': b, 'c': c}

        return super().increment_cartesian_lin(**inputs,
                                               speed=speed, wait=wait)

    def increment_cartesian_ptp(self, x=None, y=None, z=None, a=None, b=None, c=None, speed=None, wait=None):
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
        wait : bool
            (Default value = `None`) Whether to wait for output to return from the Mirobot before returning from the function. This value determines if the function will block until the operation recieves feedback. If `None`, use class default `BaseMirobot.wait` instead.

        Returns
        -------
        msg : List[str] or bool
            If `wait` is `True`, then return a list of strings which contains message output.
            If `wait` is `False`, then return whether sending the message succeeded.
        """
        if isinstance(x, MirobotCartesians):
            inputs = x.asdict()

        else:
            inputs = {'x': x, 'y': y, 'z': z, 'a': a, 'b': b, 'c': c}

        return super().increment_cartesian_ptp(**inputs,
                                               speed=speed, wait=wait)

    def increment_axis(self, x=None, y=None, z=None, a=None, b=None, c=None, d=None, speed=None, wait=None):
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
        wait : bool
            (Default value = `None`) Whether to wait for output to return from the Mirobot before returning from the function. This value determines if the function will block until the operation recieves feedback. If `None`, use class default `BaseMirobot.wait` instead.

        Returns
        -------
        msg : List[str] or bool
            If `wait` is `True`, then return a list of strings which contains message output.
            If `wait` is `False`, then return whether sending the message succeeded.
        """
        if isinstance(x, MirobotAngles):
            inputs = x.asdict()

        else:
            inputs = {'x': x, 'y': y, 'z': z, 'a': a, 'b': b, 'c': c, 'd': d}

        return super().increment_axis(**inputs,
                                      speed=speed, wait=wait)

    def increment_slide_rail(self, d, speed=None, wait=None):
        """
        Increment slide rail position a specified amount. (Command: `M21 G91`)

        Parameters
        ----------
        d : float
            Location of slide rail module.
        speed : int
            (Default value = `None`) The speed in which the Mirobot moves during this operation. (mm/s)
        wait : bool
            (Default value = `None`) Whether to wait for output to return from the Mirobot before returning from the function. This value determines if the function will block until the operation recieves feedback. If `None`, use class default `BaseMirobot.wait` instead.

        Returns
        -------
        msg : List[str] or bool
            If `wait` is `True`, then return a list of strings which contains message output.
            If `wait` is `False`, then return whether sending the message succeeded.
        """

        return super().increment_axis(d=d,
                                      speed=speed, wait=wait)

    def go_to_slide_rail(self, d, speed=None, wait=None):
        """
        Go to the slide rail position specified. (Command: `M21 G90`)

        Parameters
        ----------
        d : float
            Location of slide rail module.
        speed : int
            (Default value = `None`) The speed in which the Mirobot moves during this operation. (mm/s)
        wait : bool
            (Default value = `None`) Whether to wait for output to return from the Mirobot before returning from the function. This value determines if the function will block until the operation recieves feedback. If `None`, use class default `BaseMirobot.wait` instead.

        Returns
        -------
        msg : List[str] or bool
            If `wait` is `True`, then return a list of strings which contains message output.
            If `wait` is `False`, then return whether sending the message succeeded.
        """

        return super().go_to_axis(d=d,
                                  speed=speed, wait=wait)
    @property
    def pose(self):
        return self.cartesian