"""
Mirobot GCode通信协议
"""

import math
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

# from .wlkata_mirobot_interface_bluetooth import BluetoothLowEnergyInterface
from .wlkata_mirobot_interface_serial import WlkataMirobotInterfaceSerial
from .wlkata_mirobot_status import MirobotStatus, MirobotAngles, MirobotCartesians
from .wlkata_mirobot_exceptions import ExitOnExceptionStreamHandler, MirobotError, MirobotAlarm, MirobotReset, MirobotAmbiguousPort, MirobotStatusError, MirobotResetFileError, MirobotVariableCommandError

# 判断操作系统的类型
# nt: 微软NT标准
os_is_nt = os.name == 'nt'
# Linux跟Mac都属于 posix 标准
# posix: 类Unix 操作系统的可移植API
os_is_posix = os.name == 'posix'


class WlkataMirobotGcodeProtocol(AbstractContextManager):
	""" A base class for managing and maintaining known Mirobot operations. """
	# 气泵PWM值
	AIR_PUMP_OFF_PWM_VALUE = 0
	AIR_PUMP_BLOWING_PWM_VALUE = 500
	AIR_PUMP_SUCTION_PWM_VALUE = 1000
	# 电磁阀PWM值
	VALVE_OFF_PWM_VALUE = 65
	VALVE_ON_PWM_VALUE = 40 
	# 机械爪张开与闭合的PWM值
	GRIPPER_OPEN_PWM_VALUE = 40
	GRIPPER_CLOSE_PWM_VALUE = 60
	# 爪子间距范围(单位mm)
	GRIPPER_SPACING_MIN = 0.0
	GRIPPER_SPACING_MAX = 30.0
	# 爪子运动学参数定义(单位mm)
	GRIPPER_LINK_A = 9.5    # 舵机舵盘与中心线之间的距离
	GRIPPER_LINK_B = 18.0   # 连杆的长度
	GRIPPER_LINK_C = 3.0    # 平行爪向内缩的尺寸
	
	def __init__(self, *device_args, debug=False, connection_type='serial', \
		autoconnect=True, autofindport=True, exclusive=True, \
		default_speed=2000, reset_file=None, wait_ok=False, **device_kwargs):
		"""
		Initialization of the `WlkataMirobotGcodeProtocol` class.
		初始化`WlkataMirobotGcodeProtocol`类
		
		Parameters
		----------
		*device_args : Any
			 Arguments that are passed into the `mirobot.serial_device.DeviceSerial` or `mirobot.wlkata_mirobot_interface_bluetooth.BluetoothLowEnergyInterface` class.
		debug : bool
			(Default value = `False`) Whether to print gcode input and output to STDOUT. Stored in `WlkataMirobotGcodeProtocol.debug`.
		connection_type : str
			(Default value = `'serial'`) Which type of connection to make to the Mirobot. By default, it will look for a serial port connection (eg. a physical wire connection). For bluetooth, provide `'bluetooth'` or `'bt'` for this parameter. To explicitly specify a serial port connection, use`'serial'` or `'ser'`.
			连接类型, 默认为串口连接.
			- `serial` 串口连接
			- `bluetooth` 蓝牙连接
		autoconnect : bool
			(Default value = `True`) Whether to automatically attempt a connection to the Mirobot at the end of class creation. If this is `True`, manually connecting with `WlkataMirobotGcodeProtocol.connect` is unnecessary.
		autofindport : bool
			(Default value = `True`) Whether to automatically find the serial port that the Mirobot is attached to. If this is `False`, you must specify `portname='<portname>'` in `*serial_device_args`.
		valve_pwm_values : indexible-collection[str or numeric]
			(Default value = `('65', '40')`) The 'on' and 'off' values for the valve in terms of PWM. Useful if your Mirobot is not calibrated correctly and requires different values to open and close. `WlkataMirobotGcodeProtocol.set_valve` will only accept booleans and the values in this parameter, so if you have additional values you'd like to use, pass them in as additional elements in this tuple. Stored in `WlkataMirobotGcodeProtocol.valve_pwm_values`.
		pump_pwm_values : indexible-collection[str or numeric]
			(Default value = `('0', '1000')`) The 'on' and 'off' values for the pnuematic pump in terms of PWM. Useful if your Mirobot is not calibrated correctly and requires different values to open and close. `WlkataMirobotGcodeProtocol.set_air_pump` will only accept booleans and the values in this parameter, so if you have additional values you'd like to use, pass them in as additional elements in this tuple. Stored in `WlkataMirobotGcodeProtocol.pump_pwm_values`.
		default_speed : int
			(Default value = `2000`) This speed value will be passed in at each motion command, unless speed is specified as a function argument. Having this explicitly specified fixes phantom `Unknown Feed Rate` errors. Stored in `WlkataMirobotGcodeProtocol.default_speed`.
		reset_file : str or Path or Collection[str] or file-like
			(Default value = `None`) A file-like object, file-path, or str containing reset values for the Mirobot. The default (None) will use the commands in "reset.xml" provided by WLkata to reset the Mirobot. See `WlkataMirobotGcodeProtocol.reset_configuration` for more details.
		wait_ok : bool
			(Default value = `True`) Whether to wait_ok for commands to return a status signifying execution has finished. Turns all move-commands into blocking function calls. Stored `WlkataMirobotGcodeProtocol.wait_ok`.
		**device_kwargs : Any
			 Keywords that are passed into the `mirobot.serial_device.DeviceSerial` or `mirobot.wlkata_mirobot_interface_bluetooth.BluetoothLowEnergyInterface` class.

		Returns
		-------
		class : `WlkataMirobotGcodeProtocol`
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
		""" Object that controls the connection to the Mirobot. Can either be a `mirobot.serial_interface.WlkataMirobotInterfaceSerial` or `mirobot.wlkata_mirobot_interface_bluetooth.BluetoothLowEnergyInterface` class."""
		# Parse inputs into DeviceSerial
		if connection_type.lower() in ('serial', 'ser'):
			# 创建串口连接
			serial_device_init_fn = WlkataMirobotInterfaceSerial.__init__
			args_names = serial_device_init_fn.__code__.co_varnames[:serial_device_init_fn.__code__.co_argcount]
			args_dict = dict(zip(args_names, device_args))
			args_dict.update(device_kwargs)

			args_dict['mirobot'] = self
			args_dict['exclusive'] = exclusive
			args_dict['debug'] = debug
			args_dict['logger'] = self.logger
			args_dict['autofindport'] = autofindport
			# 设置设备为串口接口
			self.device = WlkataMirobotInterfaceSerial(**args_dict)
			# 设置端口名称
			self.default_portname = self.device.default_portname

		# elif connection_type.lower() in ('bluetooth', 'bt'):
		# 	# 创建蓝牙连接
		# 	bluetooth_device_init_fn = BluetoothLowEnergyInterface.__init__
		# 	args_names = bluetooth_device_init_fn.__code__.co_varnames[:bluetooth_device_init_fn.__code__.co_argcount]
		# 	args_dict = dict(zip(args_names, device_args))
		# 	args_dict.update(device_kwargs)

		# 	args_dict['mirobot'] = self
		# 	args_dict['debug'] = debug
		# 	args_dict['logger'] = self.logger
		# 	args_dict['autofindaddress'] = autofindport

		# 	self.device = BluetoothLowEnergyInterface(**args_dict)
		# 	self.default_portname = self.device.address

		formatter = logging.Formatter(f"[{self.default_portname}] [%(levelname)s] %(message)s")
		self.stream_handler.setFormatter(formatter)
		# self.logger.addHandler(self.stream_handler)
		# 读取重置文件
		self.reset_file = pkg_resources.read_text('wlkata_mirobot.resources', 'reset.xml') if reset_file is None else reset_file
		""" The reset commands to use when resetting the Mirobot. See `WlkataMirobotGcodeProtocol.reset_configuration` for usage and details. """
		self._debug = debug
		""" Boolean that determines if every input and output is to be printed to the screen. """
		
		""" Collection of values to use for PWM values for valve module. First value is the 'On' position while the second is the 'Off' position. Only these values may be permitted. """
		# 气泵PWM值
		self.pump_pwm_values = [
			self.AIR_PUMP_SUCTION_PWM_VALUE,
			self.AIR_PUMP_BLOWING_PWM_VALUE,
			self.AIR_PUMP_OFF_PWM_VALUE
		]
		# 电磁阀PWM值
		self.valve_pwm_values = [
			self.VALVE_OFF_PWM_VALUE,
			self.VALVE_ON_PWM_VALUE
		]
		# self.pump_pwm_values = tuple(str(n) for n in pump_pwm_values)
		""" Collection of values to use for PWM values for pnuematic pump module. First value is the 'On' position while the second is the 'Off' position. Only these values may be permitted. """
		self.default_speed = default_speed
		""" The default speed to use when issuing commands that involve the speed parameter. """
		self.wait_ok = wait_ok
		""" Boolean that determines if every command should wait_ok for a status message to return before unblocking function evaluation. Can be overridden on an individual basis by providing the `wait_ok=` parameter to all command functions. """

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
		"""连接设备"""
		self.device.connect()

	def disconnect(self):
		if getattr(self, 'device', None) is not None:
			self.device.disconnect()

	@property
	def is_connected(self):
		return self.device.is_connected

	@property
	def debug(self):
		""" Return the `debug` property of `WlkataMirobotGcodeProtocol` """
		return self._debug

	@debug.setter
	def debug(self, value):
		"""
		Set the new value for the `debug` property of `mirobot.wlkata_mirobot_gcode_protocol.WlkataMirobotGcodeProtocol`. Use as in `WlkataMirobotGcodeProtocol.setDebug(value)`.
		Use this setter method as it will also update the logging objects of `mirobot.wlkata_mirobot_gcode_protocol.WlkataMirobotGcodeProtocol` and its `mirobot.serial_device.DeviceSerial`. As opposed to setting `mirobot.wlkata_mirobot_gcode_protocol.WlkataMirobotGcodeProtocol._debug` directly which will not update the loggers.

		Parameters
		----------
		value : bool
			The new value for `mirobot.wlkata_mirobot_gcode_protocol.WlkataMirobotGcodeProtocol._debug`.

		"""
		self._debug = bool(value)
		self.stream_handler.setLevel(logging.DEBUG if self._debug else logging.INFO)
		self.device.setDebug(value)

	def send_msg(self, msg, var_command=False, disable_debug=False, terminator=os.linesep, wait_ok=None, wait_idle=False):
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
			(Default value = `False`) Whether to override the class debug setting. Used primarily by ` WlkataMirobotGcodeProtocol.device.wait_until_idle`.
		terminator : str
			(Default value = `os.linesep`) The line separator to use when signaling a new line. Usually `'\\r\\n'` for windows and `'\\n'` for modern operating systems.
			设置字符串的换行符，Windows下一般为`'\\r\\n'`
		wait_ok : bool
			(Default value = `None`) Whether to wait_ok for output to end and to return that output. If `None`, use class default `WlkataMirobotGcodeProtocol.wait_ok` instead.
			是否阻塞式等待，直到等到信息回读
		wait_idle : bool
			(Default value = `False`) Whether to wait_ok for Mirobot to be idle before returning.
			在结束的时候，等待IDLE状态才返回
		Returns
		-------
		msg : List[str] or bool
			If `wait_ok` is `True`, then return a list of strings which contains message output.
			If `wait_ok` is `False`, then return whether sending the message succeeded.
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

			if wait_ok is None:
				wait_ok = False
			
			# actually send the message
			# 返回值是布尔值，代表是否正确发送
			ret = self.device.send(msg,
									  disable_debug=disable_debug,
									  terminator=os.linesep,
									  wait_ok=wait_ok,
									  wait_idle=wait_idle)

			return ret

		else:
			raise Exception('Mirobot is not Connected!')

	def send_cmd_get_status(self, disable_debug=False):
		"""
		Get the status of the Mirobot. (Command: `?`)
		获取Mirobot的状态信息

		Parameters
		----------
		disable_debug : bool
			(Default value = `False`) Whether to override the class debug setting. Used primarily by `WlkataMirobotGcodeProtocol.device.wait_until_idle`.

		Returns
		-------
		msg : List[str]
			The list of strings returned from a '?' status command.

		"""
		instruction = '?'
		ret = self.send_msg(instruction, disable_debug=disable_debug, wait_ok=False, wait_idle=False)
		recv_str = self.device.serial_device.readline(timeout=0.10) # .decode('utf-8')
		self.logger.debug(f"[RECV] {recv_str}")
		return recv_str

	def get_status(self, disable_debug=False):
		"""
		Update the status of the Mirobot.
		更新Mirobot的状态

		Parameters
		----------
		disable_debug : bool
			(Default value = `False`) Whether to override the class debug setting. Used primarily by `WlkataMirobotGcodeProtocol.device.wait_until_idle`.

		"""
		# get only the status message and not 'ok'
		# 设置状态信息
		# 因为存在信息丢包的可能,因此需要多查询几次
		while True:
			status = None
			msg_seg = self.send_cmd_get_status(disable_debug=disable_debug)
			if "<" in msg_seg and ">" in msg_seg:
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
			Status string that is obtained from a '?' instruction or `WlkataMirobotGcodeProtocol.get_status` call.

		Returns
		-------
		return_status : MirobotStatus
			A new `mirobot.mirobot_status.MirobotStatus` object containing the new values obtained from `msg`.
		"""

		return_status = MirobotStatus()
		# 用正则表达式进行匹配
		state_regex = r'<([^,]*),Angle\(ABCDXYZ\):([-\.\d,]*),Cartesian coordinate\(XYZ RxRyRz\):([-.\d,]*),Pump PWM:(\d+),Valve PWM:(\d+),Motion_MODE:(\d)>'
		# While re.search() searches for the whole string even if the string contains multi-lines and tries to find a match of the substring in all the lines of string.
		# 注: 把re.match改为re.search
		regex_match = re.search(state_regex, msg)# re.fullmatch(state_regex, msg)
		
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
				self.logger.exception(MirobotStatusError(f"Could not parse status message \"{msg}\" \n{str(exception)}"),
									   exc_info=exception)
		else:
			self.logger.error(MirobotStatusError(f"Could not parse status message \"{msg}\""))
			
		return False, None

	def home(self, has_slider=False):
		'''机械臂Homing'''
		if has_slider:
			return self.home_7axis()
		else:
			return self.home_6axis()
	
	def home_slider(self):
		'''滑台单独Homing'''
		return self.home_1axis(7)
	
	def home_1axis(self, axis_id):
		'''单轴Homing'''
		if not isinstance(axis_id, int) or not (axis_id >= 1 and axis_id <= 7):
			return False
		msg = f'$H{axis_id}'
		return self.send_msg(msg, wait_ok=False, wait_idle=True)
	
	def home_6axis(self):
		'''六轴Homing'''
		msg = f'$H'
		return self.send_msg(msg, wait_ok=False, wait_idle=True)
	
	def home_6axis_in_turn(self):
		'''六轴Homing, 各关节依次Homing'''
		msg = f'$HH'
		return self.send_msg(msg, wait_ok=False, wait_idle=True)
	
	def home_7axis(self):
		'''七轴Homing(本体 + 滑台)'''
		msg = f'$H0'
		return self.send_msg(msg, wait_ok=False, wait_idle=True)
		
	def unlock_all_axis(self):
		'''接触各轴锁定状态'''
		msg = 'M50'
		return self.send_msg(msg, wait_ok=True, wait_idle=True)
		
	def go_to_zero(self):
		'''回零-运动到名义上的各轴零点'''
		msg = '$M'
		return self.send_msg(msg, wait_ok=False, wait_idle=True)
	
	def set_speed(self, speed):
		'''设置转速'''
		# 转换为整数
		speed = int(speed)
		# 检查数值范围是否合法
		if speed <= 0 or speed > 3000:
			self.logger.error(MirobotStatusError(f"Illegal movement speed {speed}"))
			return False
		# 发送指令
		msg = f'F{speed}'
		return self.send_msg(msg, wait_ok=None, wait_idle=None)
	
	def set_hard_limit(self, state):
		"""
		Set the hard limit state.
		设置是否开启硬件限位

		Parameters
		----------
		state : bool
			Whether to use the hard limit (`True`) or not (`False`).
			是否使用硬件限位
		wait_ok : bool
			(Default value = `None`) Whether to wait_ok for output to return from the Mirobot before returning from the function. This value determines if the function will block until the operation recieves feedback. If `None`, use class default `WlkataMirobotGcodeProtocol.wait_ok` instead.
			是否阻塞式等待

		Returns
		-------
		msg : List[str] or bool
			If `wait_ok` is `True`, then return a list of strings which contains message output.
			If `wait_ok` is `False`, then return whether sending the message succeeded.
		"""
		msg = f'$21={int(state)}'
		return self.send_msg(msg, var_command=True, wait_ok=None)

	# set the soft limit state
	def set_soft_limit(self, state):
		"""
		Set the soft limit state.
		是否开启软限位

		Parameters
		----------
		state : bool
			Whether to use the soft limit (`True`) or not (`False`).
		wait_ok : bool
			(Default value = `None`) Whether to wait_ok for output to return from the Mirobot before returning from the function. This value determines if the function will block until the operation recieves feedback. If `None`, use class default `WlkataMirobotGcodeProtocol.wait_ok` instead.

		Returns
		-------
		msg : List[str] or bool
			 If `wait_ok` is `True`, then return a list of strings which contains message output.
			 If `wait_ok` is `False`, then return whether sending the message succeeded.
		"""
		msg = f'$20={int(state)}'
		return self.send_msg(msg, var_command=True, wait_ok=None)

	def unlock_shaft(self):
		"""
		Unlock each axis on the Mirobot. Homing naturally removes the lock. (Command: `M50`)
		将Mirobot的每个轴解锁。执行完成Homing之后会自动解锁

		Parameters
		----------
		wait_ok : bool
			(Default value = `None`) Whether to wait_ok for output to return from the Mirobot before returning from the function. This value determines if the function will block until the operation recieves feedback. If `None`, use class default `WlkataMirobotGcodeProtocol.wait_ok` instead.
			是否阻塞式等待

		Returns
		-------
		msg : List[str] or bool
			If `wait_ok` is `True`, then return a list of strings which contains message output.
			If `wait_ok` is `False`, then return whether sending the message succeeded.
		"""
		msg = 'M50'
		return self.send_msg(msg, wait_ok=None)

	def format_float_value(self, value):
		if value is None:
			return value
		if isinstance(value, float):
			# 精确到小数点后两位数
			return round(value , 2)
		else:
			return value
	
	def generate_args_string(self, instruction, pairings):
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
			If `wait_ok` is `True`, then return a list of strings which contains message output.
			If `wait_ok` is `False`, then return whether sending the message succeeded.
message
			A string containing the base command followed by the correctly formatted arguments.
		"""
		args = [f'{arg_key}{self.format_float_value(value)}' for arg_key, value in pairings.items() if value is not None]

		return ' '.join([instruction] + args)
	
	def set_joint_angle(self, joint_angles, speed=None, wait_ok=None):
		"""
		设置机械臂关节的角度
		
		Parameters
		----------
		joint_angles : dict
			目标关节角度字典, key是关节的ID号, value是角度(单位°)
			举例: {1:45.0, 2:-30.0}
		speed : int
			(Default value = `None`) The speed in which the Mirobot moves during this operation. (mm/s)
		wait_ok : bool
			(Default value = `None`) Whether to wait_ok for output to return from the Mirobot before returning from the function. This value determines if the function will block until the operation recieves feedback. If `None`, use class default `WlkataMirobotGcodeProtocol.wait_ok` instead.
			
		Returns
		-------
		msg : List[str] or bool
			If `wait_ok` is `True`, then return a list of strings which contains message output.
			If `wait_ok` is `False`, then return whether sending the message succeeded.
		"""
		for joint_i in range(1, 8):
			# 补齐缺失的角度
			if joint_i not in joint_angles:
				joint_angles[joint_i] = None

		return self.go_to_axis(x=joint_angles[1], y=joint_angles[2], z=joint_angles[3], a=joint_angles[4], \
			b=joint_angles[5], c=joint_angles[6], d=joint_angles[7], speed=speed, wait_ok=wait_ok)

	def go_to_axis(self, x=None, y=None, z=None, a=None, b=None, c=None, d=None, speed=None, wait_ok=None):
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
		wait_ok : bool
			(Default value = `None`) Whether to wait_ok for output to return from the Mirobot before returning from the function. This value determines if the function will block until the operation recieves feedback. If `None`, use class default `WlkataMirobotGcodeProtocol.wait_ok` instead.

		Returns
		-------
		msg : List[str] or bool
			If `wait_ok` is `True`, then return a list of strings which contains message output.
			If `wait_ok` is `False`, then return whether sending the message succeeded.
		"""
		instruction = 'M21 G90'  # X{x} Y{y} Z{z} A{a} B{b} C{c} F{speed}
		if not speed:
			speed = self.default_speed
		if speed:
			speed = int(speed)

		pairings = {'X': x, 'Y': y, 'Z': z, 'A': a, 'B': b, 'C': c, 'D': d, 'F': speed}
		msg = self.generate_args_string(instruction, pairings)

		return self.send_msg(msg, wait_ok=wait_ok, wait_idle=True)

	def increment_axis(self, x=None, y=None, z=None, a=None, b=None, c=None, d=None, speed=None, wait_ok=None):
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
		wait_ok : bool
			(Default value = `None`) Whether to wait_ok for output to return from the Mirobot before returning from the function. This value determines if the function will block until the operation recieves feedback. If `None`, use class default `WlkataMirobotGcodeProtocol.wait_ok` instead.

		Returns
		-------
		msg : List[str] or bool
			If `wait_ok` is `True`, then return a list of strings which contains message output.
			If `wait_ok` is `False`, then return whether sending the message succeeded.
		"""
		instruction = 'M21 G91'  # X{x} Y{y} Z{z} A{a} B{b} C{c} F{speed}
		if not speed:
			speed = self.default_speed
		if speed:
			speed = int(speed)
		pairings = {'X': x, 'Y': y, 'Z': z, 'A': a, 'B': b, 'C': c, 'D': d, 'F': speed}
		msg = self.generate_args_string(instruction, pairings)

		return self.send_msg(msg, wait_ok=wait_ok, wait_idle=True)

	def go_to_cartesian_ptp(self, x=None, y=None, z=None, a=None, b=None, c=None, speed=None, wait_ok=None):
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
		wait_ok : bool
			(Default value = `None`) Whether to wait_ok for output to return from the Mirobot before returning from the function. This value determines if the function will block until the operation recieves feedback. If `None`, use class default `WlkataMirobotGcodeProtocol.wait_ok` instead.

		Returns
		-------
		msg : List[str] or bool
			If `wait_ok` is `True`, then return a list of strings which contains message output.
			If `wait_ok` is `False`, then return whether sending the message succeeded.
		"""
		instruction = 'M20 G90 G0'  # X{x} Y{y} Z{z} A{a} B{b} C{c} F{speed}

		if not speed:
			speed = self.default_speed
		if speed:
			speed = int(speed)

		pairings = {'X': x, 'Y': y, 'Z': z, 'A': a, 'B': b, 'C': c, 'F': speed}
		msg = self.generate_args_string(instruction, pairings)

		return self.send_msg(msg, wait_ok=wait_ok, wait_idle=True)

	def go_to_cartesian_lin(self, x=None, y=None, z=None, a=None, b=None, c=None, speed=None, wait_ok=None):
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
		wait_ok : bool
			(Default value = `None`) Whether to wait_ok for output to return from the Mirobot before returning from the function. This value determines if the function will block until the operation recieves feedback. If `None`, use class default `WlkataMirobotGcodeProtocol.wait_ok` instead.

		Returns
		-------
		msg : List[str] or bool
			If `wait_ok` is `True`, then return a list of strings which contains message output.
			If `wait_ok` is `False`, then return whether sending the message succeeded.
		"""
		instruction = 'M20 G90 G1'  # X{x} Y{y} Z{z} A{a} B{b} C{c} F{speed}

		if not speed:
			speed = self.default_speed
		if speed:
			speed = int(speed)

		pairings = {'X': x, 'Y': y, 'Z': z, 'A': a, 'B': b, 'C': c, 'F': speed}
		msg = self.generate_args_string(instruction, pairings)

		return self.send_msg(msg, wait_ok=wait_ok, wait_idle=True)

	def increment_cartesian_ptp(self, x=None, y=None, z=None, a=None, b=None, c=None, speed=None, wait_ok=None):
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
		wait_ok : bool
			(Default value = `None`) Whether to wait_ok for output to return from the Mirobot before returning from the function. This value determines if the function will block until the operation recieves feedback. If `None`, use class default `WlkataMirobotGcodeProtocol.wait_ok` instead.

		Returns
		-------
		msg : List[str] or bool
			If `wait_ok` is `True`, then return a list of strings which contains message output.
			If `wait_ok` is `False`, then return whether sending the message succeeded.
		"""
		instruction = 'M20 G91 G0'  # X{x} Y{y} Z{z} A{a} B{b} C{c} F{speed}

		if not speed:
			speed = self.default_speed
		if speed:
			speed = int(speed)

		pairings = {'X': x, 'Y': y, 'Z': z, 'A': a, 'B': b, 'C': c, 'F': speed}
		msg = self.generate_args_string(instruction, pairings)

		return self.send_msg(msg, wait_ok=wait_ok, wait_idle=True)

	def increment_cartesian_lin(self, x=None, y=None, z=None, a=None, b=None, c=None, speed=None, wait_ok=None):
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
		wait_ok : bool
			(Default value = `None`) Whether to wait_ok for output to return from the Mirobot before returning from the function. This value determines if the function will block until the operation recieves feedback. If `None`, use class default `WlkataMirobotGcodeProtocol.wait_ok` instead.

		Returns
		-------
		msg : List[str] or bool
			If `wait_ok` is `True`, then return a list of strings which contains message output.
			If `wait_ok` is `False`, then return whether sending the message succeeded.
		"""
		instruction = 'M20 G91 G1'  # X{x} Y{y} Z{z} A{a} B{b} C{c} F{speed}

		if not speed:
			speed = self.default_speed
		if speed:
			speed = int(speed)

		pairings = {'X': x, 'Y': y, 'Z': z, 'A': a, 'B': b, 'C': c, 'F': speed}
		msg = self.generate_args_string(instruction, pairings)

		return self.send_msg(msg, wait_ok=wait_ok, wait_idle=True)
	
	def pump_suction(self):
		'''气泵吸气'''
		self.set_air_pump(self.AIR_PUMP_SUCTION_PWM_VALUE) 
	
	def pump_blowing(self):
		'''气泵吹气'''
		self.set_air_pump(self.AIR_PUMP_BLOWING_PWM_VALUE)
	
	def pump_on(self, is_suction=True):
		"""
		气泵开启, 吸气/吹气
		"""
		if is_suction:
			self.set_air_pump(self.AIR_PUMP_SUCTION_PWM_VALUE)
		else:
			self.set_air_pump(self.AIR_PUMP_BLOWING_PWM_VALUE) 
	
	def pump_off(self):
		"""
		气泵关闭, 电磁阀开启, 放气
		"""
		self.set_air_pump(self.AIR_PUMP_OFF_PWM_VALUE, wait_ok=False)
		self.set_valve(self.VALVE_ON_PWM_VALUE, wait_ok=False)
		time.sleep(1)
		self.set_valve(self.VALVE_OFF_PWM_VALUE, wait_ok=False)
		
	# set the pwm of the air pump
	def set_air_pump(self, pwm, wait_ok=None):
		"""
		Sets the PWM of the pnuematic pump module.
		设置气泵的PWM信号

		Parameters
		----------
		pwm : int
			The pulse width modulation frequency to use.
		wait_ok : bool
			(Default value = `None`) Whether to wait_ok for output to return from the Mirobot before returning from the function. This value determines if the function will block until the operation recieves feedback. If `None`, use class default `WlkataMirobotGcodeProtocol.wait_ok` instead.

		Returns
		-------
		msg : List[str] or bool
			If `wait_ok` is `True`, then return a list of strings which contains message output.
			If `wait_ok` is `False`, then return whether sending the message succeeded.
		"""
		
		if pwm not in self.pump_pwm_values:
			self.logger.exception(ValueError(f'pwm must be one of these values: {self.pump_pwm_values}. Was given {pwm}.'))
			pwm = self.AIR_PUMP_OFF_PWM_VALUE
		msg = f'M3S{pwm}'
		return self.send_msg(msg, wait_ok=wait_ok, wait_idle=True)

	def set_valve(self, pwm, wait_ok=None):
		"""
		Sets the PWM of the valve module.

		Parameters
		----------
		pwm : int
			The pulse width modulation frequency to use.
		wait_ok : bool
			(Default value = `None`) Whether to wait_ok for output to return from the Mirobot before returning from the function. This value determines if the function will block until the operation recieves feedback. If `None`, use class default `WlkataMirobotGcodeProtocol.wait_ok` instead.

		Returns
		-------
		msg : List[str] or bool
			If `wait_ok` is `True`, then return a list of strings which contains message output.
			If `wait_ok` is `False`, then return whether sending the message succeeded.
		"""
		if pwm not in self.valve_pwm_values:
			self.logger.exception(ValueError(f'pwm must be one of these values: {self.valve_pwm_values}. Was given {pwm}.'))
			pwm = self.VALVE_OFF_PWM_VALUE
		msg = f'M4E{pwm}'
		return self.send_msg(msg, wait_ok=wait_ok, wait_idle=True)
	
	def gripper_inverse_kinematic(self, spacing_mm):
		'''爪子逆向运动学'''
		d1 = (spacing_mm / 2) + self.GRIPPER_LINK_C - self.GRIPPER_LINK_A
		theta = math.degrees(math.asin(d1/self.GRIPPER_LINK_B))
		return theta
	
	def set_gripper_spacing(self, spacing_mm):
		'''设置爪子间距'''
		# 判断是否是合法的spacing约束下
		spacing_mm = max(self.GRIPPER_SPACING_MIN, min(self.GRIPPER_SPACING_MAX, spacing_mm))
		# 逆向运动学
		theta = self.gripper_inverse_kinematic(spacing_mm)
		angle_min = self.gripper_inverse_kinematic(self.GRIPPER_SPACING_MIN)
		angle_max = self.gripper_inverse_kinematic(self.GRIPPER_SPACING_MAX)
		# 旋转角度转换为PWM值
		ratio = ((theta - angle_min) / (angle_max - angle_min))
		pwm = int(self.GRIPPER_CLOSE_PWM_VALUE + ratio * (self.GRIPPER_OPEN_PWM_VALUE - self.GRIPPER_CLOSE_PWM_VALUE))
		print(f"爪子逆向运动学 角度:{theta}  angle_min: {angle_min} angle_max: {angle_max} PWM: {pwm}")
		# 设置爪子的PWM
		self.set_gripper(pwm)
		
	def gripper_open(self):
		'''爪子开启'''
		self.set_gripper(self.GRIPPER_OPEN_PWM_VALUE)
	
	def gripper_close(self):
		'''爪子闭合'''
		self.set_gripper(self.GRIPPER_CLOSE_PWM_VALUE)
	
	def set_gripper(self, pwm, wait_ok=None):
		'''设置爪子的PWM'''
		# 类型约束
		if isinstance(pwm, bool):
			if pwm == True:
				pwm = self.GRIPPER_CLOSE_PWM_VALUE
			else:
				pwm = self.GRIPPER_OPEN_PWM_VALUE
		pwm = int(pwm)
		# 数值约束
		lowerb = min([self.GRIPPER_OPEN_PWM_VALUE, self.GRIPPER_CLOSE_PWM_VALUE])
		upperb = max([self.GRIPPER_OPEN_PWM_VALUE, self.GRIPPER_CLOSE_PWM_VALUE])
		pwm = max(lowerb, min(upperb, pwm))
		
		msg = f'M3S{pwm}'
		return self.send_msg(msg, wait_ok=wait_ok, wait_idle=True)
	
	def start_calibration(self, wait_ok=None):
		"""
		Starts the calibration sequence by setting all eeprom variables to zero. (Command: `M40`)

		Parameters
		----------
		wait_ok : bool
			(Default value = `None`) Whether to wait_ok for output to return from the Mirobot before returning from the function. This value determines if the function will block until the operation recieves feedback. If `None`, use class default `WlkataMirobotGcodeProtocol.wait_ok` instead.

		Returns
		-------
		msg : List[str] or bool
			 If `wait_ok` is `True`, then return a list of strings which contains message output.
			 If `wait_ok` is `False`, then return whether sending the message succeeded.
		"""
		instruction = 'M40'
		return self.send_msg(instruction, wait_ok=wait_ok)

	def finish_calibration(self, wait_ok=None):
		"""
		Stop the calibration sequence and write results into eeprom variables. (Command: `M41`)

		Parameters
		----------
		wait_ok : bool
			(Default value = `None`) Whether to wait_ok for output to return from the Mirobot before returning from the function. This value determines if the function will block until the operation recieves feedback. If `None`, use class default `WlkataMirobotGcodeProtocol.wait_ok` instead.

		Returns
		-------
		msg : List[str] or bool
			 If `wait_ok` is `True`, then return a list of strings which contains message output.
			 If `wait_ok` is `False`, then return whether sending the message succeeded.
		"""
		instruction = 'M41'
		return self.send_msg(instruction, wait_ok=wait_ok)

	def reset_configuration(self, reset_file=None, wait_ok=None):
		"""
		Reset the Mirobot by resetting all eeprom variables to their factory settings. If provided an explicit `reset_file` on invocation, it will execute reset commands given in by `reset_file` instead of `self.reset_file`.

		Parameters
		----------
		reset_file : str or Path or Collection[str] or file-like
			(Default value = `True`) A file-like object, Collection, or string containing reset values for the Mirobot. If given a string with newlines, it will split on those newlines and pass those in as "variable reset commands". Passing in the default value (None) will use the commands in "reset.xml" provided by WLkata to reset the Mirobot. If passed in a string without newlines, `WlkataMirobotGcodeProtocol.reset_configuration` will try to open the file specified by the string and read from it. A `Path` object will be processed similarly. With a Collection (list-like) object, `WlkataMirobotGcodeProtocol.reset_configuration` will use each element as the message body for `WlkataMirobotGcodeProtocol.send_msg`. One can also pass in file-like objects as well (like `open('path')`).
		wait_ok : bool
			(Default value = `None`) Whether to wait_ok for output to return from the Mirobot before returning from the function. This value determines if the function will block until the operation recieves feedback. If `None`, use class default `WlkataMirobotGcodeProtocol.wait_ok` instead.

		Returns
		-------
		msg : List[str] or bool
			 If `wait_ok` is `True`, then return a list of strings which contains message output.
			 If `wait_ok` is `False`, then return whether sending the message succeeded.
		"""

		output = {}

		def send_each_line(file_lines):
			nonlocal output
			for line in file_lines:
				output[line] = self.send_msg(line, var_command=True, wait_ok=wait_ok)

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
