# IGNORE THIS - TEST MESSAGE TO VERIFY BUILD
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import json
import glob

PLUGIN_TITLE = "Configuration"
CONFIG_FILE = "modding_tool_config.json"

# Default Steam paths
DEFAULT_DK2_PATH = r"C:\Program Files (x86)\Steam\steamapps\common\DoorKickers2"
DEFAULT_MODS_PATH = os.path.join(DEFAULT_DK2_PATH, "mods")

# Mod structure definition with specific file patterns
MOD_STRUCTURE = {
    "required_files": [
        "mod.xml"  # Only mod.xml is truly required
    ],
    "optional_files": [
        "mod_image.jpg"
    ],
    "optional_dirs": {  # All directories are now optional
        "gui": [
            "*_deploy.xml",      # Deploy screen layouts
            "*_gui.xml",         # General GUI layouts
            "*.xml"              # Fallback for other GUI files
        ],
        "units": [
            "*_unit.xml",        # Unit definitions
            "*_identities.xml",  # Unit identities
            "*.xml"              # Fallback for other unit files
        ],
        "entities": [
            "*_humans.xml",      # Human entity definitions
            "*_entities.xml",    # Other entity definitions
            "*.xml"              # Fallback for other entity files
        ],
        "equipment": [
            "*_binds.xml",       # Equipment bindings
            "*_equipment.xml",   # Equipment definitions
            "*.xml"              # Fallback for other equipment files
        ],
        "textures": [
            "*_squad_bg.dds",    # Squad backgrounds
            "*.dds",             # Other textures
            "*.jpg",
            "*.png"
        ],
        "localization": [
            "*_squadname_pool.txt",  # Squad name pools
            "*_strings.xml",         # String tables
            "*.txt",                 # Other text files
            "*.xml"                  # Other XML files
        ]
    }
}

DEFAULT_CONFIG = {
    "mod_path": "",  # Empty by default
    "game_path": "", # Empty by default
    "last_used_mod": ""
}

def find_first_matching_file(directory, patterns):
    """Find the first file matching any of the given patterns in priority order"""
    for pattern in patterns:  # Patterns are in priority order
        matches = glob.glob(os.path.join(directory, pattern))
        if matches:
            # Sort to ensure consistent selection
            matches.sort()
            return os.path.basename(matches[0])
    return None

def get_directory_files(directory, patterns):
    """Get all files in a directory matching the patterns"""
    files = []
    for pattern in patterns:
        files.extend(glob.glob(os.path.join(directory, pattern)))
    return [os.path.basename(f) for f in files]

def is_valid_mod_directory(mod_dir):
    """Check if a directory contains a valid mod structure"""
    if not os.path.isdir(mod_dir):
        return False, "Not a directory"
    
    # Only check for mod.xml - everything else is optional
    if not os.path.exists(os.path.join(mod_dir, "mod.xml")):
        # Special case: if it's a localization folder, it's valid without mod.xml
        if os.path.basename(mod_dir).startswith("localization_"):
            return True, {"type": "localization"}
        # Special case: if it's the os_steam_deck folder, it's valid
        if os.path.basename(mod_dir) == "os_steam_deck":
            return True, {"type": "steam_deck"}
        return False, "Missing mod.xml"
    
    found_files = {"type": "mod"}
    
    # Check all optional directories
    for dir_name, patterns in MOD_STRUCTURE["optional_dirs"].items():
        dir_path = os.path.join(mod_dir, dir_name)
        if os.path.isdir(dir_path):
            files = get_directory_files(dir_path, patterns)
            if files:
                found_files[dir_name] = files[0]  # Store the first matching file
    
    return True, found_files

def get_mod_info(mod_dir):
    """Get basic information about a mod"""
    is_valid, result = is_valid_mod_directory(mod_dir)
    info = {
        "name": os.path.basename(mod_dir),
        "has_image": os.path.exists(os.path.join(mod_dir, "mod_image.jpg")),
        "is_valid": is_valid,
        "type": result.get("type", "unknown") if isinstance(result, dict) else "unknown"
    }
    
    if is_valid and isinstance(result, dict):
        info["files"] = result
    else:
        info["error"] = result
        
    return info

def load_config():
    """Load configuration from file or create default if not exists"""
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r') as f:
                config = json.load(f)
                # Ensure all default keys exist
                for key, value in DEFAULT_CONFIG.items():
                    if key not in config:
                        config[key] = value
                return config
    except Exception as e:
        print(f"Error loading config: {e}")
    return DEFAULT_CONFIG.copy()

def save_config(config):
    """Save configuration to file"""
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=4)
        return True
    except Exception as e:
        print(f"Error saving config: {e}")
        return False

class ConfigEditor(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.config = load_config()
        self.build_ui()
        # Show first-time setup dialog if no config exists
        if not os.path.exists(CONFIG_FILE):
            self.show_first_time_setup()

    def show_first_time_setup(self):
        """Show welcome message and guide first-time setup"""
        response = messagebox.askquestion(
            "Welcome to DK2 Modding Tool",
            "Welcome to the Door Kickers 2 Modding Tool!\n\n"
            "Would you like to automatically detect your DK2 installation?",
            icon='question'
        )
        if response == 'yes':
            self.auto_detect_paths()
        else:
            messagebox.showinfo(
                "Manual Setup",
                "You can set up your paths manually:\n\n"
                "1. Set your Game Directory to your DK2 installation\n"
                "2. Set your Mod Directory to your DK2 mods folder\n"
                "3. Click 'Save Changes' when done\n\n"
                "You can also use the 'Auto-Detect Paths' button later."
            )

    def build_ui(self):
        # Create main frame
        main_frame = ttk.LabelFrame(self, text="Configuration Settings", padding="10")
        main_frame.pack(fill="both", expand=True, padx=10, pady=5)

        # Mod Directory
        ttk.Label(main_frame, text="Mod Directory:").grid(row=0, column=0, sticky="w", pady=5)
        self.mod_path_var = tk.StringVar(value=self.config.get("mod_path", ""))
        mod_path_entry = ttk.Entry(main_frame, textvariable=self.mod_path_var, width=50)
        mod_path_entry.grid(row=0, column=1, padx=5)
        ttk.Button(main_frame, text="Browse", 
                  command=lambda: self.browse_directory("mod_path")).grid(row=0, column=2)

        # Game Directory
        ttk.Label(main_frame, text="Game Directory:").grid(row=1, column=0, sticky="w", pady=5)
        self.game_path_var = tk.StringVar(value=self.config.get("game_path", ""))
        game_path_entry = ttk.Entry(main_frame, textvariable=self.game_path_var, width=50)
        game_path_entry.grid(row=1, column=1, padx=5)
        ttk.Button(main_frame, text="Browse", 
                  command=lambda: self.browse_directory("game_path")).grid(row=1, column=2)

        # Auto-detect button
        ttk.Button(main_frame, text="Auto-Detect Paths", 
                  command=self.auto_detect_paths).grid(row=2, column=0, columnspan=3, pady=10)

        # Last Used Mod
        ttk.Label(main_frame, text="Current Mod:").grid(row=3, column=0, sticky="w", pady=5)
        self.current_mod_var = tk.StringVar(value=self.config.get("last_used_mod", ""))
        self.mod_combo = ttk.Combobox(main_frame, textvariable=self.current_mod_var, width=47)
        self.mod_combo.grid(row=3, column=1, padx=5)
        self.update_mod_list()

        # Validation Status
        self.status_label = ttk.Label(main_frame, text="", foreground="green")
        self.status_label.grid(row=4, column=0, columnspan=3, pady=10)

        # Save Button
        save_frame = ttk.Frame(main_frame)
        save_frame.grid(row=5, column=0, columnspan=3, pady=10)
        ttk.Button(save_frame, text="Save Changes", 
                  command=self.save_changes).pack(side="right", padx=5)
        ttk.Button(save_frame, text="Validate Paths", 
                  command=self.validate_paths).pack(side="right", padx=5)

        # Bind path changes to validation
        self.mod_path_var.trace_add("write", lambda *args: self.on_path_change())
        self.game_path_var.trace_add("write", lambda *args: self.on_path_change())
        
        # Initial validation
        self.validate_paths()

    def browse_directory(self, path_type):
        """Open directory browser and update path"""
        current_path = self.mod_path_var.get() if path_type == "mod_path" else self.game_path_var.get()
        directory = filedialog.askdirectory(initialdir=current_path if current_path else "/")
        if directory:
            if path_type == "mod_path":
                self.mod_path_var.set(directory)
                self.update_mod_list()
            else:
                self.game_path_var.set(directory)

    def update_mod_list(self):
        """Update the list of available mods in the selected mod directory"""
        mod_path = self.mod_path_var.get()
        mods = []
        special_mods = []  # For localization and steam deck mods
        
        if os.path.exists(mod_path):
            for item in os.listdir(mod_path):
                item_path = os.path.join(mod_path, item)
                if os.path.isdir(item_path):
                    is_valid, result = is_valid_mod_directory(item_path)
                    if is_valid:
                        if isinstance(result, dict) and result.get("type") in ["localization", "steam_deck"]:
                            special_mods.append(item)
                        else:
                            mods.append(item)
        
        # Update combobox with regular mods first, then special mods
        self.mod_combo['values'] = mods + special_mods
        
        if not mods and not special_mods:
            self.current_mod_var.set("")
        elif self.current_mod_var.get() not in (mods + special_mods):
            self.current_mod_var.set(mods[0] if mods else special_mods[0] if special_mods else "")

    def validate_paths(self):
        """Validate the configured paths"""
        mod_path = self.mod_path_var.get()
        game_path = self.game_path_var.get()
        
        errors = []
        warnings = []
        
        # Validate game directory
        if not os.path.exists(game_path):
            errors.append("Game directory does not exist")
        elif not os.path.exists(os.path.join(game_path, "data")):
            errors.append("Invalid game directory (no 'data' folder found)")
        
        # Validate mods directory
        if not os.path.exists(mod_path):
            errors.append("Mod directory does not exist")
        else:
            # Check for valid mods
            valid_mods = []
            invalid_mods = []
            for item in os.listdir(mod_path):
                item_path = os.path.join(mod_path, item)
                if os.path.isdir(item_path):
                    is_valid, reason = is_valid_mod_directory(item_path)
                    if is_valid:
                        valid_mods.append(item)
                    else:
                        invalid_mods.append(item)
            
            if not valid_mods:
                warnings.append(f"No valid mods found in directory")
            if invalid_mods:
                warnings.append(f"Found {len(invalid_mods)} invalid mod(s)")
            
        if errors:
            self.status_label.config(
                text="❌ " + " | ".join(errors),
                foreground="red"
            )
            return False
        elif warnings:
            self.status_label.config(
                text="⚠️ " + " | ".join(warnings),
                foreground="orange"
            )
            return True
        else:
            self.status_label.config(
                text="✓ All paths are valid",
                foreground="green"
            )
            return True

    def on_path_change(self):
        """Handler for path changes"""
        self.validate_paths()

    def save_changes(self):
        """Save configuration changes"""
        if not self.validate_paths():
            if not messagebox.askyesno("Warning", 
                "Some paths are invalid. Do you want to save anyway?"):
                return

        self.config.update({
            "mod_path": self.mod_path_var.get(),
            "game_path": self.game_path_var.get(),
            "last_used_mod": self.current_mod_var.get()
        })
        
        if save_config(self.config):
            messagebox.showinfo("Success", "Configuration saved successfully")
            # Generate an event to notify other modules
            self.event_generate("<<ConfigurationChanged>>")
        else:
            messagebox.showerror("Error", "Failed to save configuration")

    def auto_detect_paths(self):
        """Auto-detect DK2 and mods directory"""
        # Check default Steam path first
        if os.path.exists(DEFAULT_DK2_PATH):
            self.game_path_var.set(DEFAULT_DK2_PATH)
            if os.path.exists(DEFAULT_MODS_PATH):
                self.mod_path_var.set(DEFAULT_MODS_PATH)
                messagebox.showinfo("Success", "Found Door Kickers 2 installation and mods directory!")
                self.update_mod_list()
                return

        # Try to find Steam directory in other common locations
        steam_paths = [
            r"C:\Program Files\Steam",
            r"D:\Steam",
            r"E:\Steam",
            os.path.expanduser("~/Steam"),
            os.path.expanduser("~/Games/Steam")
        ]

        for steam_path in steam_paths:
            dk2_path = os.path.join(steam_path, "steamapps", "common", "DoorKickers2")
            if os.path.exists(dk2_path):
                self.game_path_var.set(dk2_path)
                mods_path = os.path.join(dk2_path, "mods")
                if os.path.exists(mods_path):
                    self.mod_path_var.set(mods_path)
                    messagebox.showinfo("Success", "Found Door Kickers 2 installation and mods directory!")
                    self.update_mod_list()
                    return

        # If not found, ask user if they want to browse manually
        if messagebox.askyesno("Not Found", 
                             "Could not automatically detect Door Kickers 2 installation.\n\n"
                             "Would you like to browse for it manually?"):
            self.browse_directory("game_path")

def get_plugin_tab(notebook):
    """Create and return the configuration editor tab"""
    return PLUGIN_TITLE, ConfigEditor(notebook) 