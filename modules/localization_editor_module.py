import tkinter as tk
from tkinter import ttk, messagebox
import os
from modules import config_editor_module

PLUGIN_TITLE = "Localization Editor"

class LocalizationEditor(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.text_area = None
        self.config = config_editor_module.load_config()
        self.build_ui()

    def build_ui(self):
        # Create a Text widget with a Scrollbar
        self.text_area = tk.Text(self, wrap="word")
        self.text_area.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        scrollbar = ttk.Scrollbar(self, command=self.text_area.yview)
        scrollbar.pack(side="right", fill="y")
        self.text_area.config(yscrollcommand=scrollbar.set)
        
        # Load file content
        self.load_file()
        
        # Save Button
        btn_save = ttk.Button(self, text="Save Changes", command=self.save_changes)
        btn_save.pack(pady=10)

    def get_file_path(self):
        """Get the current localization file path based on configuration"""
        mod_path = self.config.get("mod_path", "")
        current_mod = self.config.get("last_used_mod", "")
        if not mod_path or not current_mod:
            return None
        return os.path.join(mod_path, current_mod, "localization", "strings.xml")

    def load_file(self):
        file_path = self.get_file_path()
        if not file_path:
            self.text_area.delete("1.0", tk.END)
            self.text_area.insert("1.0", "Please configure mod path and select a mod in the Configuration tab.")
            return
            
        try:
            if os.path.exists(file_path):
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
            else:
                content = "<!-- Create new localization strings here -->\n<strings>\n</strings>"
            self.text_area.delete("1.0", tk.END)
            self.text_area.insert("1.0", content)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load file: {e}")

    def save_changes(self):
        file_path = self.get_file_path()
        if not file_path:
            messagebox.showerror("Error", "No mod path configured")
            return
            
        try:
            # Create localization directory if it doesn't exist
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            content = self.text_area.get("1.0", tk.END)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            messagebox.showinfo("Success", "File saved successfully.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save file: {e}")

def get_plugin_tab(notebook):
    """Create and return the localization editor tab"""
    return PLUGIN_TITLE, LocalizationEditor(notebook) 