from lib.FT_functions import * # import built-in Funky Trees functions and variables
main_loop_name = "_process" #the name of the main function

# ========== demo script, some functions make no sense ==========

# declare your Global variables
min_altitude = 2.0
engine_on = True if Throttle > 0.1 else False

# main loop function, delta is the time difference between current and last frame, you can use it for time-based calculations
# all variables declared inside this function as well as all global variables will be converted to in-game variables
# you can also skip this function, then only global variables will be converted
def _process(delta) -> None:
    global min_altitude
    global engine_on
    pitch_control = 0.0
    roll_control = 0.0
    yaw_control = 0.0
    gear_control = 0.0
    autotrim = 0.0
    AOA = 0.0
    timer = 0.0

    # control logics, only simple if-else statements and variable assignments are allowed, do not use loops!
    if IAS > 10:
        if abs(PitchRate) > 5:
            pitch_control = clamp(Pitch + get_pitch_damper(Pitch) + autotrim, -1, 1)
            roll_control = Roll*clamp01((IAS-10)/40)
    else:
        roll_control = Roll
        pitch_control = Pitch
    autotrim = get_autotrim(pitch_control)
    yaw_control = Yaw - YawRate*0.1
    AOA = get_AOA()
    gear_control = smooth(GearDown, 0.1)

    if TargetSelected:
        timer += delta
    else:
        timer = 0.0
    
    print("end of main loop")

# below are helper functions, 
# it's not recommended to call other helper functions inside helper functions
# and do not use recursion!
def get_autotrim(pitchinput) -> float:
    if SelectedWeaponName == "test" or not engine_on:
        temp = 1
    else:
        temp = pitchinput
    start = 0.5
    result = start * PID(0,Pitch+temp,5,6,7)
    return result + get_trim_feedback(Pitch)*0.5

def get_trim_feedback(pitchinput) -> float:
    temp = PID(0,PitchRate,1,2,3)
    start = pitchinput
    end = start+temp
    result = end * PID(0,Pitch+temp,2,3,4) + start
    return result

def get_pitch_damper(pitch_input) -> float:
    global min_altitude
    if AltitudeAgl < min_altitude:
        return 0.0
    if abs(pitch_input) < 0.05:
        return 0.0
    return PitchRate * 0.1

def get_AOA() -> float:
    return lerp(
        -PitchAngle
        ,
        pingpong(abs(AngleOfAttack),90)*sign(AngleOfAttack)
        ,
        clamp01((IAS-5)/10)
    )

# this function does nothing and will be ignored
def toggle_gear(temp)-> bool:
    global engine_on
    pass


# you can call the main function for debugging
globals()[main_loop_name](0.01)