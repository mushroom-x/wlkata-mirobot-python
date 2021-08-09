from dataclasses import dataclass

from .extended_dataclasses import basic_dataclass, featured_dataclass


@dataclass
class MirobotAngles(featured_dataclass):
    """ A dataclass to hold Mirobot's angular values. """
    a: float = None
    """ Angle of axis 1 """
    b: float = None
    """ Angle of axis 2 """
    c: float = None
    """ Angle of axis 3 """
    x: float = None
    """ Angle of axis 4 """
    y: float = None
    """ Angle of axis 5 """
    z: float = None
    """ Angle of axis 6 """
    d: float = None
    """ Location of external slide rail module """

    @property
    def a1(self):
        """ Angle of axis 1 """
        return self.a

    @property
    def a2(self):
        """ Angle of axis 2 """
        return self.b

    @property
    def a3(self):
        """ Angle of axis 3 """
        return self.c

    @property
    def a4(self):
        """ Angle of axis 4 """
        return self.x

    @property
    def a5(self):
        """ Angle of axis 5 """
        return self.y

    @property
    def a6(self):
        """ Angle of axis 6 """
        return self.z

    @property
    def rail(self):
        """ 
        Location of external slide rail module
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
class MirobotCartesians(featured_dataclass):
    """ A dataclass to hold Mirobot's cartesian values and roll/pitch/yaw angles. """
    x: float = None
    """ Position on X-axis """
    y: float = None
    """ Position of Y-axis """
    z: float = None
    """ Position of Z-axis """
    a: float = None
    """ Position of Roll angle """
    b: float = None
    """ Position of Pitch angle """
    c: float = None
    """ Position of Yaw angle """

    @property
    def tx(self):
        """ Position on X-axis """
        return self.x

    @property
    def ty(self):
        """ Position on Y-axis """
        return self.y

    @property
    def tz(self):
        """ Position on Z-axis """
        return self.z

    
    @property
    def rx(self):
        """ Position of Roll angle """
        return self.a

    @property
    def ry(self):
        """ Position of Pitch angle """
        return self.b

    @property
    def rz(self):
        """ Position of Yaw angle """
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
class MirobotStatus(basic_dataclass):
    """ A composite dataclass to hold all of Mirobot's trackable quantities. """
    state: str = ''
    """ The brief descriptor string for Mirobot's state. """
    angle: MirobotAngles = MirobotAngles()
    """ Dataclass that holds Mirobot's angular values including the rail position value. """
    cartesian: MirobotCartesians = MirobotCartesians()
    """ Dataclass that holds the cartesian values and roll/pitch/yaw angles. """
    pump_pwm: int = None
    """ The current pwm of the pnuematic pump module. """
    valve_pwm: int = None
    """ The current pwm of the value module. (eg. gripper) """
    motion_mode: bool = False
    """ Whether Mirobot is currently in coordinate mode (`False`) or joint-motion mode (`True`) """
