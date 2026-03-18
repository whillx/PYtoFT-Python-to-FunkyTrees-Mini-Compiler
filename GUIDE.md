# GUIDE

## Project Understanding

- `PYtoFT` is a mini-compiler that converts a constrained subset of Python control logic into SimplePlanes / SimplePlanes2 Funky Trees expressions.
- The main output is a set of XML `<Setter>` entries, where each converted Python variable becomes a single-line C-style expression evaluated every frame in-game.
- The tool is designed around a "main script" model:
  - It reads global variables from the script.
  - It also reads variables declared inside a designated main function (`main_loop_name`).
  - Those variables become the primary output variables, unless excluded.
- The tool supports importing helper modules and conceptually inlines their globals and functions into the main script, recursively across nested imports.
- Conversion is intentionally limited so the final expression graph is compatible with Funky Trees:
  - Helper functions must be reducible to inline expressions.
  - Function parameters with default values are supported and should fall back to their defaults when not overridden by the caller.
  - Function calls should disappear from the final output.
  - Only allowed names should remain in the final expressions.
- Allowed names in generated expressions are expected to be:
  - Built-in Funky Trees symbols from `FT_functions.py`
  - Main script globals
  - Variables declared inside the main function
  - Explicitly excluded variables from the main script
- The `exclude` list is used to prevent certain variables from becoming generated setter variables, while still allowing them to appear in expressions when needed.
- Output ordering matters: generated setter variables should follow the declaration order from the main script.
- The implementation uses Python's `ast` module to parse source code and transform Python logic into single-line conditional / arithmetic expressions.
- The tool can deliver output in three ways:
  - Inject setters into an aircraft `.xml` file
  - Update a matching `.xml` file next to the source `.py`
  - Print generated XML to the console for manual copy-paste

## Inferred Workflow

- User writes a Python script using the project's restricted conversion rules.
- Script imports `lib.FT_functions` for built-in Funky Trees symbols and helpers.
- Script defines:
  - `main_loop_name`
  - Optional `exclude` list
  - Global variables
  - Optional helper functions
  - Optional main loop function
- The tool parses the script, resolves imported modules, reduces helper functions into inline expressions, and converts the result into Funky Trees-compatible XML setters.
- The generated XML is either injected into a craft file or printed.

## Important Constraints

- This is not a general Python compiler; it only supports a limited subset of Python.
- Classes and recursion are not supported.
- Default parameter values are supported for reducible helper functions.
- Helper functions must have return values on all paths.
- If a function cannot be reduced into a single expression, the tool should report an error.
- The target format is C-like / Funky Trees syntax, not executable Python.
- Running the tool can overwrite existing Variable Setter Funky Trees code in the target craft XML, so backups are important.
