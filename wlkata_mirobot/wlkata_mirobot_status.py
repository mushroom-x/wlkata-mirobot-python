"""
Mirobot的状态信息, 包括:
- `MirobotAngles`: 机械臂关节角度
- `MirobotCartesians`: 机械臂末端在笛卡尔坐标系下的位姿
- `MirobotStatus`: 机械臂系统状态
"""
from dataclasses import dataclass, asdict, astuple, fields
import numbers
import operator


class BasicDataClass:
    def asdict(self):
        return asdict(self)

    def astuple(self):
        return astuple(self)

    def fields(self):
        return fields(self)

    @classmethod
    def _new_from_dict(cls, dictionary):
        return cls(**dictionary)

class FeaturedDataClass(BasicDataClass):
    def _cross_same_type(self, other, operation_function, single=False):
        new_values = {}
        for f in self.fields():
            this_value = getattr(self, f.name)

            if single:
                other_value = other
            else:
                other_value = getattr(other, f.name)

            result = operation_function(this_value, other_value)

            new_values[f.name] = result

        return new_values

    def _binary_operation(self, other, operation):
        def operation_function(this_value, other_value):
            if None in (this_value, other_value):
                return None
            else:
                return operation(this_value, other_value)

        if isinstance(other, type(self)):
            new_values = self._cross_same_type(other, operation_function)

        elif isinstance(other, numbers.Real):
            new_values = self._cross_same_type(other, operation_function, single=True)

        else:
            raise NotImplementedError(f"Cannot handle {type(self)} and {type(other)}")

        return self._new_from_dict(new_values)

    def _unary_operation(self, operation_function):
        new_values = {f.name: operation_function(f)
                      for f in self.fields()}

        return self._new_from_dict(new_values)

    def _basic_unary_operation(self, operation):
        def operation_function(field):
            value = getattr(self, field.name)
            if value is not None:
                return operation(value)
            else:
                return None

        return self._unary_operation(operation_function)

    def _comparision_operation(self, other, operation):
        def operation_function(this_value, other_value):
            if None in (this_value, other_value):
                return True
            else:
                return operation(this_value, other_value)

        if isinstance(other, type(self)):
            new_values = self._cross_same_type(other, operation_function).values()

        elif isinstance(other, (int, float)):
            new_values = self._cross_same_type(other, operation_function, single=True).values()

        else:
            raise NotImplementedError(f"Cannot handle {type(self)} and {type(other)}")

        if all(new_values):
            return True

        elif not any(new_values):
            return False

        else:
            return None

    def __or__(self, other):
        def operation_function(this_value, other_value):
            if this_value is None:
                return other_value
            else:
                return this_value

        new_values = self._cross_same_type(other, operation_function)
        return self._new_from_dict(new_values)

    def __and__(self, other):
        def operation_function(this_value, other_value):
            if None not in (this_value, other_value):
                return this_value
            else:
                return None

        new_values = self._cross_same_type(other, operation_function)
        return self._new_from_dict(new_values)

    def int(self):
        def operation_function(field):
            value = getattr(self, field.name)
            if field.type in (float,) and value is not None:
                return int(value)
            else:
                return value

        return self._unary_operation(operation_function)

    def round(self):
        def operation_function(field):
            value = getattr(self, field.name)
            if field.type in (float,) and value is not None:
                return round(value)
            else:
                return value

        return self._unary_operation(operation_function)

    def __add__(self, other):
        return self._binary_operation(other, operator.add)

    def __radd__(self, other):
        return self._binary_operation(other, operator.add)

    def __sub__(self, other):
        return self._binary_operation(other, operator.sub)

    def __rsub__(self, other):
        def rsub(dataclass_value, number):
            return operator.sub(number, dataclass_value)

        return self._binary_operation(other, rsub)

    def __mul__(self, other):
        return self._binary_operation(other, operator.mul)

    def __rmul__(self, other):
        return self._binary_operation(other, operator.mul)

    def __div__(self, other):
        return self._binary_operation(other, operator.div)

    def __rdiv__(self, other):
        def rdiv(dataclass_value, number):
            return operator.div(number, dataclass_value)

        return self._binary_operation(other, rdiv)

    def __truediv__(self, other):
        return self._binary_operation(other, operator.truediv)

    def __rtruediv__(self, other):
        def rtruediv(dataclass_value, number):
            return operator.truediv(number, dataclass_value)

        return self._binary_operation(other, operator.truediv)

    def __mod__(self, other):
        return self._binary_operation(other, operator.mod)

    def __abs__(self):
        return self._basic_unary_operation(operator.abs)

    def __pos__(self):
        return self._basic_unary_operation(operator.pos)

    def __neg__(self):
        return self._basic_unary_operation(operator.neg)

    def __lt__(self, other):
        return self._comparision_operation(other, operator.lt)

    def __le__(self, other):
        return self._comparision_operation(other, operator.le)

    def __eq__(self, other):
        return self._comparision_operation(other, operator.eq)

    def __ne__(self, other):
        return self._comparision_operation(other, operator.ne)

    def __ge__(self, other):
        return self._comparision_operation(other, operator.ge)

    def __gt__(self, other):
        return self._comparision_operation(other, operator.gt)

@dataclass
class MirobotAngles(FeaturedDataClass):
    """
    Mirobot关节角度
    """
    a: float = None # 关节1的角度
    b: float = None # 关节2的角度
    c: float = None # 关节3的角度
    x: float = None # 关节4的角度
    y: float = None # 关节5的角度
    z: float = None # 关节6的角度
    d: float = None # 第七轴滑台的位置
    @property
    def a1(self):
        """ 关节1的角度, 单位° """
        return self.a

    @property
    def a2(self):
        """关节2的角度, 单位° """
        return self.b

    @property
    def a3(self):
        """ 关节3的角度, 单位° """
        return self.c

    @property
    def a4(self):
        """ 关节4的角度, 单位° """
        return self.x

    @property
    def a5(self):
        """ 关节5的角度, 单位° """
        return self.y

    @property
    def a6(self):
        """ 关节6的角度, 单位° """
        return self.z

    @property
    def rail(self):
        """ 
        第七轴也就是直线滑轨的平移
        """
        return self.d

    @property
    def joint1(self):
        """
        关节1的角度, 单位°
        """ 
        return self.x

    @property
    def joint2(self):
        """
        关节2的角度, 单位°
        """ 
        return self.y

    @property
    def joint3(self):
        """
        关节2的角度, 单位°
        """ 
        return self.z

    @property
    def joint4(self):
        """
        关节4的角度, 单位°
        """ 
        return self.a
    
    @property
    def joint5(self):
        """
        关节5的角度, 单位°
        """ 
        return self.b
    
    @property
    def joint6(self):
        """
        关节4的角度, 单位°
        """ 
        return self.c

@dataclass
class MirobotCartesians(FeaturedDataClass):
    """ 
    笛卡尔坐标系下的位姿Pose, 包括
    - 末端位置: (ex, ey, ez)
    - 末端欧拉角: (raw, pitch, yaw)
    """
    x: float = None # 末端X坐标, 单位mm
    y: float = None # 末端Y坐标, 单位mm
    z: float = None # 末端Z坐标, 单位mm
    a: float = None # 横滚角 Roll, 单位°
    b: float = None # 俯仰角 Pitch, 单位°
    c: float = None # 偏航角 Yaw, 单位°

    @property
    def tx(self):
        """ 末端X坐标, 单位mm """
        return self.x

    @property
    def ty(self):
        """ 末端Y坐标, 单位mm """
        return self.y

    @property
    def tz(self):
        """ 末端Z坐标, 单位mm """
        return self.z

    
    @property
    def rx(self):
        """ 横滚角,单位° """
        return self.a

    @property
    def ry(self):
        """
        俯仰角,单位°
        """
        return self.b

    @property
    def rz(self):
        """ 偏航角,单位° """
        return self.c

    @property
    def roll(self):
        """ 横滚角,单位° """
        return self.a
    
    @property
    def pitch(self):
        """ 俯仰角,单位° """
        return self.b
    
    @property
    def yaw(self):
        """ 偏航角,单位° """
        return self.c
    
    def __str__(self):
        return f"Pose(x={self.x},y={self.y},z={self.z},roll={self.roll},pitch={self.pitch},yaw={self.yaw})"
        
@dataclass
class MirobotStatus(BasicDataClass):
    """ 
    A composite dataclass to hold all of Mirobot's trackable quantities.
    Mirobot状态信息，用合成的数据结构来存储
    """
    # Mirobot状态符，字符串
    state: str = ''
    # 记录关节角度信息
    angle: MirobotAngles = MirobotAngles()
    # 存放笛卡尔坐标系下的位姿 xyz坐标与rpy角度
    cartesian: MirobotCartesians = MirobotCartesians()
    # 气泵的PWM
    pump_pwm: int = None
    # 电磁阀/爪子的PWM
    valve_pwm: int = None
    # 当前的运动模式
    # False:    笛卡尔坐标系模式
    # True:     关节运动模式    
    motion_mode: bool = False