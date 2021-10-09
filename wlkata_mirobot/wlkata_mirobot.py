'''
Mirobot GCode通信协议
'''
import math
from collections.abc import Collection
from contextlib import AbstractContextManager
import logging
import os
from pathlib import Path
import re
import time
from typing import TextIO, BinaryIO
import math
from collections import namedtuple
from enum import Enum
from typing import NamedTuple

try:
	import importlib.resources as pkg_resources
except ImportError:
	# Try backported to PY<37 `importlib_resources`.
	import importlib_resources as pkg_resources

# from .wlkata_mirobot_interface_bluetooth import BluetoothLowEnergyInterface
from .wlkata_mirobot_serial import WlkataMirobotSerial
from .wlkata_mirobot_status import MirobotStatus, MirobotAngles, MirobotCartesians
from .wlkata_mirobot_exceptions import ExitOnExceptionStreamHandler, MirobotError, MirobotAlarm, MirobotReset, MirobotAmbiguousPort, MirobotStatusError, MirobotResetFileError, MirobotVariableCommandError

# 判断操作系统的类型
# nt: 微软NT标准
os_is_nt = os.name == 'nt'
# Linux跟Mac都属于 posix 标准
# posix: 类Unix 操作系统的可移植API
os_is_posix = os.name == 'posix'


class WlkataMirobotTool(Enum):
	NO_TOOL = 0         # 没有工具
	SUCTION_CUP = 1     # 气泵吸头
	GRIPPER = 2         # 舵机爪子
	FLEXIBLE_CLAW = 3   # 三指柔爪
	
class WlkataMirobot(AbstractContextManager):
	'''Wlkata Python SDK'''
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
		'''初始化'''
  		# 设置日志等级
		self.logger = logging.getLogger(__name__)
		
		self.logger.setLevel(logging.DEBUG)

		self.stream_handler = ExitOnExceptionStreamHandler()
		self.stream_handler.setLevel(logging.DEBUG if debug else logging.INFO)

		formatter = logging.Formatter(f"[Mirobot Init] [%(levelname)s] %(message)s")
		self.stream_handler.setFormatter(formatter)
		self.logger.addHandler(self.stream_handler)

		self.device = None
		
		# 创建串口连接
		if connection_type.lower() in ('serial', 'ser'):
			# 创建串口连接
			serial_device_init_fn = WlkataMirobotSerial.__init__
			args_names = serial_device_init_fn.__code__.co_varnames[:serial_device_init_fn.__code__.co_argcount]
			args_dict = dict(zip(args_names, device_args))
			args_dict.update(device_kwargs)

			args_dict['mirobot'] = self
			args_dict['exclusive'] = exclusive
			args_dict['debug'] = debug
			args_dict['logger'] = self.logger
			args_dict['autofindport'] = autofindport
			# 设置设备为串口接口
			self.device = WlkataMirobotSerial(**args_dict)
			# 设置端口名称
			self.default_portname = self.device.default_portname

		formatter = logging.Formatter(f"[{self.default_portname}] [%(levelname)s] %(message)s")
		self.stream_handler.setFormatter(formatter)
		# 读取重置文件
		self.reset_file = pkg_resources.read_text('wlkata_mirobot.resources', 'reset.xml') if reset_file is None else reset_file
		# 设置调试模式
		self._debug = debug
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
		# 末端默认运动速度
		self.default_speed = default_speed
		# 默认是否等待回传数据'ok'
		self.wait_ok = wait_ok
		# Mirobot状态信息
		self.status = MirobotStatus()
		# 设置末端工具
		self.tool = WlkataMirobotTool.NO_TOOL
		# 自动连接
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
		'''获取当前的调试模式(是否开启)'''
		return self._debug

	@debug.setter
	def debug(self, enable):
		'''设置为调试模式'''
		self._debug = bool(enable)
		self.stream_handler.setLevel(logging.DEBUG if self._debug else logging.INFO)
		self.device.setDebug(enable)

	def send_msg(self, msg, var_command=False, disable_debug=False, terminator=os.linesep, wait_ok=None, wait_idle=False):
		'''给Mirobot发送指令'''
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
			
			# print(f"send_msg wait_ok = {wait_ok}")
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
		'''获取Mirobot的状态信息, 回传的是状态字符'''
		instruction = '?'
		ret = self.send_msg(instruction, disable_debug=disable_debug, wait_ok=False, wait_idle=False)
		recv_str = self.device.serial_device.readline(timeout=0.10) # .decode('utf-8')
		self.logger.debug(f"[RECV] {recv_str}")
		return recv_str

	def get_status(self, disable_debug=False):
		'''获取并更新Mirobot的状态'''
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
		'''设置新的状态'''
		self.status = status

	def _parse_status(self, msg):
		'''
		从字符串中解析Mirbot返回的状态信息, 提取有关变量赋值给机械臂对象
		'''
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
		'''解锁各轴锁定状态'''
		msg = 'M50'
		return self.send_msg(msg, wait_ok=True, wait_idle=True)
		
	def go_to_zero(self):
		'''回零-运动到名义上的各轴零点'''
		msg = '$M'
		return self.send_msg(msg, wait_ok=True, wait_idle=True)
	
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
	
	def set_hard_limit(self, enable):
		'''
		开启硬件限位
		'''
		msg = f'$21={int(enable)}'
		return self.send_msg(msg, var_command=True, wait_ok=None)

	def set_soft_limit(self, enable):
		'''开启软限位
		注: 请谨慎使用
  		'''
		msg = f'$20={int(enable)}'
		return self.send_msg(msg, var_command=True, wait_ok=None)
	
	def format_float_value(self, value):
		if value is None:
			return value
		if isinstance(value, float):
			# 精确到小数点后两位数
			return round(value , 2)
		else:
			return value
	
	def generate_args_string(self, instruction, pairings):
		'''生成参数字符'''
		args = [f'{arg_key}{self.format_float_value(value)}' for arg_key, value in pairings.items() if value is not None]

		return ' '.join([instruction] + args)
	
	def set_joint_angle(self, joint_angles, speed=None, is_relative=False, wait_ok=None):
		'''
		设置机械臂关节的角度
		joint_angles 目标关节角度字典, key是关节的ID号, value是角度(单位°)
			举例: {1:45.0, 2:-30.0}
		'''
		for joint_i in range(1, 8):
			# 补齐缺失的角度
			if joint_i not in joint_angles:
				joint_angles[joint_i] = None

		return self.go_to_axis(x=joint_angles[1], y=joint_angles[2], z=joint_angles[3], a=joint_angles[4], \
			b=joint_angles[5], c=joint_angles[6], d=joint_angles[7], is_relative=is_relative, speed=speed, wait_ok=wait_ok)

	def go_to_axis(self, x=None, y=None, z=None, a=None, b=None, c=None, d=None, speed=None, is_relative=False, wait_ok=True):
		'''设置关节角度/位置'''
		instruction = 'M21 G90'  # X{x} Y{y} Z{z} A{a} B{b} C{c} F{speed}
		if is_relative:
			instruction = 'M21 G91'
		if not speed:
			speed = self.default_speed
		if speed:
			speed = int(speed)

		pairings = {'X': x, 'Y': y, 'Z': z, 'A': a, 'B': b, 'C': c, 'D': d, 'F': speed}
		msg = self.generate_args_string(instruction, pairings)

		return self.send_msg(msg, wait_ok=wait_ok, wait_idle=True)

	def set_slider_posi(self, d, speed=None, is_relative=False, wait_ok=True):
		'''设置滑台位置, 单位mm'''
		if not is_relative:
			return 	self.go_to_axis(d=d,
									speed=speed, wait_ok=wait_ok)
		else:
			return 	self.go_to_axis(d=d,
									speed=speed, wait_ok=wait_ok, is_relative=True)
   
	def set_tool_pose(self, x=None, y=None, z=None, roll=0.0, pitch=0.0, yaw=0.0, mode='p2p', speed=None, is_relative=False, wait_ok=True):
		'''设置工具位姿'''
		if mode == "p2p":
			# 点控模式 Point To Point
			self.p2p_interpolation(x=x, y=y, z=z, a=yaw, b=pitch, c=yaw, speed=speed, is_relative=is_relative, wait_ok=wait_ok)
		elif mode == "linear":
			# 直线插补 Linera Interpolation
			self.linear_interpolation(x=x, y=y, z=z, a=yaw, b=pitch, c=yaw, speed=speed,is_relative=is_relative, wait_ok=wait_ok)
		else:
			# 默认是点到点
			self.p2p_interpolation(x=x, y=y, z=z, a=yaw, b=pitch, c=yaw, speed=speed, wait_ok=wait_ok)
   
	def p2p_interpolation(self, x=None, y=None, z=None, a=None, b=None, c=None, speed=None, is_relative=False, wait_ok=None):
		'''点到点插补'''
		instruction = 'M20 G90 G0'  # X{x} Y{y} Z{z} A{a} B{b} C{c} F{speed}
		if is_relative:
			instruction = 'M20 G91 G0'

		if not speed:
			speed = self.default_speed
		if speed:
			speed = int(speed)

		pairings = {'X': x, 'Y': y, 'Z': z, 'A': a, 'B': b, 'C': c, 'F': speed}
		msg = self.generate_args_string(instruction, pairings)

		return self.send_msg(msg, wait_ok=wait_ok, wait_idle=True)

	def linear_interpolation(self, x=None, y=None, z=None, a=None, b=None, c=None, speed=None, is_relative=False, wait_ok=None):
		'''直线插补'''
		instruction = 'M20 G90 G1'  # X{x} Y{y} Z{z} A{a} B{b} C{c} F{speed}
		if is_relative:
			instruction = 'M20 G91 G1'
		if not speed:
			speed = self.default_speed
		if speed:
			speed = int(speed)

		pairings = {'X': x, 'Y': y, 'Z': z, 'A': a, 'B': b, 'C': c, 'F': speed}
		msg = self.generate_args_string(instruction, pairings)
		return self.send_msg(msg, wait_ok=wait_ok, wait_idle=True)
	
	def circular_interpolation(self, ex, ey, radius, is_cw=True, speed=None, wait_ok=None):
		'''圆弧插补
  		在XY平面上, 从当前点运动到相对坐标(ex, ey).半径为radius
		`is_cw`决定圆弧是顺时针还是逆时针.
		'''
		# 判断是否合法
		distance = math.sqrt(ex**2 + ey**2)
		if distance > (radius * 2):
			self.logger.error(f'circular interpolation error, target posi is too far')
			return False

		instruction = None
		if is_cw:
			instruction = 'M20 G91 G02'
		else:
			instruction = 'M20 G91 G03'
		
		pairings = {'X': ex, 'Y': ey, 'R': radius, 'F': speed}
		msg = self.generate_args_string(instruction, pairings)
		return self.send_msg(msg, wait_ok=wait_ok, wait_idle=True)
	
	def set_door_lift_distance(self, lift_distance):
		'''设置门式轨迹规划抬起的高度'''
		msg = f"$49={lift_distance}"
		return self.send_msg(msg, wait_ok=True, wait_idle=True)

	def door_interpolation(self, x=None, y=None, z=None, a=None, b=None, c=None, speed=None, is_relative=False, wait_ok=None):
		'''门式插补'''
		instruction = 'M20 G90 G05'  # X{x} Y{y} Z{z} A{a} B{b} C{c} F{speed}
		if is_relative:
			instruction = 'M20 G91 G05'
		
		if not speed:
			speed = self.default_speed
		if speed:
			speed = int(speed)

		pairings = {'X': x, 'Y': y, 'Z': z, 'A': a, 'B': b, 'C': c, 'F': speed}
		msg = self.generate_args_string(instruction, pairings)
		return self.send_msg(msg, wait_ok=wait_ok, wait_idle=True)

	def set_tool_type(self, tool, wait_ok=True):
		'''选择工具类型'''
		self.tool = tool
		self.logger.info(f"set tool {tool.name}")
		# 获取工具的ID
		tool_id = tool.value

		if type(tool_id) != int or not (tool_id >= 0 and tool_id <= 3):
			self.logger.error(f"Unkown tool id {tool_id}")
			return False
		msg = f'$50={tool_id}'
		return self.send_msg(msg, wait_ok=wait_ok, wait_idle=True)
	
	def set_tool_offset(self, offset_x, offset_y, offset_z, wait_ok=True):
		'''设置工具坐标系的偏移量'''
		# 设置末端x轴偏移量
		msg = f"$46={offset_x}"
		ret_x = self.send_msg(msg, wait_ok=wait_ok, wait_idle=True)
		# 设置末端y轴偏移量
		msg = f"$47={offset_y}"
		ret_y = self.send_msg(msg, wait_ok=wait_ok, wait_idle=True)
		# 设置末端z轴偏移量
		msg = f"$48={offset_z}"
		ret_z = self.send_msg(msg, wait_ok=wait_ok, wait_idle=True)
		return ret_x and ret_y and ret_z

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
		
	def set_air_pump(self, pwm, wait_ok=None):
		'''设置气泵的PWM信号'''
		if pwm not in self.pump_pwm_values:
			self.logger.exception(ValueError(f'pwm must be one of these values: {self.pump_pwm_values}. Was given {pwm}.'))
			pwm = self.AIR_PUMP_OFF_PWM_VALUE
		msg = f'M3S{pwm}'
		return self.send_msg(msg, wait_ok=wait_ok, wait_idle=True)

	def set_valve(self, pwm, wait_ok=None):
		'''设置电磁阀的PWM'''
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
		'''开始进行机械臂标定'''
		instruction = 'M40'
		return self.send_msg(instruction, wait_ok=wait_ok)

	def finish_calibration(self, wait_ok=None):
		'''完成机械臂标定'''
		instruction = 'M41'
		return self.send_msg(instruction, wait_ok=wait_ok)

	def reset_configuration(self, reset_file=None, wait_ok=None):
		'''重置机械臂的配置'''
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
