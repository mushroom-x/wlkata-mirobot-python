"""
Mirobot串口设备对象
- 根据Mirobot串口通信的配置在serial的外层封装了一层。目的是可以让蓝牙设备跟串口设备共享同一套API。 
"""
import logging
import os
import time
import serial
# 引入异常
from .wlkata_mirobot_exceptions import ExitOnExceptionStreamHandler, SerialDeviceOpenError, SerialDeviceReadError, SerialDeviceCloseError, SerialDeviceWriteError

# Linux跟Mac都属于 posix 标准
# posix: 类Unix 操作系统的可移植API
os_is_posix = os.name == 'posix'

class WlkataMirobotDeviceSerial:
    """
    A class for establishing a connection to a serial device. 
    Mirobot串口设备
    """
    def __init__(self, portname='', baudrate=0, stopbits=1, timeout=0.2, exclusive=False, debug=False):
        """ Initialization of `WlkataMirobotDeviceSerial` class
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
        class : WlkataMirobotDeviceSerial 串口设备

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
            self.serialport = serial.Serial(exclusive=exclusive)
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
        """ Return the `debug` property of `WlkataMirobotDeviceSerial` """
        return self._debug

    @debug.setter
    def debug(self, value):
        """
        Set the new `debug` property of `WlkataMirobotDeviceSerial`. Use as in `WlkataMirobotDeviceSerial.setDebug(value)`.
        配置调试开关
        
        Parameters
        ----------
        value : bool
            The new value for `WlkataMirobotDeviceSerial.debug`. User this setter method as it will also update the logging method. As opposed to setting `WlkataMirobotDeviceSerial.debug` directly which will not update the logger.
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

            except Exception as e:
                self.logger.exception(SerialDeviceOpenError(e))

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
