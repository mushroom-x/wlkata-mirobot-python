import logging
import os
import time
import serial

from .exceptions import ExitOnExceptionStreamHandler, SerialDeviceOpenError, SerialDeviceReadError, SerialDeviceCloseError, SerialDeviceWriteError


class SerialDevice:
    """ A class for establishing a connection to a serial device. """
    def __init__(self, portname='', baudrate=0, stopbits=1, exclusive=True, debug=False):
        """ Initialization of `SerialDevice` class
        串口设备初始化

        Parameters
        ----------
        portname : str
             (Default value = `''`) Name of the port to connect to. (Example: 'COM3' or '/dev/ttyUSB1')
        baudrate : int
             (Default value = `0`) Baud rate of the connection.
        stopbits : int
             (Default value = `1`) Stopbits of the connection.
        exclusive : bool
             (Default value = `True`) Whether to (try) forcing exclusivity of serial port for this instance. Is only a true toggle on Linux and OSx; Windows always exclusively blocks serial ports. Setting this variable to `False` on Windows will throw an error.
        debug : bool
             (Default value = `False`) Whether to print DEBUG-level information from the runtime of this class. Show more detailed information on screen output.

        Returns
        -------
        class : SerialDevice

        """
        self.portname = str(portname)
        self.baudrate = int(baudrate)
        self.stopbits = int(stopbits)
        self.exclusive = exclusive
        self._debug = debug

        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)

        self.stream_handler = ExitOnExceptionStreamHandler()
        self.stream_handler.setLevel(logging.DEBUG if self._debug else logging.INFO)

        formatter = logging.Formatter(f"[{self.portname}] [%(levelname)s] %(message)s")
        self.stream_handler.setFormatter(formatter)
        self.logger.addHandler(self.stream_handler)

        self.serialport = serial.Serial(exclusive=exclusive)
        self._is_open = False

    def __del__(self):
        """ Close the serial port when the class is deleted """
        self.close()

    @property
    def debug(self):
        """ Return the `debug` property of `SerialDevice` """
        return self._debug

    @debug.setter
    def debug(self, value):
        """
        Set the new `debug` property of `SerialDevice`. Use as in `SerialDevice.setDebug(value)`.

        Parameters
        ----------
        value : bool
            The new value for `SerialDevice.debug`. User this setter method as it will also update the logging method. As opposed to setting `SerialDevice.debug` directly which will not update the logger.

        """
        self._debug = bool(value)
        self.stream_handler.setLevel(logging.DEBUG if self._debug else logging.INFO)

    @property
    def is_open(self):
        """ Check if the serial port is open """
        self._is_open = self.serialport.is_open
        return self._is_open

    def listen_to_device(self, timeout=0.1):
        """
        Listen to the serial port and return a message.
        
        Returns
        -------
        msg : str
            A single line that is read from the serial port.

        """
        t_start = time.time()
        while self._is_open:
            # 超时判断
            t_cur = time.time()
            if (t_cur - t_start) >= timeout:
                return b''
            
            try:
                msg = self.serialport.readline()
                if msg != b'':
                    msg = msg.decode().strip()
                    return msg

            except Exception as e:
                self.logger.exception(SerialDeviceReadError(e))

    def open(self):
        """ Open the serial port. """
        if not self._is_open:
            # serialport = 'portname', baudrate, bytesize = 8, parity = 'N', stopbits = 1, timeout = None, xonxoff = 0, rtscts = 0)
            self.serialport.port = self.portname
            self.serialport.baudrate = self.baudrate
            self.serialport.stopbits = self.stopbits

            try:
                self.logger.debug(f"Welcome to use mirobot_py (version： kyle2020-0821)")
                self.logger.debug(f"Attempting to open serial port {self.portname}")
                self.serialport.open()
                self._is_open = True

                self.logger.debug(f"Succeeded in opening serial port {self.portname}")

            except Exception as e:
                self.logger.exception(SerialDeviceOpenError(e))

    def close(self):
        """ Close the serial port. """
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


        Parameters
        ----------
        message : str
            The string to send to serial port.

        terminator : str
            (Default value = `os.linesep`) The line separator to use when signaling a new line. Usually `'\\r\\n'` for windows and `'\\n'` for modern operating systems.

        Returns
        -------
        result : bool
            Whether the sending of `message` succeeded.

        """
        if self._is_open:
            try:
                # 自动添加换行符
                if not message.endswith(terminator):
                    message += terminator
                self.serialport.write(message.encode('utf-8'))

            except Exception as e:
                self.logger.exception(SerialDeviceWriteError(e))

            else:
                return True
        else:
            return False
