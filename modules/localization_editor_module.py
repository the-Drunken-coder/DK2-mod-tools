import tkinter as tk
from tkinter import ttk, messagebox
import os
import json
from modules import config_editor_module

PLUGIN_TITLE = "Localization Editor"

def is_logging_enabled():
    """Check if logging is enabled for this module"""
    try:
        config_path = os.path.join(os.path.dirname(__file__), 'logging_config.json')
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                config = json.load(f)
                return config.get("localization_editor", False)
    except Exception:
        pass
    return False

def log(message):
    """Module specific logging function"""
    if is_logging_enabled():
        print(f"[LocalizationEditor] {message}")

class LocalizationEditor(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.text_area = None
        self.config = config_editor_module.load_config()
        self.current_file = None
        self.build_ui()

    def build_ui(self):
        # Create main container with horizontal split
        self.paned_window = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        self.paned_window.pack(fill="both", expand=True)

        # Left side - File list
        left_frame = ttk.Frame(self.paned_window)
        self.paned_window.add(left_frame)

        # File list label
        ttk.Label(left_frame, text="Localization Files:").pack(anchor="w", padx=5, pady=5)

        # Create treeview for file list
        self.file_tree = ttk.Treeview(left_frame, selectmode="browse", show="tree")
        self.file_tree.pack(fill="both", expand=True, padx=5, pady=5)
        self.file_tree.bind('<<TreeviewSelect>>', self.on_file_selected)

        # Add refresh button
        ttk.Button(left_frame, text="Refresh Files", command=self.refresh_file_list).pack(padx=5, pady=5)

        # Right side - Text editor
        right_frame = ttk.Frame(self.paned_window)
        self.paned_window.add(right_frame)

        # Add file path label
        self.file_label = ttk.Label(right_frame, text="No file selected")
        self.file_label.pack(fill="x", padx=5, pady=5)

        # Create text editor with scrollbars
        editor_frame = ttk.Frame(right_frame)
        editor_frame.pack(fill="both", expand=True, padx=5, pady=5)

        self.text_area = tk.Text(editor_frame, wrap="none")
        
        # Add scrollbars
        y_scrollbar = ttk.Scrollbar(editor_frame, orient="vertical", command=self.text_area.yview)
        x_scrollbar = ttk.Scrollbar(editor_frame, orient="horizontal", command=self.text_area.xview)
        
        # Configure text widget scrolling
        self.text_area.configure(yscrollcommand=y_scrollbar.set, xscrollcommand=x_scrollbar.set)
        
        # Grid layout for text area and scrollbars
        self.text_area.grid(row=0, column=0, sticky="nsew")
        y_scrollbar.grid(row=0, column=1, sticky="ns")
        x_scrollbar.grid(row=1, column=0, sticky="ew")
        
        # Configure grid weights
        editor_frame.grid_rowconfigure(0, weight=1)
        editor_frame.grid_columnconfigure(0, weight=1)

        # Save Button
        self.save_button = ttk.Button(right_frame, text="Save Changes", command=self.save_changes)
        self.save_button.pack(pady=10)
        self.save_button.configure(state="disabled")  # Disabled until file is selected

        # Initial file list load
        self.refresh_file_list()

    def get_localization_dir(self):
        """Get the localization directory path based on configuration"""
        mod_path = self.config.get("mod_path", "")
        current_mod = self.config.get("last_used_mod", "")
        if not mod_path or not current_mod:
            return None
        return os.path.join(mod_path, current_mod, "localization")

    def refresh_file_list(self):
        """Refresh the list of localization files"""
        # Clear existing items
        for item in self.file_tree.get_children():
            self.file_tree.delete(item)

        loc_dir = self.get_localization_dir()
        if not loc_dir or not os.path.exists(loc_dir):
            self.file_tree.insert("", "end", text="No localization directory found")
            return

        # Add all files from the localization directory
        files = []
        for file in os.listdir(loc_dir):
            if os.path.isfile(os.path.join(loc_dir, file)):
                files.append(file)

        if not files:
            self.file_tree.insert("", "end", text="No files found")
            return

        # Sort files alphabetically
        for file in sorted(files):
            self.file_tree.insert("", "end", text=file, values=(os.path.join(loc_dir, file),))

    def on_file_selected(self, event):
        """Handle file selection from the tree"""
        selection = self.file_tree.selection()
        if not selection:
            return

        item = self.file_tree.item(selection[0])
        if not item["values"]:  # No file path stored
            return

        file_path = item["values"][0]
        self.load_file(file_path)

    def load_file(self, file_path):
        """Load the selected file into the text editor"""
        try:
            if not os.path.exists(file_path):
                messagebox.showerror("Error", "File not found")
                return

            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            self.text_area.delete("1.0", tk.END)
            self.text_area.insert("1.0", content)
            
            # Update current file and UI
            self.current_file = file_path
            self.file_label.config(text=f"Editing: {os.path.basename(file_path)}")
            self.save_button.configure(state="normal")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to load file: {e}")

    def save_changes(self):
        """Save changes to the current file"""
        if not self.current_file:
            return

        try:
            content = self.text_area.get("1.0", tk.END)
            with open(self.current_file, "w", encoding="utf-8") as f:
                f.write(content)
            messagebox.showinfo("Success", "File saved successfully")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save file: {e}")

def get_plugin_tab(notebook):
    """Create and return the localization editor tab"""
    return PLUGIN_TITLE, LocalizationEditor(notebook) 