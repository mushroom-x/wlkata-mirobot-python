"""
Mirobot异常处理
"""
import logging

class ExitOnExceptionStreamHandler(logging.StreamHandler):
    """ 数据流存在问题, 信息不能正常的发送 """
    def emit(self, record):
        super().emit(record)
        # 当日志等级大于等于logging.ERROR 系统自动退出
        if record.levelno >= logging.ERROR:
            raise SystemExit(-1)

class MirobotError(Exception):
    """ 
    An inplace class for throwing Mirobot errors. 
    Mirobot错误
    """
    pass

class MirobotAlarm(Exception):
    """ 
    An inplace class for throwing Mirobot alarms. 
    Mirobot警报
    """
    pass

class MirobotReset(Exception):
    """ 
    An inplace class for when Mirobot resets.
    Mirobot重置
    """
    pass

class MirobotStatusError(Exception):
    """ 
    An inplace class for when Mirobot's status message is unprocessable. 
    Mirobot的状态信息无法被解析
    """
    pass

class MirobotResetFileError(Exception):
    """ 
    An inplace class for when Mirobot has problems using the given reset file. 
    Mirobot使用当前的重置配置文件发生错误
    """
    pass

class MirobotVariableCommandError(Exception):
    """ 
    An inplace class for when Mirobot finds a command that does not match variable setting-command syntax.
    Mirobot指令语法错误
    """
    pass


######################################################################
## 串口异常
######################################################################

class MirobotAmbiguousPort(Exception):
    """ 
    An inplace class for when the serial port is unconfigurable.
    Mirobot串口无法配置错误
    """
    pass

class SerialDeviceReadError(Exception):
    """ 
    An inplace class for when WlkataMirobotDeviceSerial is unable to read the serial port
    串口设备读取异常
    """
    pass

class SerialDeviceOpenError(Exception):
    """ 
    An inplace class for when WlkataMirobotDeviceSerial is unable to open the serial port 
    串口设备打开异常
    """
    pass

class SerialDeviceCloseError(Exception):
    """ 
    An inplace class for when WlkataMirobotDeviceSerial is unable to close the serial port 
    串口设备关闭错误
    """
    pass

class SerialDeviceWriteError(Exception):
    """ 
    An inplace class for when WlkataMirobotDeviceSerial is unable to write to the serial port 
    串口写入错误
    """
    pass

######################################################################
## 蓝牙异常
######################################################################
class InvalidBluetoothAddressError(Exception):
    """ 
    An inplace class for when an invalid Bluetooth address is given 
    蓝牙地址错误
    """
    pass