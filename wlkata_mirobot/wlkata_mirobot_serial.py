"""
Mirobot串口通信协议/接口
"""
import os
import time
import serial
import logging

# 使用pyserial的串口设备列表查看器
import serial.tools.list_ports as lp
# 异常
from .wlkata_mirobot_exceptions import MirobotError, MirobotAlarm, MirobotReset, MirobotAmbiguousPort
from .wlkata_mirobot_exceptions import ExitOnExceptionStreamHandler, SerialDeviceOpenError, SerialDeviceReadError, SerialDeviceCloseError, SerialDeviceWriteError

# 当前操作系统的类型
# posix： Linux
# nt: Windows
# java: Java虚拟机
os_is_nt = os.name == 'nt'
# Linux跟Mac都属于 posix 标准
# posix: 类Unix 操作系统的可移植API
os_is_posix = os.name == 'posix'


class DeviceSerial:
	'''串口设备，在Serial的基础上再做一层封装'''
	def __init__(self, portname='', baudrate=115200, stopbits=1, timeout=0.2, exclusive=False, debug=False):
		""" Initialization of `DeviceSerial` class
		串口设备初始化

		Parameters
		----------
		portname : str
			 (Default value = `''`) Name of the port to connect to. (Example: 'COM3' or '/dev/ttyUSB1')
			 端口名称
		baudrate : int
			 (Default value = `0`) Baud rate of the connection.
			 波特率
		stopbits : int
			 (Default value = `1`) Stopbits of the connection.
			 停止位
		exclusive : bool
			 (Default value = `True`) Whether to (try) forcing exclusivity of serial port for this instance. Is only a true toggle on Linux and OSx; Windows always exclusively blocks serial ports. Setting this variable to `False` on Windows will throw an error.
		debug : bool
			 (Default value = `False`) Whether to print DEBUG-level information from the runtime of this class. Show more detailed information on screen output.
			调试开关
		Returns
		-------
		class : DeviceSerial 串口设备

		"""
		self.portname = str(portname)
		self.baudrate = int(baudrate)
		self.stopbits = int(stopbits)
		self.timeout = int(timeout)
		self.exclusive = exclusive
		self._debug = debug

		# 日志模块初始化
		self.logger = logging.getLogger(__name__)
		self.logger.setLevel(logging.DEBUG)
		self.stream_handler = ExitOnExceptionStreamHandler()
		# 设置日志等级
		self.stream_handler.setLevel(logging.DEBUG if self._debug else logging.INFO)
		# 日志格式
		formatter = logging.Formatter(f"[{self.portname}] [%(levelname)s] %(message)s")
		self.stream_handler.setFormatter(formatter)
		self.logger.addHandler(self.stream_handler)

		if os_is_posix:
			# 设置独占访问模式（仅POSIX）。 如果端口已经以独占访问模式打开，则不能以独占访问模式打开端口。
			# self.serialport = serial.Serial(exclusive=exclusive)
			self.serialport = serial.Serial()
		else:
			self.serialport = serial.Serial()
		self._is_open = False

	def __del__(self):
		""" Close the serial port when the class is deleted 
		类被删除的时候，关闭串口
		"""
		self.close()

	@property
	def debug(self):
		""" Return the `debug` property of `DeviceSerial` """
		return self._debug

	@debug.setter
	def debug(self, value):
		"""
		Set the new `debug` property of `DeviceSerial`. Use as in `DeviceSerial.setDebug(value)`.
		配置调试开关
		
		Parameters
		----------
		value : bool
			The new value for `DeviceSerial.debug`. User this setter method as it will also update the logging method. As opposed to setting `DeviceSerial.debug` directly which will not update the logger.
		"""
		self._debug = bool(value)
		self.stream_handler.setLevel(logging.DEBUG if self._debug else logging.INFO)

	@property
	def is_open(self):
		""" 
		Check if the serial port is open
		检查串口是否开启
		"""
		self._is_open = self.serialport.is_open
		return self._is_open

	def readline(self, timeout=0.1):
		"""
		Listen to the serial port and return a message.
		监听串口，读取一行信息
		
		Parameters
		----------
		timeout : float
			等待超时的判断阈值，单位:s
		Returns
		-------
		msg : str
			A single line that is read from the serial port.
			从串口里面读取的一行数据.
			TODO 这里是存在一些不确定性的，因为可能读取的时候，还没有接收到换行符
		"""
		t_start = time.time()
		msg_recv = b''
		while self._is_open:
			# 超时判断
			t_cur = time.time()
			if (t_cur - t_start) >= timeout:
				return msg_recv.decode("utf-8").strip()
			
			try:
				msg_seg = self.serialport.readline()
				if len(msg_seg) > 0:
					msg_recv += msg_seg
			except Exception as e:
				self.logger.exception(SerialDeviceReadError(e))
				
	def open(self):
		""" Open the serial port. 
		打开串口
		"""
		if not self._is_open:
			# serialport = 'portname', baudrate, bytesize = 8, parity = 'N', stopbits = 1, timeout = None, xonxoff = 0, rtscts = 0)
			# 配置串口的参数：
			# - 端口号 portname
			# - 波特率 baudrate
			# - 停止位 stopbits
			# - 超时等待 timeout
			self.serialport.port = self.portname
			self.serialport.baudrate = self.baudrate
			self.serialport.stopbits = self.stopbits
			self.serialport.timeout = self.timeout
			
			try:
				self.logger.debug(f"Wlkata Mirobot Python SDK")
				self.logger.debug(f"- Attempting to open serial port {self.portname}")
				self.serialport.open()
				self._is_open = True
				self.logger.debug(f"- Succeeded in opening serial port {self.portname}")
				return True
			except Exception as e:
				self.logger.exception(SerialDeviceOpenError(e))
				return False
	def close(self):
		""" 
		Close the serial port.
		关闭串口
		"""
		if self._is_open:
			try:
				self.logger.debug(f"Attempting to close serial port {self.portname}")

				self._is_open = False
				self.serialport.close()

				self.logger.debug(f"Succeeded in closing serial port {self.portname}")

			except Exception as e:
				self.logger.exception(SerialDeviceCloseError(e))

	def send(self, message, terminator=os.linesep):
		"""
		Send a message to the serial port.
		向串口发送数据

		Parameters
		----------
		message : str
			The string to send to serial port.
			要通过串口发送出去的字符串
		terminator : str
			系统的换行符。 linux操作系统的换行符是`'\\r\\n'`， Windows操作系统的换行符是`\\n`
			(Default value = `os.linesep`) The line separator to use when signaling a new line. Usually `'\\r\\n'` for windows and `'\\n'` for modern operating systems.

		Returns
		-------
		result : bool
			Whether the sending of `message` succeeded.
			`result`代表指令是否发送成功

		"""
		if self._is_open:
			try:
				# 自动添加换行符
				if not message.endswith(terminator):
					message += terminator
				# 串口发送数据，编码为utf-8
				self.serialport.write(message.encode('utf-8'))
			except Exception as e:
				# 日志写入串口设备写入异常
				self.logger.exception(SerialDeviceWriteError(e))

			else:
				return True
		else:
			return False


class WlkataMirobotSerial:
	""" A class for bridging the interface between `mirobot.wlkata_mirobot_gcode_protocol.WlkataMirobotGcodeProtocol` and `mirobot.serial_device.DeviceSerial`"""
	def __init__(self, mirobot, portname=None, baudrate=None, stopbits=None, exclusive=True, debug=False, logger=None, autofindport=True):
		'''Mirobot串口通信接口'''
		self.mirobot = mirobot
		if logger is not None:
			self.logger = logger

		self._debug = debug
		serial_device_kwargs = {'debug': debug, 'exclusive': exclusive}

		# check if baudrate was passed in args or kwargs, if not use the default value instead
		if baudrate is None:
			# 设置默认的波特率
			serial_device_kwargs['baudrate'] = 115200
		# check if stopbits was passed in args or kwargs, if not use the default value instead
		if stopbits is None:
			# 设置默认的停止位配置
			serial_device_kwargs['stopbits'] = 1

		# if portname was not passed in and autofindport is set to true, autosearch for a serial port
		# 如果没有指定端口号，自行进行搜索
		if autofindport and portname is None:
			self.default_portname = self._find_portname()
			""" The default portname to use when making connections. To override this on a individual basis, provide portname to each invokation of `WlkataMirobotGcodeProtocol.connect`. """
			self.logger.info(f"Using Serial Port \"{self.default_portname}\"")
		else:
			# 设置端口号
			self.default_portname = portname
		serial_device_kwargs['portname'] = self.default_portname
		# 创建串口设备
		self.serial_device = DeviceSerial(**serial_device_kwargs)
		# 打开串口
		self.serial_device.open()
		# 重置机械臂
		# 强制重启
		self.serial_device.serialport.write("%\n".encode("utf-8"))
	
	@property
	def debug(self):
		""" Return the `debug` property of `WlkataMirobotSerial` """
		return self._debug

	@debug.setter
	def debug(self, value):
		'''设置调试开关'''
		self._debug = bool(value)
		self.serial_device.setDebug(value)

	def send(self, msg, disable_debug=False, terminator=os.linesep, wait_ok=False, wait_idle=False):
		'''给Mirobot发送指令'''
		# 发送消息前需要先清除缓冲区
		cache_msg = self.empty_cache()
		if self._debug and not disable_debug:
			# 将缓冲数据打印出来
			if len(cache_msg) != 0:
				self.logger.debug(f"[RECV CACHE] {cache_msg}")

		output = self.serial_device.send(msg, terminator=terminator)
		
		if self._debug and not disable_debug:
			self.logger.debug(f"[SENT] {msg}")

		if wait_ok is None:
			wait_ok = False
		
		if wait_idle is None:
			wait_idle = False
			
		if wait_ok:
			output = self.wait_for_ok(disable_debug=disable_debug)
		
		if wait_idle:
			self.wait_until_idle()
		
		return output
	
	@property
	def is_connected(self):
		'''串口是否连接上'''
		return self.serial_device.is_open
	
	def _is_mirobot_device(self, portname):
		'''是否为mirobot设备'''
		self.logger.info(f"尝试打开串口 {portname}")
		# 尝试打开设备
		try:
			device=serial.Serial(portname, 115200, timeout=0.1)
		except Exception as e:
			self.logger.error(e)
			return False
		
		if not device.isOpen():
			self.logger.error("Serial is not open")
			return False
		# device.write("?\n".encode("utf-8"))
		# 设备重置, 兼容分控板
		device.write("%\n".encode("utf-8"))
		time.sleep(1)
		# 读入所有字符，查看 'WLKATA'是否在接收的字符串里面
		recv_str = device.readall().decode('utf-8')
		self.logger.info(f"[RECV] {recv_str}")
		is_mirobot = 'WLKATA' in recv_str or 'Qinnew' in recv_str
		# 关闭设备
		device.close()
		return is_mirobot
	
	def _find_portname(self):
		'''自动检索可能是Mirobot的端口号'''
		port_objects = lp.comports()

		if not port_objects:
			self.logger.exception(MirobotAmbiguousPort("No ports found! Make sure your Mirobot is connected and recognized by your operating system."))
		else:
			for p in port_objects:
				# 尝试建立连接,发送指令， 看看能不能得到回传
				if self._is_mirobot_device(p.device):
					return p.device
			self.logger.exception(MirobotAmbiguousPort("No open ports found! Make sure your Mirobot is connected and is not being used by another process."))

	def wait_for_ok(self, reset_expected=False, disable_debug=False):
		'''等待ok到来'''
		output = ['']
		# 代表ok的后缀
		ok_eols = ['ok']
		# Reset重置的字符
		reset_strings = ['Using reset pos!']

		# eol: end of line 一行的末尾
		def matches_eol_strings(terms, s):
			# print("matches_eol_strings: s={}".format(s))
			for eol in terms:
				# 修改了这里的ok的判断条件
				# 因为homing成功之后，返回的不是ok而是homeing moving...ok
				# 针对这种情况做了优化, 防止卡死
				if s.endswith(eol) or eol in s:
					# self.logger.debug(f'String {s} terms:{terms}, match')
					return True
			return False

		if reset_expected:
			eols = ok_eols + reset_strings
		else:
			eols = ok_eols

		if os_is_nt and not reset_expected:
			# Window下的期待的ok返回次数
			# eol_threshold = 2 # 感觉是作者写错了
			eol_threshold = 1
		else:
			# Linux下的期待的ok返回次数
			eol_threshold = 1

		eol_counter = 0
		while eol_counter < eol_threshold:
			# 读取消息
			# 这里其实存在问题就是这里的listen_to_device是死循环
			msg = self.serial_device.readline(timeout=0.1)
			# 调试, 打印接收的消息
			if self._debug and not disable_debug:
				if len(msg) != 0:
					self.logger.debug(f"[RECV] {msg}")
			# 异常情况判断
			if 'error' in msg:
				self.logger.error(MirobotError(msg.replace('error: ', '')))
			# 异常情况判断
			if 'ALARM' in msg:
				self.logger.error(MirobotAlarm(msg.split('ALARM: ', 1)[1]))

			output.append(msg)

			if not reset_expected and matches_eol_strings(reset_strings, msg):
				self.logger.error(MirobotReset('Mirobot was unexpectedly reset!'))

			if matches_eol_strings(eols, output[-1]):
				eol_counter += 1

		return output[1:]  # don't include the dummy empty string at first index

	def wait_until_idle(self, refresh_rate=0.1):
		'''等待直到系统状态为Idle空闲状态'''
		# 更新一下当前Mirobot的状态
		self.mirobot.get_status(disable_debug=True)
		while self.mirobot.status is None or self.mirobot.status.state != 'Idle':
			time.sleep(refresh_rate)
			# 不断的发送状态查询, 更新状态
			self.mirobot.get_status(disable_debug=True)
	def empty_cache(self):
		'''清空接收缓冲区'''
		cache_msg = ""
		while(self.serial_device.serialport.in_waiting):
			cache_msg += self.serial_device.serialport.read().decode('utf-8')
		return cache_msg

	def connect(self, portname=None):
		'''建立串口连接'''
		if portname is None:
			if self.default_portname is not None:
				portname = self.default_portname
			else:
				self.logger.exception(ValueError('Portname must be provided! Example: `portname="COM3"`'))

		self.serial_device.portname = portname
		self.serial_device.open()
		# return self.wait_for_ok(reset_expected=True)
		return True
	
	def disconnect(self):
		'''断开与Mirobot的连接，断开串口'''
		if getattr(self, 'serial_device', None) is not None:
			self.serial_device.close()
