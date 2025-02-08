import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import xml.etree.ElementTree as ET
import zipfile
from modules.units_editor_module import UnitsEditor
import importlib.util
import sys
import json
import logging
from utils import load_file, save_file, load_mod_info, load_xml, validate_xml
from modules import config_editor_module
from modules.mod_files import mod_files
import datetime
import ctypes
import tempfile

# Global variables
PROGRAM_DIR = None
DATA_DIR = None
CONFIG_FILE = None
log_file = None
logger = None

def setup_logging():
    """Set up logging with proper paths"""
    global log_file, logger
    
    # Set up logging
    if os.path.exists(log_file):
        try:
            os.remove(log_file)
        except:
            pass

    logging.basicConfig(
        filename=log_file,
        filemode='w',  # Write mode - overwrites the file
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Also log to console
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    logging.getLogger().addHandler(console_handler)

    logger = logging.getLogger(__name__)
    logger.info("Starting Door Kickers 2 Modding Tool")
    logger.info(f"Program directory: {PROGRAM_DIR}")
    logger.info(f"Data directory: {DATA_DIR}")
    logger.info(f"Log file location: {log_file}")

def initialize_program():
    """Initialize program directories and logging"""
    global PROGRAM_DIR, DATA_DIR, CONFIG_FILE, log_file, logger
    
    print("\nInitializing program...")
    
    try:
        # Get program directories first
        PROGRAM_DIR, DATA_DIR = get_program_dirs()
        
        # Ensure data directory exists
        os.makedirs(DATA_DIR, exist_ok=True)
        print(f"Ensured data directory exists: {DATA_DIR}")
        
        # Set up file paths
        CONFIG_FILE = os.path.join(DATA_DIR, "config.json")
        log_file = os.path.join(DATA_DIR, "modding_tool.log")
        
        # Create initial files if they don't exist
        if not os.path.exists(CONFIG_FILE) or not os.path.exists(log_file):
            print("Creating initial files...")
            create_initial_files(DATA_DIR)
        
        # Now that files exist, set up logging
        setup_logging()
        
        # Initialize configuration
        config = initialize_config()
        
        print("Program initialization complete!")
        return config
        
    except Exception as e:
        print(f"Failed to initialize program: {str(e)}")
        if not os.path.exists(DATA_DIR):
            print(f"Data directory does not exist: {DATA_DIR}")
        if not os.path.exists(CONFIG_FILE):
            print(f"Config file does not exist: {CONFIG_FILE}")
        if not os.path.exists(log_file):
            print(f"Log file does not exist: {log_file}")
        raise

def is_admin():
    """Check if the program has admin privileges"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def request_admin():
    """Request admin privileges by relaunching the program"""
    try:
        if not is_admin():
            print("Requesting admin privileges...")
            # Re-run the program with admin rights
            ctypes.windll.shell32.ShellExecuteW(
                None, "runas", sys.executable, " ".join(sys.argv), None, 1
            )
            sys.exit()
        return True
    except Exception as e:
        print(f"Failed to get admin privileges: {str(e)}")
        return False

def ensure_directory_writable(directory):
    """Ensure a directory exists and is writable"""
    try:
        # First try to create/verify the directory
        os.makedirs(directory, exist_ok=True)
        
        # Try to create a test file
        test_file = os.path.join(directory, 'test_write.tmp')
        try:
            with open(test_file, 'w') as f:
                f.write('test')
            os.remove(test_file)
            print(f"Successfully verified write access to: {directory}")
            return True
        except (OSError, PermissionError) as e:
            print(f"Cannot write to directory {directory}: {str(e)}")
            return False
    except Exception as e:
        print(f"Failed to verify directory permissions: {str(e)}")
        return False

def get_writable_directory(primary_path, fallback_path=None):
    """Get a writable directory, trying primary path first then fallback"""
    # First try user's Documents folder as it's usually accessible
    documents_dir = os.path.join(os.path.expanduser("~"), "Documents", "DK2ModdingTool")
    if ensure_directory_writable(documents_dir):
        return documents_dir
        
    # Then try AppData Local
    appdata_dir = os.path.join(os.getenv('LOCALAPPDATA'), 'DK2ModdingTool')
    if ensure_directory_writable(appdata_dir):
        return appdata_dir
        
    # Finally try temp directory as last resort
    temp_dir = os.path.join(tempfile.gettempdir(), 'DK2ModdingTool')
    if ensure_directory_writable(temp_dir):
        return temp_dir
        
    raise PermissionError(f"Cannot find writable directory. Tried: Documents, AppData, and Temp directories")

def create_initial_files(data_dir):
    """Create initial files in the data directory during installation"""
    print(f"\nCreating initial files in: {data_dir}")
    
    # First ensure the directory exists and is writable
    if not ensure_directory_writable(data_dir):
        print(f"Cannot write to directory: {data_dir}")
        # Try Documents folder
        data_dir = os.path.join(os.path.expanduser("~"), "Documents", "DK2ModdingTool")
        if not ensure_directory_writable(data_dir):
            raise PermissionError(f"Cannot find writable directory")
    
    # Create initial config file
    config_file = os.path.join(data_dir, "config.json")
    print(f"Creating config file at: {config_file}")
    initial_config = {
        "mod_path": "",
        "game_path": "",
        "last_used_mod": "",
        "created_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    try:
        # Write config file
        with open(config_file, 'w') as f:
            json.dump(initial_config, f, indent=4)
        print("Successfully created config file")
        
        # Create log file
        log_file = os.path.join(data_dir, "modding_tool.log")
        print(f"Creating log file at: {log_file}")
        with open(log_file, 'w') as f:
            f.write("# Door Kickers 2 Modding Tool Log\n")
            f.write(f"# Created: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("# This file will be overwritten each time the program starts\n\n")
        print("Successfully created log file")
        
        # Verify files were created and are writable
        if not os.path.exists(config_file) or not os.path.exists(log_file):
            raise FileNotFoundError("Files were not created successfully")
            
        # Test write access
        with open(config_file, 'a') as f:
            pass
        with open(log_file, 'a') as f:
            pass
            
        print("Successfully verified file access!")
        return True
        
    except Exception as e:
        print(f"Failed to create files: {str(e)}")
        raise

def get_program_dirs():
    """Get or create program directories"""
    print("\nSetting up program directories...")
    
    # Initialize Tkinter root for dialogs
    root = tk.Tk()
    root.withdraw()  # Hide the root window
    
    # First, check if we're already in Program Files
    exe_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
    program_dir = exe_dir
    print(f"Using program directory: {program_dir}")
    
    # Use the same directory for data files
    data_dir = program_dir
    print(f"Using same directory for data files: {data_dir}")
    
    # Create/verify files
    try:
        # Create/verify files
        if not os.path.exists(data_dir):
            print("Data directory doesn't exist, creating it...")
            create_initial_files(data_dir)
        else:
            print("Data directory exists, verifying files...")
            config_file = os.path.join(data_dir, "config.json")
            log_file = os.path.join(data_dir, "modding_tool.log")
            
            if not os.path.exists(config_file) or not os.path.exists(log_file):
                print("Some files are missing, recreating them...")
                create_initial_files(data_dir)
            else:
                # Verify files are writable
                if not ensure_directory_writable(data_dir):
                    print("Files exist but are not writable, recreating them...")
                    create_initial_files(data_dir)
                else:
                    print("All required files exist and are writable")
                    
    except Exception as e:
        print(f"Failed to set up data directory: {str(e)}")
        messagebox.showerror(
            "Error",
            "Cannot create or access data files. Please ensure you have write permissions."
        )
        root.destroy()
        sys.exit(1)
    
    root.destroy()  # Clean up the temporary root window
    print(f"\nSetup complete!\nUsing directory: {program_dir}")
    return program_dir, data_dir

DEFAULT_DK2_PATH = r"C:\Program Files (x86)\Steam\steamapps\common\DoorKickers2"

def initialize_config():
    """Initialize configuration file if it doesn't exist"""
    try:
        print(f"Initializing config from: {CONFIG_FILE}")
        logger.info("Starting configuration initialization")
        
        if os.path.exists(CONFIG_FILE):
            logger.info("Loading existing config file...")
            try:
                with open(CONFIG_FILE, 'r') as f:
                    config = json.load(f)
                    # Validate paths in the loaded config
                    if config.get("mod_path"):
                        config["mod_path"] = os.path.normpath(config["mod_path"])
                        if not os.path.exists(config["mod_path"]):
                            logger.warning(f"Configured mod path does not exist: {config['mod_path']}")
                            messagebox.showwarning(
                                "Missing Mod Directory",
                                f"The configured mods directory was not found:\n{config['mod_path']}\n\n"
                                "Please select the correct mods directory in the Configuration tab."
                            )
                            config["mod_path"] = ""
                        else:
                            logger.info(f"Verified mod_path: {config['mod_path']}")
                            
                    if config.get("game_path"):
                        config["game_path"] = os.path.normpath(config["game_path"])
                        if not os.path.exists(config["game_path"]):
                            logger.warning(f"Configured game path does not exist: {config['game_path']}")
                            messagebox.showwarning(
                                "Missing Game Directory",
                                f"The configured Door Kickers 2 directory was not found:\n{config['game_path']}\n\n"
                                "Please select the correct game directory in the Configuration tab."
                            )
                            config["game_path"] = ""
                        else:
                            logger.info(f"Verified game_path: {config['game_path']}")
                    return config
            except Exception as e:
                logger.error(f"Failed to read config file: {str(e)}")
                raise
                
        logger.info("No config file found, creating new one...")
        config = {
            "mod_path": "",
            "game_path": "",
            "last_used_mod": ""
        }
        
        # List of possible Steam installation drives
        steam_paths = []
        
        # Add all possible drive letters
        import string
        for drive in string.ascii_uppercase:
            drive_path = f"{drive}:\\"
            if os.path.exists(drive_path):
                # Common Steam installation paths for each drive
                steam_paths.extend([
                    os.path.join(drive_path, "Program Files (x86)", "Steam"),
                    os.path.join(drive_path, "Program Files", "Steam"),
                    os.path.join(drive_path, "Steam"),
                    os.path.join(drive_path, "Games", "Steam")
                ])
        
        # Add user-specific paths
        steam_paths.extend([
            os.path.expanduser("~/Steam"),
            os.path.expanduser("~/Games/Steam"),
            os.path.expanduser("~/SteamLibrary")
        ])
        
        logger.info("Searching for DK2 installation...")
        found = False
        
        # First check default location
        if os.path.exists(DEFAULT_DK2_PATH):
            logger.info("Found DK2 installation at default path")
            config["game_path"] = os.path.normpath(DEFAULT_DK2_PATH)
            mods_path = os.path.join(DEFAULT_DK2_PATH, "mods")
            if os.path.exists(mods_path):
                logger.info("Found mods directory")
                config["mod_path"] = os.path.normpath(mods_path)
                found = True
            else:
                logger.warning(f"Mods directory not found at: {mods_path}")
                messagebox.showwarning(
                    "Missing Mods Directory",
                    f"The mods directory was not found at:\n{mods_path}\n\n"
                    "Please create a 'mods' folder in your Door Kickers 2 directory."
                )
        
        # If not found in default location, search other locations
        if not found:
            logger.info("DK2 not found in default location, searching other paths...")
            for steam_path in steam_paths:
                # Check both standard and library paths
                possible_paths = [
                    os.path.join(steam_path, "steamapps", "common", "DoorKickers2"),
                    os.path.join(steam_path, "SteamApps", "common", "DoorKickers2")
                ]
                
                for dk2_path in possible_paths:
                    if os.path.exists(dk2_path):
                        logger.info(f"Found DK2 installation at: {dk2_path}")
                        config["game_path"] = os.path.normpath(dk2_path)
                        mods_path = os.path.join(dk2_path, "mods")
                        if os.path.exists(mods_path):
                            logger.info("Found mods directory")
                            config["mod_path"] = os.path.normpath(mods_path)
                            found = True
                        else:
                            logger.warning(f"Mods directory not found at: {mods_path}")
                            messagebox.showwarning(
                                "Missing Mods Directory",
                                f"The mods directory was not found at:\n{mods_path}\n\n"
                                "Please create a 'mods' folder in your Door Kickers 2 directory."
                            )
                        break
                
                if found:
                    break
        
        if not found:
            logger.warning("Could not automatically detect DK2 installation")
            messagebox.showwarning(
                "Game Not Found",
                "Door Kickers 2 installation could not be automatically detected.\n\n"
                "Please use the Configuration tab to manually set your game directory."
            )
        
        # Save the config - only create the directory for the config file itself
        logger.info("Saving configuration file...")
        try:
            config_dir = os.path.dirname(CONFIG_FILE)
            if not os.path.exists(config_dir):
                logger.warning(f"Config directory does not exist: {config_dir}")
                messagebox.showerror(
                    "Configuration Error",
                    f"Cannot save configuration. Directory does not exist:\n{config_dir}\n\n"
                    "Please run the tool from a directory where you have write permissions."
                )
                return config
            
            # Try to write config
            with open(CONFIG_FILE, 'w') as f:
                json.dump(config, f, indent=4)
            logger.info("Successfully saved config file")
        except Exception as e:
            logger.error(f"Failed to save config file: {str(e)}")
            messagebox.showerror(
                "Configuration Error",
                f"Failed to save configuration file:\n{str(e)}\n\n"
                "Please ensure you have write permissions in the tool's directory."
            )
            
        return config
    except Exception as e:
        logger.error(f"Error in initialize_config: {e}", exc_info=True)
        # Return a default config as fallback
        return {
            "mod_path": "",
            "game_path": "",
            "last_used_mod": ""
        }

def get_unit_file(mod_path):
    """Get the unit XML file for a mod."""
    global mod_files
    mod_path = os.path.normpath(mod_path)
    if mod_files.mod_path != mod_path:
        mod_files.mod_path = mod_path
        mod_files.scan_mod_directory()
    return mod_files.get_unit_file()

def get_equipment_file(mod_path):
    """Get the equipment binds XML file for a mod."""
    global mod_files
    mod_path = os.path.normpath(mod_path)
    # Only scan if the path has changed
    if mod_files.mod_path != mod_path:
        mod_files.mod_path = mod_path
        mod_files.scan_mod_directory()
    return mod_files.get_equipment_file()

def get_entities_file(mod_path):
    """Get the entities XML file for a mod."""
    global mod_files
    mod_path = os.path.normpath(mod_path)
    # Only scan if the path has changed
    if mod_files.mod_path != mod_path:
        mod_files.mod_path = mod_path
        mod_files.scan_mod_directory()
    return mod_files.get_entities_file()

def get_gui_file(mod_path):
    """Get the GUI XML file for a mod."""
    global mod_files
    mod_path = os.path.normpath(mod_path)
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
    
    # First, remove any existing tabs
    for tab_id in notebook.tabs():
        notebook.forget(tab_id)
    
    # Load config module first
    try:
        if force_reload and "config_editor_module" in sys.modules:
            importlib.reload(sys.modules["config_editor_module"])
        
        # Add config tab first
        title, widget = config_editor_module.get_plugin_tab(notebook)
        notebook.add(widget, text=title)
        loaded_modules["config_editor_module"] = widget
        
    except Exception as e:
        print(f"Failed to load configuration module: {e}")
        import traceback
        traceback.print_exc()
    
    # Then load all non-config modules
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
                
    # Select the configuration tab
    if notebook.tabs():
        notebook.select(0)
                
    return loaded_modules


def reload_plugins(notebook):
    """Reload all plugin modules"""
    return load_plugins(notebook, force_reload=True)


def main():
    try:
        # Initialize everything first
        config = initialize_program()
        
        # Only import modules after initialization is complete
        import importlib.util
        import sys
        from utils import load_file, save_file, load_mod_info, load_xml, validate_xml
        from modules import config_editor_module
        from modules.mod_files import mod_files
        
        root = tk.Tk()
        
        # Load initial configuration
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
        
    except Exception as e:
        print(f"\nFatal error during startup: {str(e)}")
        import traceback
        traceback.print_exc()
        input("\nPress Enter to exit...")
        sys.exit(1)


if __name__ == "__main__":
    main() 