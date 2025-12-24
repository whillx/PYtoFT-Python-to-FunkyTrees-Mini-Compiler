# PYtoFT
Python to Funky Trees Mini Compiler
by Whills - v0.1

## Overview

PYtoFT converts variables in a Python script into condensed, single-line functions compatible with the SimplePlanes Funky Trees system.

The tool can either:
- Automatically update the .xml file of a SimplePlanes craft, or
- Output the generated XML code directly to the console.

## How It Works

- Parses variable definitions from a Python script.
- Converts them into SimplePlanes-compatible Funky Trees expressions.
- Outputs the result as XML, either by injecting it into an existing craft file or printing it for manual use.

## How to Use (Windows)

- Go to the Releases section and download the .zip file.
- Unzip the downloaded archive.
- Place the Python .py file you want to convert in the same directory as PY_to_FT.exe.
- Double-click PY_to_FT.exe to start the conversion.
- If you choose to export directly to your SimplePlanes .xml save:
    - Select the folder containing the .xml file.
    - Ensure the .xml file has the same base name as your .py file.
- If you choose to export to the current directory:
    - Make sure the corresponding .xml file is already present in the same directory as the .py file.

## Run Locally (Python)

- Install Python 3

- Download or clone the project

- Run:
```bash
python _PY_to_FT.py
```

## Example Script

- The Python script must have the same name as the target SimplePlanes .xml craft file.
- Do not start your file name with an underscore.

```python
from _FT_functions import * # import built-in Funky Trees functions and variables.
main_loop_name = "_process" # the name of the main function
exclude = ["start_mission_timer"]  # list of variable names to be excluded from the conversion, you may need to add some aircraft-part-exported variables here.

# ========== program start ==========
# optional: declare your global variables
min_altitude = 3.0
start_mission_timer = False

# main loop function
# all variables declared inside this function as well as all global variables will be converted to in-game variables
# you can also do not write this function, then only global variables will be converted
def _process() -> None:
    global min_altitude
    mach_number = get_mach_number()
    if AltitudeAgl > min_altitude:
        pitch_control = Pitch - 0.01*PitchRate
    else:
        pitch_control = Pitch

# below are helper functions, make sure all functions have return values in all cases.
# it's not recommended to call other helper functions inside helper functions.
# default argument values are *NOT* supported and do *NOT* use recursion!

def get_mach_number() -> float:
    speed_of_sound = 340.3
    return TAS/(speed_of_sound-0.0041*Altitude if Altitude < 11000 else 295.2)

def foo(some_value) -> float:
    input_val = some_value
    if Altitude > 200:
        input_val += 2
    else:
        input_val -=2
    result = input_val + bar()
    return result
    
def bar()-> float :
    if IAS>10:
        return 5
    else:
        return 0
...
```