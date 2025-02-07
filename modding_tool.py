import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import xml.etree.ElementTree as ET
import zipfile
from modules.units_editor_module import UnitsEditor
import importlib.util
from utils import load_file, save_file, load_mod_info, load_xml, validate_xml


def create_editor_tab(parent, file_path, tab_label):
    """Create a standard editor tab with text area and save button"""
    frame = ttk.Frame(parent)
    
    # File info
    ttk.Label(frame, text=f"Editing: {file_path}").pack(anchor="w", padx=5, pady=2)
    
    # Text area with scroll
    text_area = tk.Text(frame, wrap="word")
    scrollbar = ttk.Scrollbar(frame, command=text_area.yview)
    text_area.config(yscrollcommand=scrollbar.set)
    
    # Layout
    text_area.pack(side="left", fill="both", expand=True, padx=5, pady=5)
    scrollbar.pack(side="right", fill="y")
    
    # Load content
    content = load_file(file_path)
    text_area.delete("1.0", tk.END)
    text_area.insert("1.0", content)
    
    # Save button
    save_btn = ttk.Button(frame, text="Save", 
                         command=lambda: save_file(file_path, text_area.get("1.0", tk.END)))
    save_btn.pack(anchor="e", padx=5, pady=5)
    
    return frame


def package_mod():
    # Package the mod folder: "Example mod/Baby seals"
    mod_dir = os.path.join("Example mod", "Baby seals")
    if not os.path.isdir(mod_dir):
        messagebox.showerror("Error", f"Mod folder not found: {mod_dir}")
        return
    zip_filename = "baby_seals_mod.zip"
    try:
        with zipfile.ZipFile(zip_filename, "w", zipfile.ZIP_DEFLATED) as zipf:
            for root_dir, dirs, files in os.walk(mod_dir):
                for file in files:
                    file_path = os.path.join(root_dir, file)
                    arcname = os.path.relpath(file_path, os.path.join("Example mod"))
                    zipf.write(file_path, arcname)
        messagebox.showinfo("Package Mod", f"Mod packaged as {zip_filename}")
    except Exception as e:
        messagebox.showerror("Package Mod", f"Error packaging mod: {e}")


def preview_mod_info():
    # Opens a new window to preview mod info from mod.xml
    mod_file = os.path.join("Example mod", "Baby seals", "mod.xml")
    mod_info = load_mod_info(mod_file)
    preview_win = tk.Toplevel()
    preview_win.title("Mod Info Preview")
    text = tk.Text(preview_win, wrap="word", width=50, height=15)
    text.insert("1.0", mod_info)
    text.config(state="disabled")
    text.pack(padx=20, pady=20)
    # Center the preview window
    preview_win.update_idletasks()
    window_width = preview_win.winfo_width()
    window_height = preview_win.winfo_height()
    screen_width = preview_win.winfo_screenwidth()
    screen_height = preview_win.winfo_screenheight()
    x_coordinate = int((screen_width / 2) - (window_width / 2))
    y_coordinate = int((screen_height / 2) - (window_height / 2))
    preview_win.geometry(f"+{x_coordinate}+{y_coordinate}")


def create_xml_validator_tab(parent):
    frame = ttk.Frame(parent)
    # List of XML files to validate
    xml_files = [
        os.path.join("Example mod", "Baby seals", "mod.xml"),
        os.path.join("Example mod", "Baby seals", "gui", "seals_deploy.xml"),
        os.path.join("Example mod", "Baby seals", "units", "seals_unit.xml"),
        os.path.join("Example mod", "Baby seals", "units", "seals_human_identities.xml"),
        os.path.join("Example mod", "Baby seals", "entities", "seals_humans.xml"),
        os.path.join("Example mod", "Baby seals", "equipment", "seals_binds.xml")
    ]
    label = ttk.Label(frame, text="Select XML file to validate:")
    label.pack(anchor="w", padx=5, pady=5)

    validator_var = tk.StringVar()
    validator_combo = ttk.Combobox(frame, textvariable=validator_var, values=xml_files, width=60)
    validator_combo.pack(padx=5, pady=5)
    if xml_files:
        validator_combo.current(0)

    btn_validate = ttk.Button(frame, text="Validate", command=lambda: validate_xml(validator_var.get()))
    btn_validate.pack(padx=5, pady=5)
    return frame


def load_plugins(notebook):
    """Load all plugin modules from the modules directory"""
    plugins_dir = os.path.join(os.path.dirname(__file__), "modules")
    if not os.path.isdir(plugins_dir):
        return
        
    for filename in os.listdir(plugins_dir):
        if filename.endswith("_module.py"):
            try:
                plugin_path = os.path.join(plugins_dir, filename)
                spec = importlib.util.spec_from_file_location(filename[:-3], plugin_path)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                if hasattr(module, "get_plugin_tab"):
                    title, widget = module.get_plugin_tab(notebook)
                    notebook.add(widget, text=title)
            except Exception as e:
                print(f"Failed to load plugin {filename}: {e}")


def main():
    root = tk.Tk()
    root.title("Modding Tool for Baby Seals Mod")

    # Create Notebook
    notebook = ttk.Notebook(root)
    notebook.pack(fill="both", expand=True)

    # Load dynamic plugins from modules folder
    load_plugins(notebook)

    # Center the main window
    root.update_idletasks()
    window_width = root.winfo_width()
    window_height = root.winfo_height()
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    x_coordinate = int((screen_width / 2) - (window_width / 2))
    y_coordinate = int((screen_height / 2) - (window_height / 2))
    root.geometry(f"+{x_coordinate}+{y_coordinate}")

    root.mainloop()


if __name__ == "__main__":
    main() 