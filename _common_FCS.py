# this is a common functions file, you can define functions here that can be used in multiple scripts
from lib.FT_functions import *

def clamp11(value) -> float:
    return clamp(value, -1, 1)

def get_AOA() -> float:
    return lerp(
        -PitchAngle
        ,
        pingpong(abs(AngleOfAttack),90)*sign(AngleOfAttack)
        ,
        clamp01((IAS-5)/10)
    )

def get_mach_number() -> float:
    return TAS/(340.3-0.0041*Altitude if Altitude < 11000 else 295.2)