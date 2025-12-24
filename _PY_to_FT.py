# SPDX-License-Identifier: GPL-3.0-or-later
from lib.FT_converter import py_to_ft, load_py_file
from lib.write_to_xml import insert_variables_text
import json
import os
from pathlib import Path
import tkinter as tk
from tkinter import filedialog

version = "0.1"
write_to_xml = False
CONFIG_FILE = Path("_PY_to_FT_config.json")
CONFIG_KEY = "aircraft_directory"
PREFERENCE_KEY = "export_to_aircraft_directory"

def choose_directory():
    root = tk.Tk()
    root.withdraw()  # Hide the empty root window
    folder = filedialog.askdirectory(title="Choose SimplePlanes AircraftDesigns directory")
    root.destroy()
    return folder

def load_config():
    if not CONFIG_FILE.exists():
        return None
    if CONFIG_FILE.stat().st_size == 0:
        # Empty file
        return None
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        # Corrupt or unreadable file
        return None

def save_config(preference: int, path: str):
    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump({PREFERENCE_KEY: preference, CONFIG_KEY: path,},f,indent=4)

def is_valid_directory(path: str) -> bool:
    return (
        path
        and os.path.isdir(path)
        and os.access(path, os.W_OK)
        and os.path.basename(path) == "AircraftDesigns"
    )

def get_target_directory():
    config = load_config()

    if config:
        preference = config.get(PREFERENCE_KEY)
        if preference == 0:
            return None
        path = config.get(CONFIG_KEY)
        if path and os.path.isdir(path):
            return path

    # Ask user if config is missing or invalid
    while True:
        print("Do you want to directly export to your SimplePlanes XML savings directory?\n")
        print("1: Yes (make sure you have an aircraft with the same name as your .py file)\n2: No (please put your aircraft XML file in current directory)\n")
        user_input = input("Enter 1 or 2: ")
        if user_input.strip() == "1" or user_input.strip() == "2":
            if user_input.strip() == "2":
                save_config(0,"")
                return None
            break
        else:
            print("Invalid input. Please enter 1 or 2.\n")
    print("Please select the your SimplePlanes AircraftDesigns directory:\n")
    while True:
        folder = choose_directory()
        if not folder:
            input("No directory selected, press Enter to try again.\n")
        elif not is_valid_directory(folder):
            input("Please select the folder named 'AircraftDesigns', press Enter to try again.\n")
        else:
            input(f"You have selected: {folder}\n\nPress Enter to continue.\n")
            save_config(1, folder)
            return folder

def main():
    source_py_files = load_py_file()
    if not source_py_files:
        raise FileNotFoundError("No python source files found in current directory!")
    if len(source_py_files) > 1:
        print(f"Multiple .py files found, using the first one: {source_py_files[0].name}\n")
    else:
        print(f"Using source file: {source_py_files[0].name}\n")

    source_py_path = source_py_files[0]
    input("Press Enter to start conversion.\n")
    export_var_dic = py_to_ft(source_py_path)

    if target_dir:
        source_xml_path = Path(target_dir) / f"{source_py_path.stem}.xml"
    else:
        source_xml_path = source_py_path.with_suffix('.xml')
    if os.path.exists(source_xml_path):
        input(f"You are going to overwrite all funkey tree functions in {source_xml_path.name}. \n\nPress Enter to continue.\n")
        print(f"Writing to XML file: {source_xml_path.name}\n")
        write_to_xml = True
    else:
        input(f"{source_xml_path.name} does not exist in {target_dir}. Output will be written to console. \n\nPress Enter to continue.\n")
        write_to_xml = False

    # Convert dictionary to XML setter strings
    xml_setters = ""
    for variable, function in export_var_dic.items():
        # Escape XML special characters in the function string
        function_escaped = function.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        setter = f'    <Setter variable="{variable}" function="{function_escaped}" priority="0" />'
        xml_setters += setter + "\n"

    # Print or save the XML strings
    if write_to_xml:
        #add delta variable
        xml_setters = xml_setters.rstrip()
        insert_variables_text(source_xml_path, xml_setters, path_checked = True)
        print(f"{source_xml_path.name} has been updated with converted functions.\n")
    else:
        print(xml_setters)


if __name__ == "__main__": 
    print(f'Python to Funky Trees Converter by Whills v{version}\n')
    try:
        target_dir = get_target_directory()
        if target_dir:
            print("Using output directory:", target_dir, "\n")
        else:
            print("Using current directory as output directory.\n")
        main()
    except Exception as e:
        print(f"ERROR: {e}\n")
    input("Press any key to exit....")