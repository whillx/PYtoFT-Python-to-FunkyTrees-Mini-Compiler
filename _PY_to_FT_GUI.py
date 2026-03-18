# SPDX-License-Identifier: GPL-3.0-or-later
import json
import os
import sys
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from lib.FT_converter import py_to_ft
from lib.write_to_xml import insert_variables_text


VERSION = "0.2"
def get_executable_dir() -> Path:
    if getattr(sys, 'frozen', False):
        return Path(os.path.dirname(sys.executable))
    return Path(__file__).resolve().parent

def get_resource_dir() -> Path:
    if getattr(sys, 'frozen', False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parent

APP_DIR = get_executable_dir()
RESOURCE_DIR = get_resource_dir()
CONFIG_FILE = APP_DIR / "_PY_to_FT_config.json"
SCRIPT_KEY = "gui_last_script_path"
OUTPUT_XML_KEY = "gui_last_output_xml_path"


def load_config() -> dict:
    if not CONFIG_FILE.exists() or CONFIG_FILE.stat().st_size == 0:
        return {}
    try:
        with CONFIG_FILE.open("r", encoding="utf-8") as config_file:
            data = json.load(config_file)
            return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def save_config(updates: dict) -> None:
    config = load_config()
    config.update(updates)
    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with CONFIG_FILE.open("w", encoding="utf-8") as config_file:
        json.dump(config, config_file, indent=4)


def build_xml_setters(export_var_dic: dict) -> str:
    xml_lines = []
    for variable, function in export_var_dic.items():
        function_escaped = (
            function.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
        )
        xml_lines.append(
            f'    <Setter variable="{variable}" function="{function_escaped}" priority="0" />'
        )
    return "\n".join(xml_lines)


class PYtoFTGui:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title(f"PYtoFT GUI v{VERSION}")
        self.root.geometry("900x650")
        self.root.minsize(760, 520)
        self._set_window_icon()

        config = load_config()
        self.script_path_var = tk.StringVar(value=config.get(SCRIPT_KEY, ""))
        self.output_xml_path_var = tk.StringVar(value=config.get(OUTPUT_XML_KEY, ""))
        self.status_var = tk.StringVar(value="Load a Python main script to begin.")

        self._build_ui()
        self._refresh_textbox("")

    def _set_window_icon(self) -> None:
        icon_path = RESOURCE_DIR / "images" / "py_to_ft.ico"
        if not icon_path.exists():
            return
        try:
            self.root.iconbitmap(default=str(icon_path))
        except tk.TclError:
            pass

    def _safe_save_config(self, updates: dict) -> bool:
        try:
            save_config(updates)
            return True
        except OSError as exc:
            self.status_var.set("Could not save GUI preferences. The tool will still work for this session.")
            messagebox.showwarning(
                "Config Save Failed",
                f"Could not save GUI preferences to:\n{CONFIG_FILE}\n\n{exc}",
            )
            return False

    def _build_ui(self) -> None:
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(1, weight=1)

        controls = ttk.Frame(self.root, padding=12)
        controls.grid(row=0, column=0, sticky="ew")
        controls.columnconfigure(1, weight=1)

        ttk.Label(controls, text="Main Script").grid(row=0, column=0, sticky="w", padx=(0, 8), pady=(0, 8))
        ttk.Entry(controls, textvariable=self.script_path_var).grid(row=0, column=1, sticky="ew", pady=(0, 8))
        ttk.Button(controls, text="Load...", command=self.load_script).grid(row=0, column=2, padx=(8, 0), pady=(0, 8))

        ttk.Label(controls, text="Target XML").grid(row=1, column=0, sticky="w", padx=(0, 8), pady=(0, 8))
        ttk.Entry(controls, textvariable=self.output_xml_path_var).grid(row=1, column=1, sticky="ew", pady=(0, 8))
        ttk.Button(controls, text="Browse...", command=self.choose_output_xml).grid(row=1, column=2, padx=(8, 0), pady=(0, 8))

        button_row = ttk.Frame(controls)
        button_row.grid(row=2, column=0, columnspan=3, sticky="w", pady=(4, 0))
        ttk.Button(button_row, text="Convert", command=self.convert).pack(side="left")
        ttk.Button(button_row, text="Clear Output XML", command=self.clear_output_xml).pack(side="left", padx=(8, 0))
        ttk.Button(button_row, text="Copy Result", command=self.copy_result).pack(side="left", padx=(8, 0))

        output_frame = ttk.Frame(self.root, padding=(12, 0, 12, 12))
        output_frame.grid(row=1, column=0, sticky="nsew")
        output_frame.columnconfigure(0, weight=1)
        output_frame.rowconfigure(1, weight=1)

        ttk.Label(
            output_frame,
            text="Result (used for copy-paste when no target XML file is selected)"
        ).grid(row=0, column=0, sticky="w", pady=(0, 6))

        self.result_text = tk.Text(output_frame, wrap="word", undo=False)
        self.result_text.grid(row=1, column=0, sticky="nsew")

        scrollbar = ttk.Scrollbar(output_frame, orient="vertical", command=self.result_text.yview)
        scrollbar.grid(row=1, column=1, sticky="ns")
        self.result_text.configure(yscrollcommand=scrollbar.set)

        status = ttk.Label(self.root, textvariable=self.status_var, anchor="w", padding=(12, 0, 12, 10))
        status.grid(row=2, column=0, sticky="ew")

    def _refresh_textbox(self, content: str) -> None:
        self.result_text.delete("1.0", tk.END)
        if content:
            self.result_text.insert("1.0", content)

    def load_script(self) -> None:
        initial_dir = self._initial_script_dir()
        file_path = filedialog.askopenfilename(
            title="Select main Python script",
            initialdir=initial_dir,
            filetypes=[("Python files", "*.py"), ("All files", "*.*")],
        )
        if not file_path:
            return
        self.script_path_var.set(file_path)
        self._safe_save_config({SCRIPT_KEY: file_path})
        if not self.output_xml_path_var.get().strip():
            default_xml = str(Path(file_path).with_suffix(".xml"))
            self.output_xml_path_var.set(default_xml)
        self.status_var.set(f"Loaded script: {Path(file_path).name}")

    def choose_output_xml(self) -> None:
        initial_dir = self._initial_output_dir()
        file_path = filedialog.askopenfilename(
            title="Select target XML file",
            initialdir=initial_dir,
            filetypes=[("XML files", "*.xml"), ("All files", "*.*")],
        )
        if not file_path:
            self.status_var.set("No XML selected. Conversion can still output to the text box.")
            return
        self.output_xml_path_var.set(file_path)
        self._safe_save_config({OUTPUT_XML_KEY: file_path})
        self.status_var.set(f"Target XML selected: {Path(file_path).name}")

    def clear_output_xml(self) -> None:
        self.output_xml_path_var.set("")
        self._safe_save_config({OUTPUT_XML_KEY: ""})
        self.status_var.set("Target XML cleared. Next conversion will use copy-paste output unless you select an XML file.")

    def copy_result(self) -> None:
        content = self.result_text.get("1.0", tk.END).strip()
        if not content:
            messagebox.showinfo("Copy Result", "There is no result to copy yet.")
            return
        self.root.clipboard_clear()
        self.root.clipboard_append(content)
        self.root.update_idletasks()
        self.status_var.set("Result copied to clipboard.")

    def convert(self) -> None:
        script_path_text = self.script_path_var.get().strip()
        if not script_path_text:
            messagebox.showwarning("Missing Script", "Please load a Python main script first.")
            return

        script_path = Path(script_path_text)
        if not script_path.exists() or script_path.suffix.lower() != ".py":
            messagebox.showerror("Invalid Script", "The selected main script does not exist or is not a .py file.")
            return

        self._safe_save_config({SCRIPT_KEY: str(script_path)})

        try:
            export_var_dic = py_to_ft(script_path)
            xml_setters = build_xml_setters(export_var_dic)
        except Exception as exc:
            messagebox.showerror("Conversion Error", str(exc))
            self.status_var.set("Conversion failed.")
            return

        target_xml = self._resolve_output_xml(script_path)
        if target_xml is not None:
            try:
                insert_variables_text(target_xml, xml_setters, path_checked=False)
            except Exception as exc:
                self._refresh_textbox(xml_setters)
                self.result_text.focus_set()
                self.status_var.set("XML write failed. Generated setters are shown for copy-paste.")
                messagebox.showwarning(
                    "XML Write Failed",
                    f"Could not update the selected XML file.\n\n{exc}\n\nThe generated setters are shown in the text box instead.",
                )
                return

            self._refresh_textbox(xml_setters)
            self.status_var.set(f"Converted successfully and updated: {target_xml.name}")
            messagebox.showinfo("Conversion Complete", f"Updated XML file:\n{target_xml}")
            return

        self._refresh_textbox(xml_setters)
        self.result_text.focus_set()
        self.status_var.set("Converted successfully. No XML file selected, so setters are shown for copy-paste.")
        messagebox.showinfo(
            "Conversion Complete",
            "No target XML file was selected. The generated setters are displayed in the text box for copy-paste.",
        )

    def _resolve_output_xml(self, script_path: Path) -> Path | None:
        current_output = self.output_xml_path_var.get().strip()
        if current_output:
            output_path = Path(current_output)
            if output_path.exists():
                self._safe_save_config({OUTPUT_XML_KEY: str(output_path)})
                return output_path

        initial_dir = self._initial_output_dir(default_script=script_path)
        selected_path = filedialog.askopenfilename(
            title="Select target XML file (Cancel to use copy-paste output)",
            initialdir=initial_dir,
            filetypes=[("XML files", "*.xml"), ("All files", "*.*")],
        )
        if not selected_path:
            self.output_xml_path_var.set("")
            self._safe_save_config({OUTPUT_XML_KEY: ""})
            return None

        output_path = Path(selected_path)
        self.output_xml_path_var.set(str(output_path))
        self._safe_save_config({OUTPUT_XML_KEY: str(output_path)})
        return output_path

    def _initial_script_dir(self) -> str:
        current_script = self.script_path_var.get().strip()
        if current_script:
            current_path = Path(current_script)
            if current_path.parent.exists():
                return str(current_path.parent)
        return str(Path.cwd())

    def _initial_output_dir(self, default_script: Path | None = None) -> str:
        current_output = self.output_xml_path_var.get().strip()
        if current_output:
            current_path = Path(current_output)
            if current_path.parent.exists():
                return str(current_path.parent)
        if default_script and default_script.parent.exists():
            return str(default_script.parent)
        current_script = self.script_path_var.get().strip()
        if current_script:
            current_path = Path(current_script)
            if current_path.parent.exists():
                return str(current_path.parent)
        return str(Path.cwd())


def main() -> None:
    root = tk.Tk()
    app = PYtoFTGui(root)
    root.mainloop()


if __name__ == "__main__":
    main()
