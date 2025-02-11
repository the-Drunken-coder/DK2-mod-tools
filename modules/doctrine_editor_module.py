import tkinter as tk
from tkinter import ttk, messagebox
import os
import json
import xml.etree.ElementTree as ET
from modules import config_editor_module, mod_files

PLUGIN_TITLE = "Doctrine Editor"

def is_logging_enabled():
    """Check if logging is enabled for this module"""
    try:
        config_path = os.path.join(os.path.dirname(__file__), 'logging_config.json')
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                config = json.load(f)
                return config.get("doctrine_editor", False)
    except Exception:
        pass
    return False

def log(message):
    """Module specific logging function"""
    if is_logging_enabled():
        print(f"[DoctrineEditor] {message}")

class DoctrineEditor(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.config = config_editor_module.load_config()
        self.doctrine_tree = None
        self.doctrine_nodes_tree = None
        
        # Initialize ModFiles with the current mod path
        mod_path = self.get_mod_path()
        if mod_path:
            mod_files.mod_files.mod_path = mod_path
            mod_files.mod_files.scan_mod_directory()
        
        self.build_ui()

    def get_mod_path(self):
        """Get the current mod path based on configuration"""
        mod_path = self.config.get("mod_path", "")
        current_mod = self.config.get("last_used_mod", "")
        if not mod_path or not current_mod:
            return None
        return os.path.join(mod_path, current_mod)

    def build_ui(self):
        # Create main container with horizontal split
        self.paned_window = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        self.paned_window.pack(fill="both", expand=True)

        # Left side - Doctrine nodes
        left_frame = ttk.LabelFrame(self.paned_window, text="Doctrine Nodes")
        self.paned_window.add(left_frame)

        # Add "Create Doctrine Nodes File" button if file doesn't exist
        self.create_nodes_btn = ttk.Button(left_frame, text="Create Doctrine Nodes File", 
                                         command=self.create_doctrine_nodes)
        self.create_nodes_btn.pack(padx=5, pady=5)

        # Right side - Doctrine strings
        right_frame = ttk.LabelFrame(self.paned_window, text="Doctrine Strings")
        self.paned_window.add(right_frame)

        # Add "Create Doctrine File" button if file doesn't exist
        self.create_doctrine_btn = ttk.Button(right_frame, text="Create Doctrine File", 
                                            command=self.create_doctrine)
        self.create_doctrine_btn.pack(padx=5, pady=5)

        # Initial load
        self.refresh_files()

    def refresh_files(self):
        """Check for doctrine files and update UI accordingly"""
        if not self.get_mod_path():
            self.create_nodes_btn.configure(state="disabled")
            self.create_doctrine_btn.configure(state="disabled")
            return
            
        # Check for doctrine nodes file
        nodes_file = mod_files.mod_files.get_doctrine_nodes_file()
        if nodes_file and os.path.exists(nodes_file):
            self.create_nodes_btn.configure(state="disabled")
            log(f"Found doctrine nodes file: {nodes_file}")
        else:
            self.create_nodes_btn.configure(state="normal")
            log("No doctrine nodes file found")

        # Check for doctrine file
        doctrine_file = mod_files.mod_files.get_doctrine_file()
        if doctrine_file and os.path.exists(doctrine_file):
            self.create_doctrine_btn.configure(state="disabled")
            log(f"Found doctrine file: {doctrine_file}")
        else:
            self.create_doctrine_btn.configure(state="normal")
            log("No doctrine file found")

    def create_doctrine_nodes(self):
        """Create a new doctrine nodes file"""
        if not self.get_mod_path():
            messagebox.showerror("Error", "Please configure mod path and select a mod first")
            return
            
        success, message = mod_files.mod_files.create_doctrine_nodes_file()
        if success:
            messagebox.showinfo("Success", message)
        else:
            messagebox.showerror("Error", message)
        self.refresh_files()

    def create_doctrine(self):
        """Create a new doctrine file"""
        if not self.get_mod_path():
            messagebox.showerror("Error", "Please configure mod path and select a mod first")
            return
            
        success, message = mod_files.mod_files.create_doctrine_file()
        if success:
            messagebox.showinfo("Success", message)
        else:
            messagebox.showerror("Error", message)
        self.refresh_files()

def get_plugin_tab(notebook):
    """Create and return the doctrine editor tab"""
    return PLUGIN_TITLE, DoctrineEditor(notebook) 