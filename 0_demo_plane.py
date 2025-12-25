# this is a demo script, the file name must be the same as your aircraft XML file name. Don't start the file name with an underscore.

from lib.FT_functions import * # import built-in Funky Trees functions and variables.
# from _user._common_FCS import * # experimental: your can import your common functions so you don't neeed to rewrite them in every script.
main_loop_name = "_process" # the name of the main function
exclude = ["start_mission_timer"]  # list of variable names to be excluded from conversion,
                                   # you may need to add some aircraft-part-exported variables here

# ========== program start ==========

# optional: declare your global variables
min_altitude = 3.0
start_mission_timer = False
timer = 0.0
AOA = 0.0
delta = 0.0
AIControl = False

# main loop function: the control logic in this function will be executed once every frame in game.
# all variables declared inside this function + all global variables will be converted to in-game variables
# you can also do not write this function, then only global variables will be converted
def _process() -> None:
    global min_altitude
    global start_mission_timer
    global timer
    global AOA
    global delta
    global AIControl

    engine_on = True if Fuel > 0.01 else False
    AIControl = True if FireWeapons and Time<1 else AIControl
    last_frame_time = Time
    delta = Time-last_frame_time

    # control logic, only simple if-else statements and variable assignments are allowed, do not use loops!
    AOA = get_AOA()
    control_limiter = clamp(30000*pow(IAS,-2)*(0.9+0.1*Fuel)*(0.7 if VerticalG<1 else 1),0.01,1)
    Glimiter = 1
    Glimiter = get_Glimiter(-3,9,Glimiter)
    mach_number = get_mach_number()
    pitch_damper = get_pitch_damper(1)*control_limiter*inverselerp(2,5,abs(PitchRate))
    roll_damper = RollRate*0.005*inverselerp(20,200,IAS)*control_limiter*inverselerp(2,8,abs(RollRate))
    yaw_damper = -YawRate*(0.02+0.03*inverselerp(250,100,IAS))*control_limiter*inverselerp(1,4,abs(YawRate))
    autotrim = get_autotrim(0.3,0.2)
    AOA_feed = get_AOA_feed(0.5)
    canopy_opened = Activate1

    if IAS > 12:
        pitch_control = smooth(Pitch,0.5+1.5*inverselerp(300,50,IAS))*control_limiter*Glimiter
        roll_control = smooth(Roll,2)*control_limiter
        yaw_control = smooth(Yaw,2)*control_limiter
    elif canopy_opened == False:
        pitch_control = smooth(Pitch,4)
        roll_control = smooth(Roll,4)
        yaw_control = Yaw
    else:
        pitch_control = Pitch * 2
        roll_control = Roll * 2
        yaw_control = Yaw * 2

    if IAS > 30 and AltitudeAgl > min_altitude:
        brake_control = clamp01(Brake + clamp01(Activate2))
    else:
        brake_control = clamp01(Activate2)

    if start_mission_timer:
        timer += delta
    else:
        timer = 0.0

    if engine_on: # "engine_on is True" is not supported!
        if Throttle > 0.95:
            if AIControl:
                thrust_control = 0.7
            else:
                thrust_control = 1.0
        else:
            thrust_control = Throttle*0.702
    else:
        thrust_control = 0.0

    canard_pitch = get_canard_pitch(pitch_control) + AOA_feed + get_AOA_damper() + autotrim
    canardL = clamp11(-canard_pitch - clamp01(-(roll_control+roll_damper))*inverselerp(-5,-20, AOA)*0.5)
    canardR = clamp11(-canard_pitch - clamp01( (roll_control+roll_damper))*inverselerp(-5,-20, AOA)*0.5)
    
    flaperonL = clamp11(pitch_control*(1 if pitch_control < 0 else 0.5) + pitch_damper +\
        (roll_control+roll_damper)*inverselerp(-30,-20,AOA))
    flaperonR = clamp11(pitch_control*(1 if pitch_control < 0 else 0.5) + pitch_damper -\
        (roll_control+roll_damper)*inverselerp(-30,-20,AOA))
    
    rudder = yaw_control + yaw_damper

    print("main loop executed successfully.")

# below are helper functions, make sure all functions have return values in all cases.
# it's not recommended to call other helper functions inside helper functions.
# default argument values are *NOT* supported and do *NOT* use recursion!

def get_AOA_feed(max_feedback) -> float:
    global AOA
    target_AOA = (30+40*clamp01(-Activate8)-10*clamp01(abs(smooth(Roll,2))*2))*smooth(clamp(Pitch,-1,0),1)
    result = clamp((target_AOA-AOA)*0.02,0,max_feedback)
    if IAS > 5 and abs(AngleOfSlip) > 45:
        return 0
    return result*inverselerp(30,80,IAS) - (AOA/45)

def get_AOA_damper() -> float:
    global AOA
    return -rate(AOA)*0.007*inverselerp(200,100,IAS)*clamp01(Activate8)

def get_pitch_damper(max_damper) -> float:
    pitch_rate = clamp(PitchRate, -180, 180)
    damper_multiplier = 0.01 + 0.005*inverselerp(400,200,IAS)
    return clamp(-pitch_rate * damper_multiplier, -max_damper, max_damper)

def get_canard_pitch(pitch_input) -> float:
    global AOA
    pitch_limiter = (0.5 if pitch_input < 0 else 0.1+0.9*inverselerp(80,30,IAS))
    aoa_fade = inverselerp(30+40*clamp01(-Activate8),10,abs(AOA))
    return pitch_input*pitch_limiter*aoa_fade
    
def get_Glimiter(min_G, max_G, limiter)-> float:
    limit_rate = 1.5 if rate(limiter) < 0 else 0.1
    return smooth(
        0.25
        +0.75*inverselerp(max_G+1,max_G-1,VerticalG)
        -0.75*inverselerp(min_G+1,min_G-1,VerticalG), limit_rate
        )

def get_autotrim(manual_trim_mult, max_trim)-> float:
    global AOA
    target_pitch_rate_offset = clamp01(0.2-rate(Altitude))
    target_pitch_rate = clamp(PitchAngle + AOA - target_pitch_rate_offset,-1,1)
    smooth_val = (0.03
        *inverselerp(40,15,abs(PitchAngle))
        *inverselerp(35,15,abs(RollAngle))
        *inverselerp(20,10,abs(PitchRate)+abs(RollRate))
        *inverselerp(0.3,0.1,abs(Pitch)+abs(Roll))
        )
    autotrim_limiter = inverselerp(1,0,abs(Pitch)) * inverselerp(20,50,IAS) * inverselerp(90,60,abs(RollAngle)) * clamp01(1-2*abs(Trim))
    return (
        smooth(max_trim*clamp01(Time>0.5)*clamp11(PID(target_pitch_rate,PitchRate,2,0,0.2)), smooth_val) * autotrim_limiter 
        + manual_trim_mult*Trim
        )

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

# a bad example here: this function returns nothing so it will be ignored
# def toggle_gear(temp) :
#     global engine_on
#     pass

# optional: you can simulate the game loop for debugging
globals()[main_loop_name]()