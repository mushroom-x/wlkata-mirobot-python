from collections.abc import Collection
from contextlib import AbstractContextManager
import logging
import os
from pathlib import Path
import re
import time
from typing import TextIO, BinaryIO

try:
    import importlib.resources as pkg_resources
except ImportError:
    # Try backported to PY<37 `importlib_resources`.
    import importlib_resources as pkg_resources

from .bluetooth_low_energy_interface import BluetoothLowEnergyInterface
from .serial_interface import SerialInterface
from .mirobot_status import MirobotStatus, MirobotAngles, MirobotCartesians
from .exceptions import ExitOnExceptionStreamHandler, MirobotError, MirobotAlarm, MirobotReset, MirobotAmbiguousPort, MirobotStatusError, MirobotResetFileError, MirobotVariableCommandError

os_is_nt = os.name == 'nt'
os_is_posix = os.name == 'posix'


class BaseMirobot(AbstractContextManager):
    """ A base class for managing and maintaining known Mirobot operations. """

    def __init__(self, *device_args, debug=True, connection_type='serial', autoconnect=True, autofindport=True, exclusive=True, valve_pwm_values=('65', '40'), pump_pwm_values=('0', '1000'), default_speed=2000, reset_file=None, wait=True, **device_kwargs):
        """
        Initialization of the `BaseMirobot` class.

        Parameters
        ----------
        *device_args : Any
             Arguments that are passed into the `mirobot.serial_device.SerialDevice` or `mirobot.bluetooth_low_energy_interface.BluetoothLowEnergyInterface` class.
        debug : bool
            (Default value = `False`) Whether to print gcode input and output to STDOUT. Stored in `BaseMirobot.debug`.
        connection_type : str
            (Default value = `'serial'`) Which type of connection to make to the Mirobot. By default, it will look for a serial port connection (eg. a physical wire connection). For bluetooth, provide `'bluetooth'` or `'bt'` for this parameter. To explicitly specify a serial port connection, use`'serial'` or `'ser'`.
        autoconnect : bool
            (Default value = `True`) Whether to automatically attempt a connection to the Mirobot at the end of class creation. If this is `True`, manually connecting with `BaseMirobot.connect` is unnecessary.
        autofindport : bool
            (Default value = `True`) Whether to automatically find the serial port that the Mirobot is attached to. If this is `False`, you must specify `portname='<portname>'` in `*serial_device_args`.
        valve_pwm_values : indexible-collection[str or numeric]
            (Default value = `('65', '40')`) The 'on' and 'off' values for the valve in terms of PWM. Useful if your Mirobot is not calibrated correctly and requires different values to open and close. `BaseMirobot.set_valve` will only accept booleans and the values in this parameter, so if you have additional values you'd like to use, pass them in as additional elements in this tuple. Stored in `BaseMirobot.valve_pwm_values`.
        pump_pwm_values : indexible-collection[str or numeric]
            (Default value = `('0', '1000')`) The 'on' and 'off' values for the pnuematic pump in terms of PWM. Useful if your Mirobot is not calibrated correctly and requires different values to open and close. `BaseMirobot.set_air_pump` will only accept booleans and the values in this parameter, so if you have additional values you'd like to use, pass them in as additional elements in this tuple. Stored in `BaseMirobot.pump_pwm_values`.
        default_speed : int
            (Default value = `2000`) This speed value will be passed in at each motion command, unless speed is specified as a function argument. Having this explicitly specified fixes phantom `Unknown Feed Rate` errors. Stored in `BaseMirobot.default_speed`.
        reset_file : str or Path or Collection[str] or file-like
            (Default value = `None`) A file-like object, file-path, or str containing reset values for the Mirobot. The default (None) will use the commands in "reset.xml" provided by WLkata to reset the Mirobot. See `BaseMirobot.reset_configuration` for more details.
        wait : bool
            (Default value = `True`) Whether to wait for commands to return a status signifying execution has finished. Turns all move-commands into blocking function calls. Stored `BaseMirobot.wait`.
        **device_kwargs : Any
             Keywords that are passed into the `mirobot.serial_device.SerialDevice` or `mirobot.bluetooth_low_energy_interface.BluetoothLowEnergyInterface` class.

        Returns
        -------
        class : `BaseMirobot`
        """
        self.logger = logging.getLogger(__name__)
        """ The instance level logger. Of type `logging.Logger` """
        self.logger.setLevel(logging.DEBUG)

        self.stream_handler = ExitOnExceptionStreamHandler()
        self.stream_handler.setLevel(logging.DEBUG if debug else logging.INFO)

        formatter = logging.Formatter(f"[Mirobot Init] [%(levelname)s] %(message)s")
        self.stream_handler.setFormatter(formatter)
        self.logger.addHandler(self.stream_handler)

        self.device = None
        """ Object that controls the connection to the Mirobot. Can either be a `mirobot.serial_interface.SerialInterface` or `mirobot.bluetooth_low_energy_interface.BluetoothLowEnergyInterface` class."""
        # Parse inputs into SerialDevice
        if connection_type.lower() in ('serial', 'ser'):
            serial_device_init_fn = SerialInterface.__init__
            args_names = serial_device_init_fn.__code__.co_varnames[:serial_device_init_fn.__code__.co_argcount]
            args_dict = dict(zip(args_names, device_args))
            args_dict.update(device_kwargs)

            args_dict['mirobot'] = self
            args_dict['exclusive'] = exclusive
            args_dict['debug'] = debug
            args_dict['logger'] = self.logger
            args_dict['autofindport'] = autofindport

            # 设置设备为串口接口
            self.device = SerialInterface(**args_dict)
            # 设置端口名称
            self.default_portname = self.device.default_portname

        elif connection_type.lower() in ('bluetooth', 'bt'):
            bluetooth_device_init_fn = BluetoothLowEnergyInterface.__init__
            args_names = bluetooth_device_init_fn.__code__.co_varnames[:bluetooth_device_init_fn.__code__.co_argcount]
            args_dict = dict(zip(args_names, device_args))
            args_dict.update(device_kwargs)

            args_dict['mirobot'] = self
            args_dict['debug'] = debug
            args_dict['logger'] = self.logger
            args_dict['autofindaddress'] = autofindport

            self.device = BluetoothLowEnergyInterface(**args_dict)
            self.default_portname = self.device.address

        formatter = logging.Formatter(f"[{self.default_portname}] [%(levelname)s] %(message)s")
        self.stream_handler.setFormatter(formatter)
        # self.logger.addHandler(self.stream_handler)

        self.reset_file = pkg_resources.read_text('mirobot.resources', 'reset.xml') if reset_file is None else reset_file
        """ The reset commands to use when resetting the Mirobot. See `BaseMirobot.reset_configuration` for usage and details. """
        self._debug = debug
        """ Boolean that determines if every input and output is to be printed to the screen. """

        self.valve_pwm_values = tuple(str(n) for n in valve_pwm_values)
        """ Collection of values to use for PWM values for valve module. First value is the 'On' position while the second is the 'Off' position. Only these values may be permitted. """
        self.pump_pwm_values = tuple(str(n) for n in pump_pwm_values)
        """ Collection of values to use for PWM values for pnuematic pump module. First value is the 'On' position while the second is the 'Off' position. Only these values may be permitted. """
        self.default_speed = default_speed
        """ The default speed to use when issuing commands that involve the speed parameter. """
        self.wait = wait
        """ Boolean that determines if every command should wait for a status message to return before unblocking function evaluation. Can be overridden on an individual basis by providing the `wait=` parameter to all command functions. """

        self.status = MirobotStatus()
        """ Dataclass that holds tracks Mirobot's coordinates and pwm values among other quantities. See `mirobot.mirobot_status.MirobotStatus` for more details."""

        # do this at the very end, after everything is setup
        if autoconnect:
            self.connect()

    def __enter__(self):
        """ Magic method for contextManagers """
        return self

    def __exit__(self, *exc):
        """ Magic method for contextManagers """
        self.disconnect()

    def __del__(self):
        """ Magic method for object deletion """
        self.disconnect()

    def connect(self):
        self.device.connect()

    def disconnect(self):
        if getattr(self, 'device', None) is not None:
            self.device.disconnect()

    @property
    def is_connected(self):
        return self.device.is_connected

    @property
    def debug(self):
        """ Return the `debug` property of `BaseMirobot` """
        return self._debug

    @debug.setter
    def debug(self, value):
        """
        Set the new value for the `debug` property of `mirobot.base_mirobot.BaseMirobot`. Use as in `BaseMirobot.setDebug(value)`.
        Use this setter method as it will also update the logging objects of `mirobot.base_mirobot.BaseMirobot` and its `mirobot.serial_device.SerialDevice`. As opposed to setting `mirobot.base_mirobot.BaseMirobot._debug` directly which will not update the loggers.

        Parameters
        ----------
        value : bool
            The new value for `mirobot.base_mirobot.BaseMirobot._debug`.

        """
        self._debug = bool(value)
        self.stream_handler.setLevel(logging.DEBUG if self._debug else logging.INFO)
        self.device.setDebug(value)

    def send_msg(self, msg, var_command=False, disable_debug=False, terminator=os.linesep, wait=None, wait_idle=False):
        """
        Send a message to the Mirobot.
        给Mirobot发送信息

        Parameters
        ----------
        msg : str or bytes
             A message or instruction to send to the Mirobot.
             要发送给Mirobot的指令
        var_command : bool
            (Default value = `False`) Whether `msg` is a variable command (of form `$num=value`). Will throw an error if does not validate correctly.
            是否为数值指令，若设置为数值设置指令，会对数值范围进行校验，如果不满足要求会报错
        disable_debug : bool
            (Default value = `False`) Whether to override the class debug setting. Used primarily by ` BaseMirobot.device.wait_until_idle`.
        terminator : str
            (Default value = `os.linesep`) The line separator to use when signaling a new line. Usually `'\\r\\n'` for windows and `'\\n'` for modern operating systems.
            设置字符串的换行符，Windows下一般为`'\\r\\n'`
        wait : bool
            (Default value = `None`) Whether to wait for output to end and to return that output. If `None`, use class default `BaseMirobot.wait` instead.
            是否阻塞式等待，直到等到信息回读
        wait_idle : bool
            (Default value = `False`) Whether to wait for Mirobot to be idle before returning.
            是否等待Mirbot转换为Idle空闲状态再发送指令
        Returns
        -------
        msg : List[str] or bool
            If `wait` is `True`, then return a list of strings which contains message output.
            If `wait` is `False`, then return whether sending the message succeeded.
        """
        if self.is_connected:
            # convert to str from bytes
            # 将字符串转换为字节
            if isinstance(msg, bytes):
                msg = str(msg, 'utf-8')
            
            # remove any newlines
            msg = msg.strip()

            # check if this is supposed to be a variable command and fail if not
            # 如果是数值设置指令，则进行合法性检测
            if var_command and not re.fullmatch(r'\$\d+=[\d\.]+', msg):
                self.logger.exception(MirobotVariableCommandError("Message is not a variable command: " + msg))

            # actually send the message
            output = self.device.send(msg,
                                      disable_debug=disable_debug,
                                      terminator=os.linesep,
                                      wait=(wait or (wait is None and self.wait)),
                                      wait_idle=wait_idle)

            return output

        else:
            raise Exception('Mirobot is not Connected!')

    def get_status(self, disable_debug=False):
        """
        Get the status of the Mirobot. (Command: `?`)

        Parameters
        ----------
        disable_debug : bool
            (Default value = `False`) Whether to override the class debug setting. Used primarily by `BaseMirobot.device.wait_until_idle`.

        Returns
        -------
        msg : List[str]
            The list of strings returned from a '?' status command.

        """
        instruction = '?'
        # we don't want to wait for idle when checking status-- this leads to unbroken recursion!!
        return self.send_msg(instruction, disable_debug=disable_debug, wait=True, wait_idle=False)

    def update_status(self, disable_debug=False):
        """
        Update the status of the Mirobot.
        更新Mirobot的状态

        Parameters
        ----------
        disable_debug : bool
            (Default value = `False`) Whether to override the class debug setting. Used primarily by `BaseMirobot.device.wait_until_idle`.

        """
        # get only the status message and not 'ok'
        # 设置状态信息
        # 因为存在信息丢包的可能,因此需要多查询几次
        while True:
            status = None
            status_str_list = self.get_status(disable_debug=disable_debug)

            for msg_seg in status_str_list:
                if "<" in msg_seg:
                    status_msg = msg_seg
                    try:
                        ret, status = self._parse_status(status_msg)
                        if ret:
                            break
                    except Exception as e:
                        print(e)
            if status is not None:
                break
            # 等待一会儿
            time.sleep(0.1)
        self._set_status(status)

    def _set_status(self, status):
        """
        Set the status object given as the instance's new status.
        设置新的状态

        Parameters
        ----------
        status : `mirobot.mirobot_status.MirobotStatus`
            The new status object of this instance.

        """
        self.status = status

    def _parse_status(self, msg):
        """
        Parse the status string of the Mirobot and store the various values as class variables.
        从字符串中解析Mirbot返回的状态信息, 提取有关变量赋值给机械臂对象

        Parameters
        ----------
        msg : str
            Status string that is obtained from a '?' instruction or `BaseMirobot.get_status` call.

        Returns
        -------
        return_status : MirobotStatus
            A new `mirobot.mirobot_status.MirobotStatus` object containing the new values obtained from `msg`.
        """

        return_status = MirobotStatus()
        # 用正则表达式进行匹配
        state_regex = r'<([^,]*),Angle\(ABCDXYZ\):([-\.\d,]*),Cartesian coordinate\(XYZ RxRyRz\):([-.\d,]*),Pump PWM:(\d+),Valve PWM:(\d+),Motion_MODE:(\d)>'

        regex_match = re.match(state_regex, msg)# re.fullmatch(state_regex, msg)
        
        if regex_match:
            try:
                state, angles, cartesians, pump_pwm, valve_pwm, motion_mode = regex_match.groups()

                return_angles = MirobotAngles(**dict(zip('xyzdabc', map(float, angles.split(',')))))

                return_cartesians = MirobotCartesians(*map(float, cartesians.split(',')))

                return_status = MirobotStatus(state,
                                              return_angles,
                                              return_cartesians,
                                              int(pump_pwm),
                                              int(valve_pwm),
                                              bool(motion_mode))
                return True, return_status
            except Exception as exception:
                # self.logger.exception(MirobotStatusError(f"Could not parse status message \"{msg}\" \n{str(exception)}"),
                #                       exc_info=exception)
                print(f"Could not parse status message \"{msg}\"")
        else:
            # self.logger.error(MirobotStatusError(f"Could not parse status message \"{msg}\""))
            print(f"Could not parse status message \"{msg}\"")
            
        return False, None

    def home_individual(self, wait=None):
        """
        Home each axis individually. (Command: `$HH`)
        每个轴依次Homing, 耗时比较久

        Parameters
        ----------
        wait : bool
            (Default value = `None`) Whether to wait for output to return from the Mirobot before returning from the function. This value determines if the function will block until the operation recieves feedback. If `None`, use class default `BaseMirobot.wait` instead.

        Returns
        -------
        msg : List[str] or bool
            If `wait` is `True`, then return a list of strings which contains message output.
            If `wait` is `False`, then return whether sending the message succeeded.
        """
        msg = '$HH'
        return self.send_msg(msg, wait=wait, wait_idle=True)

    def home_simultaneous(self, wait=None):
        """
        Home all axes simultaneously. (Command:`$H`)
        机械臂多轴同时复位

        Parameters
        ----------
        wait : bool
            (Default value = `None`) Whether to wait for output to return from the Mirobot before returning from the function. This value determines if the function will block until the operation recieves feedback. If `None`, use class default `BaseMirobot.wait` instead.

        Returns
        -------
        msg : List[str] or bool
            If `wait` is `True`, then return a list of strings which contains message output.
            If `wait` is `False`, then return whether sending the message succeeded.
        """
        msg = '$H'
        # return self.send_msg(msg, wait=wait, wait_idle=True)
        # 取消了homing之后需要等待Idle的约束
        return self.send_msg(msg, wait=wait, wait_idle=False)

    def set_hard_limit(self, state, wait=None):
        """
        Set the hard limit state.
        设置是否开启硬件限位

        Parameters
        ----------
        state : bool
            Whether to use the hard limit (`True`) or not (`False`).
            是否使用硬件限位
        wait : bool
            (Default value = `None`) Whether to wait for output to return from the Mirobot before returning from the function. This value determines if the function will block until the operation recieves feedback. If `None`, use class default `BaseMirobot.wait` instead.
            是否阻塞式等待

        Returns
        -------
        msg : List[str] or bool
            If `wait` is `True`, then return a list of strings which contains message output.
            If `wait` is `False`, then return whether sending the message succeeded.
        """
        msg = f'$21={int(state)}'
        return self.send_msg(msg, var_command=True, wait=wait)

    # set the soft limit state
    def set_soft_limit(self, state, wait=None):
        """
        Set the soft limit state.
        是否开启软限位

        Parameters
        ----------
        state : bool
            Whether to use the soft limit (`True`) or not (`False`).
        wait : bool
            (Default value = `None`) Whether to wait for output to return from the Mirobot before returning from the function. This value determines if the function will block until the operation recieves feedback. If `None`, use class default `BaseMirobot.wait` instead.

        Returns
        -------
        msg : List[str] or bool
             If `wait` is `True`, then return a list of strings which contains message output.
             If `wait` is `False`, then return whether sending the message succeeded.
        """
        msg = f'$20={int(state)}'
        return self.send_msg(msg, var_command=True, wait=wait)

    def unlock_shaft(self, wait=None):
        """
        Unlock each axis on the Mirobot. Homing naturally removes the lock. (Command: `M50`)
        将Mirobot的每个轴解锁。执行完成Homing之后会自动解锁

        Parameters
        ----------
        wait : bool
            (Default value = `None`) Whether to wait for output to return from the Mirobot before returning from the function. This value determines if the function will block until the operation recieves feedback. If `None`, use class default `BaseMirobot.wait` instead.
            是否阻塞式等待

        Returns
        -------
        msg : List[str] or bool
            If `wait` is `True`, then return a list of strings which contains message output.
            If `wait` is `False`, then return whether sending the message succeeded.
        """
        msg = 'M50'
        return self.send_msg(msg, wait=wait)

    @staticmethod
    def _generate_args_string(instruction, pairings):
        """
        A helper methods to generate argument strings for the various movement instructions.

        Parameters
        ----------
        instruction : str
            The command to include at the beginning of the string.
        pairings : dict[str:Any]
            A dictionary containing the pairings of argument name to argument value.
            If a value is `None`, it and its argument name is not included in the result.

        Returns
        -------
        msg : List[str] or bool
            If `wait` is `True`, then return a list of strings which contains message output.
            If `wait` is `False`, then return whether sending the message succeeded.
message
            A string containing the base command followed by the correctly formatted arguments.
        """
        args = [f'{arg_key}{value}' for arg_key, value in pairings.items() if value is not None]

        return ' '.join([instruction] + args)
    
    def set_joint_angle(self, joint_angles, speed=None, wait=None):
        """
        设置机械臂关节的角度
        
        Parameters
        ----------
        joint_angles : dict
            目标关节角度字典, key是关节的ID号, value是角度(单位°)
            举例: {1:45.0, 2:-30.0}
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
        for joint_i in range(1, 8):
            # 补齐缺失的角度
            if joint_i not in joint_angles:
                joint_angles[joint_i] = None

        return self.go_to_axis(x=joint_angles[1], y=joint_angles[2], z=joint_angles[3], a=joint_angles[4], \
            b=joint_angles[5], c=joint_angles[6], d=joint_angles[7], speed=speed, wait=wait)

    def go_to_axis(self, x=None, y=None, z=None, a=None, b=None, c=None, d=None, speed=None, wait=None):
        """
        Send all axes to a specific position in angular coordinates. (Command: `M21 G90`)

        Parameters
        ----------
        x : float
            (Default value = `None`) Angle of axis 1.
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
        instruction = 'M21 G90'  # X{x} Y{y} Z{z} A{a} B{b} C{c} F{speed}
        if not speed:
            speed = self.default_speed
        if speed:
            speed = int(speed)

        pairings = {'X': x, 'Y': y, 'Z': z, 'A': a, 'B': b, 'C': c, 'D': d, 'F': speed}
        msg = self._generate_args_string(instruction, pairings)

        return self.send_msg(msg, wait=wait, wait_idle=True)

    def increment_axis(self, x=None, y=None, z=None, a=None, b=None, c=None, d=None, speed=None, wait=None):
        """
        Increment all axes a specified amount in angular coordinates. (Command: `M21 G91`)

        Parameters
        ----------
        x : float
            (Default value = `None`) Angle of axis 1.
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
        instruction = 'M21 G91'  # X{x} Y{y} Z{z} A{a} B{b} C{c} F{speed}

        if not speed:
            speed = self.default_speed
        if speed:
            speed = int(speed)

        pairings = {'X': x, 'Y': y, 'Z': z, 'A': a, 'B': b, 'C': c, 'D': d, 'F': speed}
        msg = self._generate_args_string(instruction, pairings)

        return self.send_msg(msg, wait=wait, wait_idle=True)

    def go_to_cartesian_ptp(self, x=None, y=None, z=None, a=None, b=None, c=None, speed=None, wait=None):
        """
        Point-to-point move to a position in cartesian coordinates. (Command: `M20 G90 G0`)

        Parameters
        ----------
        x : float
            (Default value = `None`) X-axis position.
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
        instruction = 'M20 G90 G0'  # X{x} Y{y} Z{z} A{a} B{b} C{c} F{speed}

        if not speed:
            speed = self.default_speed
        if speed:
            speed = int(speed)

        pairings = {'X': x, 'Y': y, 'Z': z, 'A': a, 'B': b, 'C': c, 'F': speed}
        msg = self._generate_args_string(instruction, pairings)

        return self.send_msg(msg, wait=wait, wait_idle=True)

    def go_to_cartesian_lin(self, x=None, y=None, z=None, a=None, b=None, c=None, speed=None, wait=None):
        """
        Linear move to a position in cartesian coordinates. (Command: `M20 G90 G1`)

        Parameters
        ----------
        x : float
            (Default value = `None`) X-axis position.
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
        instruction = 'M20 G90 G1'  # X{x} Y{y} Z{z} A{a} B{b} C{c} F{speed}

        if not speed:
            speed = self.default_speed
        if speed:
            speed = int(speed)

        pairings = {'X': x, 'Y': y, 'Z': z, 'A': a, 'B': b, 'C': c, 'F': speed}
        msg = self._generate_args_string(instruction, pairings)

        return self.send_msg(msg, wait=wait, wait_idle=True)

    def increment_cartesian_ptp(self, x=None, y=None, z=None, a=None, b=None, c=None, speed=None, wait=None):
        """
        Point-to-point increment in cartesian coordinates. (Command: `M20 G91 G0`)

        Parameters
        ----------
        x : float
            (Default value = `None`) X-axis position.
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
        instruction = 'M20 G91 G0'  # X{x} Y{y} Z{z} A{a} B{b} C{c} F{speed}

        if not speed:
            speed = self.default_speed
        if speed:
            speed = int(speed)

        pairings = {'X': x, 'Y': y, 'Z': z, 'A': a, 'B': b, 'C': c, 'F': speed}
        msg = self._generate_args_string(instruction, pairings)

        return self.send_msg(msg, wait=wait, wait_idle=True)

    def increment_cartesian_lin(self, x=None, y=None, z=None, a=None, b=None, c=None, speed=None, wait=None):
        """
        Linear increment in cartesian coordinates. (Command: `M20 G91 G1`)

        Parameters
        ----------
        x : float
            (Default value = `None`) X-axis position
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
        instruction = 'M20 G91 G1'  # X{x} Y{y} Z{z} A{a} B{b} C{c} F{speed}

        if not speed:
            speed = self.default_speed
        if speed:
            speed = int(speed)

        pairings = {'X': x, 'Y': y, 'Z': z, 'A': a, 'B': b, 'C': c, 'F': speed}
        msg = self._generate_args_string(instruction, pairings)

        return self.send_msg(msg, wait=wait, wait_idle=True)

    def pump_on(self):
        """
        气泵开启, 吸气
        """
        # pump_pwm_values=('0', '1000')
        self.set_air_pump(self.pump_pwm_values[1]) # 气泵打开
    
    def pump_off(self):
        """
        气泵关闭, 电磁阀开启, 放气
        """
        # valve_pwm_values=('65', '40'),
        self.set_air_pump(self.pump_pwm_values[0], wait=False) # 气泵关闭
        self.set_valve(self.valve_pwm_values[1], wait=False) # 电磁阀打开
        time.sleep(1)
        self.set_valve(self.valve_pwm_values[0], wait=False) # 电磁阀关闭

    # set the pwm of the air pump
    def set_air_pump(self, pwm, wait=None):
        """
        Sets the PWM of the pnuematic pump module.
        设置气泵的PWM信号

        Parameters
        ----------
        pwm : int
            The pulse width modulation frequency to use.
        wait : bool
            (Default value = `None`) Whether to wait for output to return from the Mirobot before returning from the function. This value determines if the function will block until the operation recieves feedback. If `None`, use class default `BaseMirobot.wait` instead.

        Returns
        -------
        msg : List[str] or bool
            If `wait` is `True`, then return a list of strings which contains message output.
            If `wait` is `False`, then return whether sending the message succeeded.
        """

        if isinstance(pwm, bool):
            pwm = self.pump_pwm_values[not pwm]

        if str(pwm) not in self.pump_pwm_values:
            self.logger.exception(ValueError(f'pwm must be one of these values: {self.pump_pwm_values}. Was given {pwm}.'))

        msg = f'M3S{pwm}'
        return self.send_msg(msg, wait=wait, wait_idle=True)

    def set_valve(self, pwm, wait=None):
        """
        Sets the PWM of the valve module.

        Parameters
        ----------
        pwm : int
            The pulse width modulation frequency to use.
        wait : bool
            (Default value = `None`) Whether to wait for output to return from the Mirobot before returning from the function. This value determines if the function will block until the operation recieves feedback. If `None`, use class default `BaseMirobot.wait` instead.

        Returns
        -------
        msg : List[str] or bool
            If `wait` is `True`, then return a list of strings which contains message output.
            If `wait` is `False`, then return whether sending the message succeeded.
        """

        if isinstance(pwm, bool):
            pwm = self.valve_pwm_values[not pwm]

        if str(pwm) not in self.valve_pwm_values:
            self.logger.exception(ValueError(f'pwm must be one of these values: {self.valve_pwm_values}. Was given {pwm}.'))

        msg = f'M4E{pwm}'
        return self.send_msg(msg, wait=wait, wait_idle=True)

    def start_calibration(self, wait=None):
        """
        Starts the calibration sequence by setting all eeprom variables to zero. (Command: `M40`)

        Parameters
        ----------
        wait : bool
            (Default value = `None`) Whether to wait for output to return from the Mirobot before returning from the function. This value determines if the function will block until the operation recieves feedback. If `None`, use class default `BaseMirobot.wait` instead.

        Returns
        -------
        msg : List[str] or bool
             If `wait` is `True`, then return a list of strings which contains message output.
             If `wait` is `False`, then return whether sending the message succeeded.
        """
        instruction = 'M40'
        return self.send_msg(instruction, wait=wait)

    def finish_calibration(self, wait=None):
        """
        Stop the calibration sequence and write results into eeprom variables. (Command: `M41`)

        Parameters
        ----------
        wait : bool
            (Default value = `None`) Whether to wait for output to return from the Mirobot before returning from the function. This value determines if the function will block until the operation recieves feedback. If `None`, use class default `BaseMirobot.wait` instead.

        Returns
        -------
        msg : List[str] or bool
             If `wait` is `True`, then return a list of strings which contains message output.
             If `wait` is `False`, then return whether sending the message succeeded.
        """
        instruction = 'M41'
        return self.send_msg(instruction, wait=wait)

    def reset_configuration(self, reset_file=None, wait=None):
        """
        Reset the Mirobot by resetting all eeprom variables to their factory settings. If provided an explicit `reset_file` on invocation, it will execute reset commands given in by `reset_file` instead of `self.reset_file`.

        Parameters
        ----------
        reset_file : str or Path or Collection[str] or file-like
            (Default value = `True`) A file-like object, Collection, or string containing reset values for the Mirobot. If given a string with newlines, it will split on those newlines and pass those in as "variable reset commands". Passing in the default value (None) will use the commands in "reset.xml" provided by WLkata to reset the Mirobot. If passed in a string without newlines, `BaseMirobot.reset_configuration` will try to open the file specified by the string and read from it. A `Path` object will be processed similarly. With a Collection (list-like) object, `BaseMirobot.reset_configuration` will use each element as the message body for `BaseMirobot.send_msg`. One can also pass in file-like objects as well (like `open('path')`).
        wait : bool
            (Default value = `None`) Whether to wait for output to return from the Mirobot before returning from the function. This value determines if the function will block until the operation recieves feedback. If `None`, use class default `BaseMirobot.wait` instead.

        Returns
        -------
        msg : List[str] or bool
             If `wait` is `True`, then return a list of strings which contains message output.
             If `wait` is `False`, then return whether sending the message succeeded.
        """

        output = {}

        def send_each_line(file_lines):
            nonlocal output
            for line in file_lines:
                output[line] = self.send_msg(line, var_command=True, wait=wait)

        reset_file = reset_file if reset_file else self.reset_file

        if isinstance(reset_file, str) and '\n' in reset_file or \
           isinstance(reset_file, bytes) and b'\n' in reset_file:
            # if we find that we have a string and it contains new lines,
            send_each_line(reset_file.splitlines())

        elif isinstance(reset_file, (str, Path)):
            if not os.path.exists(reset_file):
                self.logger.exception(MirobotResetFileError("Reset file not found or reachable: {reset_file}"))
            with open(reset_file, 'r') as f:
                send_each_line(f.readlines())

        elif isinstance(reset_file, Collection) and not isinstance(reset_file, str):
            send_each_line(reset_file)

        elif isinstance(reset_file, (TextIO, BinaryIO)):
            send_each_line(reset_file.readlines())

        else:
            self.logger.exception(MirobotResetFileError(f"Unable to handle reset file of type: {type(reset_file)}"))

        return output
