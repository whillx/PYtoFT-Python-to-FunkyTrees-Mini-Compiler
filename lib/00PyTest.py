from lib.FT_functions import *
main_loop_name = "_process"

#============== Program Start ==============
# static global values
min_Altitude = 2.0

def _process(delta)-> None:
    pitch_control = 0.0
    roll_control = 0.0
    yaw_control = 0.0
    pitch_damper = 0.0
    AOA_feedback = 0.0
    AOA = 0.0
    mission_timer = 0.0
    mission_started = False
    autotrim = 0.0
    flap_L = 0.0
    flap_R = 0.0

#mission timer, starts when a target is selected
    mission_started = True if TargetSelected else False
    if mission_started:
        mission_timer += delta
    else:
        mission_timer = 0.0

#flight controls
    pitch_control = clamp(Pitch + pitch_damper + AOA_feedback + autotrim, -1, 1)
    pitch_damper = get_pitch_damper(Pitch)
    autotrim = get_autotrim(pitch_control)
    AOA_feedback = get_AOA_feedback(AOA)+flap_R

    pass

def get_pitch_damper(pitch_input):
    if abs(pitch_input)<0.05:
        return 0.0
    return PitchRate * 0.02

def get_autotrim(pitchinput):
    if abs(pitchinput)<0.1:
        if IAS < 5:
            if Pitch > 2.0:
                if PitchRate > 0.1:
                    return 0.1
                else:
                    return 8964
            return 0.0
    elif abs(pitchinput)<0.5:
        return pitchinput * 0.05
    elif abs(pitchinput)<0.8:
        return 0
    return pitchinput * 0.1

def get_AOA_feedback(aoa_input):
    if abs(aoa_input)<1.0:
        return 0.0
    return aoa_input * 0.05