# PYtoFT

## What does it do
This project is a tool that converts a python script into an funky trees expressions (C-like expressions) that can be used in the game SimplePlanes. It collects the variables used in the python script (main script), then converts them into single line C-style expressions that can be used to be evaluated every frame in the SimplePlanes game, to control the aircraft behaviors. It can insert the conveted funky trees into the aircraft XML files.

## Main Logic
- Reads a python script (main script), collect all global variables and variables within the main funciton (name defined in the main script) as the main variable (setter variable), then convert their values into single line expressions.

- If the main script imports other modules (external scripts), then the modules' global variables and funcitons should be appended into the main script, and treat as part of the main script, if the imported module imports another module, do the same logic.

- The converted expressions should only includes the following variables: Variables defined in the FT_functions.py; the global variables and main function variables in the main script (setter variables); the "exclude" variables defined in the main script.

- If a variable name is in the exclude list defined in the main script, it should not be included as a main variable (setter variable).

- For all functions in the main script, they should all be reduced into single line expressions, with input parameters replaced with the caller's arguments. If a funciton cannot be reduced, errors should be reported to user.

- If a function's parameter has a default value, if not overridden by the argument, then the default value should be used.

- The reduced expressions should be converted to C style expressions.

## Expected result
- The output should have each setter variable have their corresponding expressions, which only contains: setter variables; variables defined in the FT_functions.py; the "exclude" variables defined in the main script.

- The order of the setter variable should follow the order in the main script.

- Any function names are NOT allowed in the reduced expressions.

## Resources
- Guide to funky trees: https://www.simpleplanes.com/Forums/View/1042680/Funky-Trees
- README.md