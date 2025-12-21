# this is a demo script, the file name must be the same as your aircraft XML file name. And don't start the file name with an underscore.

from lib.FT_functions import * # import built-in Funky Trees functions and variables

from _common_FCS import * # your can import your common functions so you don't neeed to rewrite them in every script

main_loop_name = "_process" #the name of the main function
exclude = ["attack_mode"]  #list of variable names to be excluded from conversion, you may need to add some aircraft-part-exported variables here

# ========== program start ==========

# declare your global variables
min_altitude = 3.0
engine_on = False
attack_mode  = False
timer = 0.0
AOA = 0.0

# main loop function, delta is the time difference between current and last frame, you can use it for time-based calculations
# all variables declared inside this function as well as all global variables will be converted to in-game variables
# you can also do not write this function, then only global variables will be converted
def _process(delta) -> None:
    global min_altitude
    global engine_on
    global attack_mode
    global timer
    global AOA

    # control logics, only simple if-else statements and variable assignments are allowed, do not use loops!
    pitch_damper = get_pitch_damper(0.5)
    autotrim = get_autotrim(0.2)
    AOA = get_AOA() # this is also an imported function
    mach_number = get_mach_number()
    gear_control = 0 if smooth(LandingGear, 0.5) < 0.5 else 1
    engine_on = True if Activate8 else False

    if IAS > 30:
        pitch_control = clamp11(Pitch + pitch_damper + autotrim) # clamp11() is a function that imported from _common_FCS.py
        roll_control = clamp11(Roll - RollRate*0.05)
        yaw_control = clamp11(Yaw - YawRate*0.05)
    elif IAS > 5:
        pitch_control = clamp11(Pitch + pitch_damper)
        roll_control = Roll
        yaw_control = Yaw
    else:
        pitch_control = Pitch * 1.2
        yaw_control = Yaw * 1.2
        roll_control = Roll * 1.2

    if IAS > 30 and AltitudeAgl > min_altitude:
        brake_control = Brake
    else:
        brake_control = 0.0

    if TargetSelected and engine_on:
        timer += delta
    else:
        timer = 0.0

    if engine_on:
        if Throttle > 0.95:
            throttle_control = 1.0
        else:
            throttle_control = Throttle*0.7
    else:
        throttle_control = 0.0

    print("end of main loop")
    print(pitch_control, roll_control, yaw_control, throttle_control)

# below are helper functions, make sure all functions have return values in all cases.
# it's not recommended to call other helper functions inside helper functions
# and do not use recursion!
def get_autotrim(max_trim) -> float:
    if TargetSelected:
        return 0.0
    elif engine_on == False:
        return 0.0

def get_AOA_feedback(pitchinput) -> float:
    global AOA
    temp = PID(0,PitchRate,1,2,3)
    start = pitchinput
    end = start+temp
    result = end * PID(0,Pitch+temp,2,3,4) + start
    return result

def get_pitch_damper(max_damper) -> float:
    global min_altitude
    if AltitudeAgl < min_altitude:
        return 0.0
    if abs(Pitch) < 0.05:
        return 0.0
    return clamp(PitchRate * 0.1, -max_damper, max_damper)

# a bad example here: this function returns nothing so it will be ignored
def toggle_gear(temp)-> bool:
    global engine_on
    pass

# optional: you can call the main function for debugging
if __name__ == "__main__":
    Activate8 = True
    Pitch = 0.1
    Roll = 0.2
    Yaw = 0.3
    IAS = 50.0
    AltitudeAgl = 20.0
    Throttle = 0.5
    globals()[main_loop_name](0.01)