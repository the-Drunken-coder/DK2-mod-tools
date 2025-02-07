import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import xml.etree.ElementTree as ET
import zipfile
from modules.units_editor_module import UnitsEditor
import importlib.util
import sys
from utils import load_file, save_file, load_mod_info, load_xml, validate_xml
from modules import config_editor_module
from modules.mod_files import mod_files

def get_unit_file(mod_path):
    """Get the unit XML file for a mod."""
    global mod_files
    if mod_files.mod_path != mod_path:
        mod_files.mod_path = mod_path
        mod_files.scan_mod_directory()
    return mod_files.get_unit_file()

def get_equipment_file(mod_path):
    """Get the equipment binds XML file for a mod."""
    global mod_files
    # Only scan if the path has changed
    if mod_files.mod_path != mod_path:
        mod_files.mod_path = mod_path
        mod_files.scan_mod_directory()
    return mod_files.get_equipment_file()

def get_entities_file(mod_path):
    """Get the entities XML file for a mod."""
    global mod_files
    # Only scan if the path has changed
    if mod_files.mod_path != mod_path:
        mod_files.mod_path = mod_path
        mod_files.scan_mod_directory()
    return mod_files.get_entities_file()

def get_gui_file(mod_path):
    """Get the GUI XML file for a mod."""
    global mod_files
    # Only scan if the path has changed
    if mod_files.mod_path != mod_path:
        mod_files.mod_path = mod_path
        mod_files.scan_mod_directory()
    return mod_files.get_gui_file()

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
    # Get current configuration
    config = config_editor_module.load_config()
    mod_path = config.get("mod_path", "")
    current_mod = config.get("last_used_mod", "")
    
    if not mod_path or not current_mod:
        messagebox.showerror("Error", "No mod path or current mod configured")
        return
        
    mod_dir = os.path.join(mod_path, current_mod)
    if not os.path.isdir(mod_dir):
        messagebox.showerror("Error", f"Mod folder not found: {mod_dir}")
        return
        
    zip_filename = f"{current_mod}.zip"
    try:
        with zipfile.ZipFile(zip_filename, "w", zipfile.ZIP_DEFLATED) as zipf:
            for root_dir, dirs, files in os.walk(mod_dir):
                for file in files:
                    file_path = os.path.join(root_dir, file)
                    arcname = os.path.relpath(file_path, mod_path)
                    zipf.write(file_path, arcname)
        messagebox.showinfo("Package Mod", f"Mod packaged as {zip_filename}")
    except Exception as e:
        messagebox.showerror("Package Mod", f"Error packaging mod: {e}")


def preview_mod_info():
    # Get current configuration
    config = config_editor_module.load_config()
    mod_path = config.get("mod_path", "")
    current_mod = config.get("last_used_mod", "")
    
    if not mod_path or not current_mod:
        messagebox.showerror("Error", "No mod path or current mod configured")
        return
        
    mod_file = os.path.join(mod_path, current_mod, "mod.xml")
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
    
    # Get current configuration
    config = config_editor_module.load_config()
    mod_path = os.path.normpath(config.get("mod_path", ""))
    current_mod = config.get("last_used_mod", "")
    
    if not mod_path or not current_mod:
        label = ttk.Label(frame, text="Please configure mod path and select a mod first")
        label.pack(padx=5, pady=5)
        return frame
        
    mod_dir = os.path.normpath(os.path.join(mod_path, current_mod))
    
    # Find all XML files in the mod directory recursively
    xml_files = []
    if os.path.exists(mod_dir):
        for root, dirs, files in os.walk(mod_dir):
            for file in files:
                if file.endswith('.xml'):
                    full_path = os.path.normpath(os.path.join(root, file))
                    xml_files.append(full_path)
    
    # Sort files for consistent display
    xml_files.sort()
    
    if not xml_files:
        label = ttk.Label(frame, text="No XML files found in the current mod")
        label.pack(padx=5, pady=5)
        return frame
    
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


def load_plugins(notebook, force_reload=False):
    """Load all plugin modules from the modules directory"""
    plugins_dir = os.path.join(os.path.dirname(__file__), "modules")
    if not os.path.isdir(plugins_dir):
        messagebox.showerror("Error", "Modules directory not found")
        return {}
        
    # Add modules directory to Python path if not already there
    if plugins_dir not in sys.path:
        sys.path.insert(0, os.path.dirname(__file__))
        
    # Keep track of loaded modules and their widgets
    loaded_modules = {}
    
    # First, remove any existing tabs except configuration
    for tab_id in notebook.tabs():
        tab_text = notebook.tab(tab_id, "text")
        if tab_text != config_editor_module.PLUGIN_TITLE:
            notebook.forget(tab_id)
    
    # Load all non-config modules first
    for filename in os.listdir(plugins_dir):
        if filename.endswith("_module.py") and filename != "config_editor_module.py":
            try:
                module_name = filename[:-3]
                
                # Import or reload module
                if module_name in sys.modules and force_reload:
                    module = importlib.reload(sys.modules[module_name])
                else:
                    module = importlib.import_module(f"modules.{module_name}")
                    sys.modules[module_name] = module
                
                # Create tab if module has the required interface
                if hasattr(module, "get_plugin_tab"):
                    title, widget = module.get_plugin_tab(notebook)
                    notebook.add(widget, text=title)
                    loaded_modules[module_name] = widget
                    
            except Exception as e:
                print(f"Failed to load plugin {filename}: {e}")
                import traceback
                traceback.print_exc()
    
    # Load or reload config module last
    try:
        if force_reload and "config_editor_module" in sys.modules:
            importlib.reload(sys.modules["config_editor_module"])
        
        # Remove existing config tab if it exists
        for tab_id in notebook.tabs():
            tab_text = notebook.tab(tab_id, "text")
            if tab_text == config_editor_module.PLUGIN_TITLE:
                notebook.forget(tab_id)
                break
        
        # Add new config tab
        title, widget = config_editor_module.get_plugin_tab(notebook)
        notebook.add(widget, text=title)
        loaded_modules["config_editor_module"] = widget
        
        # Move config tab to the end
        tabs = list(notebook.tabs())
        if len(tabs) > 1:
            notebook.insert(tabs[-1], tabs[0])
            
    except Exception as e:
        print(f"Failed to load configuration module: {e}")
        import traceback
        traceback.print_exc()
                
    return loaded_modules


def reload_plugins(notebook):
    """Reload all plugin modules"""
    return load_plugins(notebook, force_reload=True)


def main():
    root = tk.Tk()
    
    # Load initial configuration
    config = config_editor_module.load_config()
    root.title(f"Door Kickers 2 Mod Tools - {config.get('last_used_mod', '')}")

    # Create Notebook
    notebook = ttk.Notebook(root)
    notebook.pack(fill="both", expand=True)

    # Load dynamic plugins from modules folder
    loaded_modules = load_plugins(notebook)

    # Handle configuration changes
    def on_config_change(event):
        config = config_editor_module.load_config()
        root.title(f"Door Kickers 2 Mod Tools - {config.get('last_used_mod', '')}")
        # Reload plugins to reflect new configuration
        load_plugins(notebook, force_reload=True)

    root.bind_all("<<ConfigurationChanged>>", on_config_change)

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