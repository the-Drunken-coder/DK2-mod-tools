import tkinter as tk
from tkinter import ttk, messagebox
import os
import xml.etree.ElementTree as ET
from modules import config_editor_module

PLUGIN_TITLE = "Mod Metadata"

class ModMetadataEditor(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.tree = None
        self.mod_elem = None
        self.attr_entries = {}
        self.config = config_editor_module.load_config()
        
        self.load_xml()
        self.build_ui()

    def get_xml_path(self):
        """Get the current mod.xml file path based on configuration"""
        mod_path = self.config.get("mod_path", "")
        current_mod = self.config.get("last_used_mod", "")
        if not mod_path or not current_mod:
            return None
        return os.path.join(mod_path, current_mod, "mod.xml")

    def load_xml(self):
        try:
            xml_path = self.get_xml_path()
            if not xml_path:
                messagebox.showerror("Error", "No mod path configured")
                return
                
            if not os.path.exists(xml_path):
                # Create basic mod.xml structure
                root = ET.Element("mod")
                root.set("title", "")
                root.set("description", "")
                root.set("author", "")
                root.set("tags", "")
                root.set("gameVersion", "")
                self.tree = ET.ElementTree(root)
                self.mod_elem = root
                # Write the file
                os.makedirs(os.path.dirname(xml_path), exist_ok=True)
                self.tree.write(xml_path, encoding='utf-8', xml_declaration=True)
            else:
                self.tree = ET.parse(xml_path)
                root = self.tree.getroot()
                self.mod_elem = root
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load XML: {e}")

    def build_ui(self):
        if self.mod_elem is None:
            error_label = ttk.Label(self, text="Please configure mod path and select a mod in the Configuration tab.")
            error_label.grid(row=0, column=0, columnspan=2, padx=10, pady=10)
            return
        
        # List of attributes to edit
        fields = ["title", "description", "author", "tags", "gameVersion"]
        for i, field in enumerate(fields):
            ttk.Label(self, text=field).grid(row=i, column=0, sticky="w", padx=5, pady=2)
            entry = ttk.Entry(self, width=50)
            entry.grid(row=i, column=1, sticky="w", padx=5, pady=2)
            entry.insert(0, self.mod_elem.get(field, ''))
            self.attr_entries[field] = entry
        
        # Save Button
        btn_save = ttk.Button(self, text="Save Changes", command=self.save_changes)
        btn_save.grid(row=len(fields), column=0, columnspan=2, pady=10)

    def save_changes(self):
        xml_path = self.get_xml_path()
        if not xml_path:
            messagebox.showerror("Error", "No mod path configured")
            return
            
        for field, entry in self.attr_entries.items():
            self.mod_elem.set(field, entry.get())
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(xml_path), exist_ok=True)
            self.tree.write(xml_path, encoding='utf-8', xml_declaration=True)
            messagebox.showinfo("Success", "XML file updated successfully.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to write XML: {e}")


def get_plugin_tab(notebook):
    """Create and return the mod metadata editor tab"""
    return PLUGIN_TITLE, ModMetadataEditor(notebook) 