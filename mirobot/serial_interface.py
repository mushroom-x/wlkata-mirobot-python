import os
import time
# 使用pyserial的串口设备列表查看器
import serial.tools.list_ports as lp

from .serial_device import SerialDevice
from .exceptions import MirobotError, MirobotAlarm, MirobotReset, MirobotAmbiguousPort

# 当前操作系统的类型
# posix： Linux
# nt: Windows
# java: Java虚拟机
os_is_nt = os.name == 'nt'
os_is_posix = os.name == 'posix'


class SerialInterface:
    """ A class for bridging the interface between `mirobot.base_mirobot.BaseMirobot` and `mirobot.serial_device.SerialDevice`"""
    def __init__(self, mirobot, portname=None, baudrate=None, stopbits=None, exclusive=True, debug=False, logger=None, autofindport=True):
        """ Initialization of `SerialInterface` class

        Parameters
        ----------
        mirobot : `mirobot.base_mirobot.BaseMirobot`
            Mirobot object that this instance is attached to.
        portname : str
             (Default value = None) The portname to attach to. If `None`, and the `autofindport` parameter is `True`, then this class will automatically try to find an open port. It will attach to the first one that is available.
        baudrate : int
             (Default value = None) Baud rate of the connection.
        stopbits : int
             (Default value = None) Stopbits of the connection.
        exclusive : bool
             (Default value = True) Whether to exclusively block the port for this instance. Is only a true toggle on Linux and OSx; Windows always exclusively blocks serial ports. Setting this variable to `False` on Windows will throw an error.
        debug : bool
             (Default value = False) Whether to show debug statements in logger.
        logger : logger.Logger
             (Default value = None) Logger instance to use for this class. Usually `mirobot.base_mirobot.BaseMirobot.logger`.
        autofindport : bool
             (Default value = True) Whether to automatically search for an available port if `address` parameter is `None`.

        Returns
        -------

        """

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
            """ The default portname to use when making connections. To override this on a individual basis, provide portname to each invokation of `BaseMirobot.connect`. """
            serial_device_kwargs['portname'] = self.default_portname
            self.logger.info(f"Using Serial Port \"{self.default_portname}\"")
        else:
            # 设置端口号
            self.default_portname = portname

        self.serial_device = SerialDevice(**serial_device_kwargs)

    @property
    def debug(self):
        """ Return the `debug` property of `SerialInterface` """
        return self._debug

    @debug.setter
    def debug(self, value):
        """
        Set the new value for the `debug` property of `mirobot.serial_interface.SerialInterface`. Use as in `BaseMirobot.setDebug(value)`.
        Use this setter method as it will also update the logging objects of `mirobot.serial_interface.SerialInterface` and its `mirobot.serial_device.SerialDevice`. As opposed to setting `mirobot.serial_interface.SerialInterface._debug` directly which will not update the loggers.
        
        Parameters
        ----------
        value : bool
            The new value for `mirobot.serial_interface.SerialInterface._debug`.

        """
        self._debug = bool(value)
        self.serial_device.setDebug(value)

    def send(self, msg, disable_debug=False, terminator=os.linesep, wait=True, wait_idle=False):
        """
        Send a message to the Mirobot.

        Parameters
        ----------
        msg : str or bytes
             A message or instruction to send to the Mirobot.
        var_command : bool
            (Default value = `False`) Whether `msg` is a variable command (of form `$num=value`). Will throw an error if does not validate correctly.
        disable_debug : bool
            (Default value = `False`) Whether to override the class debug setting. Used primarily by ` BaseMirobot.device.wait_until_idle`.
        terminator : str
            (Default value = `os.linesep`) The line separator to use when signaling a new line. Usually `'\\r\\n'` for windows and `'\\n'` for modern operating systems.
        wait : bool
            (Default value = `None`) Whether to wait for output to end and to return that output. If `None`, use class default `BaseMirobot.wait` instead.
        wait_idle : bool
            (Default value = `False`) Whether to wait for Mirobot to be idle before returning.

        Returns
        -------
        msg : List[str] or bool
            If `wait` is `True`, then return a list of strings which contains message output.
            If `wait` is `False`, then return whether sending the message succeeded.
        """
        # 发送消息前需要先清除缓冲区
        cache_msg = self.empty_cache()
        if self._debug and not disable_debug:
            # 将缓冲数据打印出来
            self.logger.debug(f"[RECV CACHE] {cache_msg}")
    
        output = self.serial_device.send(msg, terminator=terminator)
        
        if self._debug and not disable_debug:
            self.logger.debug(f"[SENT] {msg}")

        if wait_idle:
            self.wait_until_idle()
        elif wait:
            output = self.wait_for_ok(disable_debug=disable_debug)
        
        return output
    
    @property
    def is_connected(self):
        """
        Check if Mirobot is connected.

        Returns
        -------
        connected : bool
            Whether the Mirobot is connected.
        """
        return self.serial_device.is_open

    def _find_portname(self):
        """
        Find the port that might potentially be connected to the Mirobot.
        自动检索可能是Mirobot的端口号

        Returns
        -------
        device_name : str
            The name of the device that is (most-likely) connected to the Mirobot.
            端口号
        """
        port_objects = lp.comports()

        if not port_objects:
            self.logger.exception(MirobotAmbiguousPort("No ports found! Make sure your Mirobot is connected and recognized by your operating system."))

        else:
            for p in port_objects:
                if os_is_posix:
                    try:
                        open(p.device)
                    except Exception:
                        continue
                    else:
                        return p.device
                else:
                    return p.device

            self.logger.exception(MirobotAmbiguousPort("No open ports found! Make sure your Mirobot is connected and is not being used by another process."))

    def wait_for_ok(self, reset_expected=False, disable_debug=False):
        """
        Continuously loops over and collects message output from the serial device.
        It stops when it encounters an 'ok' or otherwise terminal condition phrase.
        持续等待有'ok'返回

        Parameters
        ----------
        reset_expected : bool
            (Default value = `False`) Whether a reset string is expected in the output (Example: on starting up Mirobot, output ends with a `'Using reset pos!'` rather than the traditional `'Ok'`)
        disable_debug : bool
            (Default value = `False`) Whether to override the class debug setting. Otherwise one will see status message debug output every 0.1 seconds, thereby cluttering standard output. Used primarily by `BaseMirobot.wait_until_idle`.

        Returns
        -------
        output : List[str]
            A list of output strings upto and including the terminal string.
        """
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
            msg = self.serial_device.listen_to_device(timeout=0.1)
            
            # 调试, 打印接收的消息
            if self._debug and not disable_debug:
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
        """
        Continuously loops over and refreshes state of the Mirobot.
        It stops when it encounters an 'Idle' state string.
        等待直到系统状态为Idle空闲状态

        Parameters
        ----------
        refresh_rate : float
            (Default value = `0.1`) The rate in seconds to check for the 'Idle' state. Choosing a low number might overwhelm the controller on Mirobot. Be cautious when lowering this parameter.

        Returns
        -------
        output : List[str]
            A list of output strings upto and including the terminal string.
        """
        # 更新一下当前Mirobot的状态
        self.mirobot.update_status(disable_debug=True)
        # self.mirobot.update_status(disable_debug=False)
        while self.mirobot.status is None or self.mirobot.status.state != 'Idle':
            time.sleep(refresh_rate)
            # 不断的发送状态查询, 更新状态
            self.mirobot.update_status(disable_debug=True)
            # self.mirobot.update_status(disable_debug=False)
            # 打印mirobot当前的状态
            if self.mirobot.status is not None:
                self.logger.debug(f"current mirobot state: {self.mirobot.status.state}")
            
    def empty_cache(self):
        '''清空接收缓冲区'''
        cache_msg = ""
        while(self.serial_device.serialport.in_waiting):
            cache_msg += self.serial_device.serialport.read().decode('utf-8')
        return cache_msg

    def connect(self, portname=None):
        """
        Connect to the Mirobot.
        建立串口连接

        Parameters
        ----------
        portname : str
            (Default value = `None`) The name of the port to connnect to. If this is `None`, then it will try to use `self.default_portname`. If both are `None`, then an error will be thrown. To avoid this, specify a portname.

        Returns
        -------
        ok_msg : List[str]
            The output from an initial Mirobot connection.
        """
        if portname is None:
            if self.default_portname is not None:
                portname = self.default_portname
            else:
                self.logger.exception(ValueError('Portname must be provided! Example: `portname="COM3"`'))

        self.serial_device.portname = portname

        self.serial_device.open()

        return self.wait_for_ok(reset_expected=True)

    def disconnect(self):
        """ 
        Disconnect from the Mirobot. Close the serial device connection.
        断开与Mirobot的连接，断开串口 
        """
        if getattr(self, 'serial_device', None) is not None:
            self.serial_device.close()
