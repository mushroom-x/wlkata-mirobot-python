import logging


class ExitOnExceptionStreamHandler(logging.StreamHandler):
    '''数据流存在问题, 信息不能正常的发送'''
    def emit(self, record):
        super().emit(record)
        if record.levelno >= logging.ERROR:
            raise SystemExit(-1)


class MirobotError(Exception):
    """ An inplace class for throwing Mirobot errors. """
    pass


class MirobotAlarm(Exception):
    """  An inplace class for throwing Mirobot alarms. """
    pass


class MirobotReset(Exception):
    """ An inplace class for when Mirobot resets. """
    pass


class MirobotAmbiguousPort(Exception):
    """ An inplace class for when the serial port is unconfigurable. """
    pass


class MirobotStatusError(Exception):
    """ An inplace class for when Mirobot's status message is unprocessable. """
    pass


class MirobotResetFileError(Exception):
    """ An inplace class for when Mirobot has problems using the given reset file. """
    pass


class MirobotVariableCommandError(Exception):
    """ An inplace class for when Mirobot finds a command that does not match variable setting-command syntax. """
    pass


class SerialDeviceReadError(Exception):
    """ An inplace class for when SerialDevice is unable to read the serial port """
    pass


class SerialDeviceOpenError(Exception):
    """ An inplace class for when SerialDevice is unable to open the serial port """
    pass


class SerialDeviceCloseError(Exception):
    """ An inplace class for when SerialDevice is unable to close the serial port """
    pass


class SerialDeviceWriteError(Exception):
    """ An inplace class for when SerialDevice is unable to write to the serial port """
    pass


class InvalidBluetoothAddressError(Exception):
    """ An inplace class for when an invalid Bluetooth address is given """
    pass
