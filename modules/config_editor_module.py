# IGNORE THIS - TEST MESSAGE TO VERIFY BUILD
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import json
import glob
import shutil
import xml.etree.ElementTree as ET
from datetime import datetime

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
    """Check if a directory is a mod directory"""
    if not os.path.isdir(mod_dir):
        return False, "Not a directory"
    
    # All directories are considered valid mods
    found_files = {"type": "mod"}
    
    # Still scan for files to help with file management
    for dir_name, patterns in MOD_STRUCTURE["optional_dirs"].items():
        dir_path = os.path.join(mod_dir, dir_name)
        if os.path.isdir(dir_path):
            files = get_directory_files(dir_path, patterns)
            if files:
                found_files[dir_name] = files[0]  # Store the first matching file
    
    return True, found_files

def get_mod_info(mod_dir):
    """Get basic information about a mod"""
    info = {
        "name": os.path.basename(mod_dir),
        "has_image": os.path.exists(os.path.join(mod_dir, "mod_image.jpg")),
        "is_valid": True,  # All directories are valid
        "type": "mod"
    }
    
    # Still scan for files to help with file management
    is_valid, result = is_valid_mod_directory(mod_dir)
    if isinstance(result, dict):
        info["files"] = result
        
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

def sanitize_mod_name(mod_name):
    """Sanitize mod name to be filesystem safe"""
    # Replace spaces with underscores and remove invalid characters
    import re
    # Remove or replace invalid characters
    safe_name = re.sub(r'[<>:"/\\|?*]', '', mod_name)
    # Replace spaces with underscores
    safe_name = safe_name.replace(' ', '_')
    # Remove any non-ASCII characters
    safe_name = ''.join(c for c in safe_name if ord(c) < 128)
    return safe_name

def create_mod_template(mod_path, mod_name, author="", description=""):
    """Create a new mod template with basic structure based on Baby Seals template"""
    try:
        # Sanitize mod name
        safe_mod_name = sanitize_mod_name(mod_name)
        if not safe_mod_name:
            return False, "Invalid mod name. Please use only letters, numbers, and basic punctuation."
            
        # Create full mod path
        full_mod_path = os.path.join(mod_path, safe_mod_name)
        if os.path.exists(full_mod_path):
            return False, f"The mod directory '{safe_mod_name}' already exists. Please choose a different name or delete the existing directory first."

        # Create main mod directory
        os.makedirs(full_mod_path)

        # Create subdirectories
        for dir_name in MOD_STRUCTURE["optional_dirs"].keys():
            os.makedirs(os.path.join(full_mod_path, dir_name))

        # Create mod.xml
        mod_xml_content = f"""<?xml version="1.0" encoding="utf-8"?>
<mod>
    <name>{mod_name}</name>
    <author>{author}</author>
    <description>{description}</description>
    <version>1.0</version>
    <game_version>1.0</game_version>
</mod>"""
        
        with open(os.path.join(full_mod_path, "mod.xml"), 'w', encoding='utf-8') as f:
            f.write(mod_xml_content)

        # Create template files for each directory
        templates = {
            "units": {
                "mod_unit.xml": """<?xml version="1.0" encoding="utf-8"?>
<Units>
    <Unit name="MOD_UNIT" nameUI="Mod Unit" description="Description of your unit" flagTex="data/textures/mod_squad_bg.dds" flagColor="f0f0f0" rndNameEntry="@#squadname" voicepack="commander_eng" incapacitationChance="80" incapacitationChanceCrit="25">
        <Classes>
            <Class name="DefaultClass" nameUI="DEFAULT CLASS" description="Default class description" supply="100" iconTex="data/textures/gui/deploy/class_icon_undercover.dds" upgrades="BH_Defence1, BH_Offence1" maxUpgradeable="2" numSlots="4" />
        </Classes>
        <TrooperRanks>
            <Rank name="@agent_rank_0" xpNeeded="0" badgeTex="data/textures/gui/customization/cia_rank_01.dds" />
            <Rank name="@agent_rank_1" xpNeeded="700" badgeTex="data/textures/gui/customization/cia_rank_02.dds" />
        </TrooperRanks>
        <Ranks>
            <Rank xpNeeded="0" badgeTex="" />
            <Rank xpNeeded="4000" badgeTex="" />
        </Ranks>
    </Unit>
</Units>""",
                "mod_identities.xml": """<?xml version="1.0" encoding="utf-8"?>
<identities>
    <!-- Add your unit identities here -->
</identities>"""
            },
            "equipment": {
                "mod_equipment.xml": """<?xml version="1.0" encoding="utf-8"?>
<equipment>
    <!-- Add your equipment definitions here -->
</equipment>""",
                "mod_binds.xml": """<?xml version="1.0" encoding="utf-8"?>
<binds>
    <!-- Add your equipment bindings here -->
</binds>"""
            },
            "entities": {
                "mod_entities.xml": """<?xml version="1.0" encoding="utf-8"?>
<entities>
    <!-- Add your entity definitions here -->
</entities>""",
                "mod_humans.xml": """<?xml version="1.0" encoding="utf-8"?>
<humans>
    <!-- Add your human entity definitions here -->
</humans>"""
            },
            "gui": {
                "mod_gui.xml": """<?xml version="1.0" encoding="utf-8"?>
<gui>
    <!-- Add your GUI definitions here -->
</gui>""",
                "mod_deploy.xml": """<?xml version="1.0" encoding="utf-8"?>
<deploy>
    <!-- Add your deployment screen layouts here -->
</deploy>"""
            },
            "localization": {
                "mod_strings.xml": """<?xml version="1.0" encoding="utf-8"?>
<strings>
    <!-- Add your string translations here -->
</strings>""",
                "mod_squadname_pool.txt": """# Add your squad names here, one per line
Squad Alpha
Squad Bravo
Squad Charlie"""
            }
        }

        # Create all template files
        for directory, files in templates.items():
            dir_path = os.path.join(full_mod_path, directory)
            for filename, content in files.items():
                file_path = os.path.join(dir_path, filename)
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)

        return True, f"Successfully created mod template: {safe_mod_name}"

    except Exception as e:
        return False, f"Error creating mod template: {str(e)}"

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

        # Add Create New Mod section
        create_mod_frame = ttk.LabelFrame(main_frame, text="Create New Mod")
        create_mod_frame.pack(fill="x", padx=5, pady=5)
        
        # Mod name entry
        ttk.Label(create_mod_frame, text="Mod Name:").pack(anchor="w", padx=5, pady=2)
        self.mod_name_var = tk.StringVar()
        mod_name_entry = ttk.Entry(create_mod_frame, textvariable=self.mod_name_var)
        mod_name_entry.pack(fill="x", padx=5, pady=2)
        
        # Author entry
        ttk.Label(create_mod_frame, text="Author:").pack(anchor="w", padx=5, pady=2)
        self.author_var = tk.StringVar()
        author_entry = ttk.Entry(create_mod_frame, textvariable=self.author_var)
        author_entry.pack(fill="x", padx=5, pady=2)
        
        # Description entry
        ttk.Label(create_mod_frame, text="Description:").pack(anchor="w", padx=5, pady=2)
        self.desc_var = tk.StringVar()
        desc_entry = ttk.Entry(create_mod_frame, textvariable=self.desc_var)
        desc_entry.pack(fill="x", padx=5, pady=2)
        
        # Create Mod button
        ttk.Button(create_mod_frame, text="Create Mod", command=self.create_new_mod).pack(anchor="e", padx=5, pady=5)
        
        # Add separator
        ttk.Separator(main_frame, orient="horizontal").pack(fill="x", padx=5, pady=10)
        
        # Paths section
        paths_frame = ttk.Frame(main_frame)
        paths_frame.pack(fill="x", padx=5, pady=5)
        
        # Mod Directory
        mod_dir_frame = ttk.Frame(paths_frame)
        mod_dir_frame.pack(fill="x", pady=2)
        ttk.Label(mod_dir_frame, text="Mod Directory:").pack(side="left", padx=5)
        self.mod_path_var = tk.StringVar(value=self.config.get("mod_path", ""))
        mod_path_entry = ttk.Entry(mod_dir_frame, textvariable=self.mod_path_var, width=50)
        mod_path_entry.pack(side="left", fill="x", expand=True, padx=5)
        ttk.Button(mod_dir_frame, text="Browse", 
                  command=lambda: self.browse_directory("mod_path")).pack(side="left", padx=5)

        # Game Directory
        game_dir_frame = ttk.Frame(paths_frame)
        game_dir_frame.pack(fill="x", pady=2)
        ttk.Label(game_dir_frame, text="Game Directory:").pack(side="left", padx=5)
        self.game_path_var = tk.StringVar(value=self.config.get("game_path", ""))
        game_path_entry = ttk.Entry(game_dir_frame, textvariable=self.game_path_var, width=50)
        game_path_entry.pack(side="left", fill="x", expand=True, padx=5)
        ttk.Button(game_dir_frame, text="Browse", 
                  command=lambda: self.browse_directory("game_path")).pack(side="left", padx=5)

        # Auto-detect button
        ttk.Button(paths_frame, text="Auto-Detect Paths", 
                  command=self.auto_detect_paths).pack(pady=10)

        # Current Mod section
        mod_frame = ttk.Frame(main_frame)
        mod_frame.pack(fill="x", padx=5, pady=5)
        ttk.Label(mod_frame, text="Current Mod:").pack(side="left", padx=5)
        self.current_mod_var = tk.StringVar(value=self.config.get("last_used_mod", ""))
        self.mod_combo = ttk.Combobox(mod_frame, textvariable=self.current_mod_var, width=47)
        self.mod_combo.pack(side="left", fill="x", expand=True, padx=5)
        self.update_mod_list()

        # Validation Status
        self.status_label = ttk.Label(main_frame, text="", foreground="green")
        self.status_label.pack(fill="x", padx=5, pady=10)

        # Buttons frame
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill="x", padx=5, pady=5)
        ttk.Button(button_frame, text="Save Changes", 
                  command=self.save_changes).pack(side="right", padx=5)
        ttk.Button(button_frame, text="Validate Paths", 
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
        
        if os.path.exists(mod_path):
            for item in os.listdir(mod_path):
                item_path = os.path.join(mod_path, item)
                if os.path.isdir(item_path):
                    mods.append(item)
        
        # Update combobox with all mods
        self.mod_combo['values'] = sorted(mods)
        
        if not mods:
            self.current_mod_var.set("")
        elif self.current_mod_var.get() not in mods:
            self.current_mod_var.set(mods[0] if mods else "")

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

    def create_new_mod(self):
        mod_name = self.mod_name_var.get().strip()
        if not mod_name:
            messagebox.showerror("Error", "Please enter a mod name")
            return
            
        config = load_config()
        mod_path = config.get("mod_path")
        if not mod_path:
            messagebox.showerror("Error", "Please configure mod path first")
            return
            
        success, message = create_mod_template(
            mod_path, 
            mod_name,
            self.author_var.get().strip(),
            self.desc_var.get().strip()
        )
        
        if success:
            messagebox.showinfo("Success", message)
            # Clear entries
            self.mod_name_var.set("")
            self.author_var.set("")
            self.desc_var.set("")
            # Trigger configuration changed event to refresh mod list
            self.event_generate("<<ConfigurationChanged>>")
        else:
            messagebox.showerror("Error", message)

def get_plugin_tab(notebook):
    """Create and return the configuration editor tab"""
    return PLUGIN_TITLE, ConfigEditor(notebook) 