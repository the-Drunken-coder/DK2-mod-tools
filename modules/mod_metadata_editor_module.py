import tkinter as tk
from tkinter import ttk, messagebox
import os
import xml.etree.ElementTree as ET

# Path to the mod metadata XML file
XML_PATH = os.path.join("Example mod", "Baby seals", "mod.xml")

class ModMetadataEditor(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.tree = None
        self.mod_elem = None
        self.attr_entries = {}
        
        self.load_xml()
        self.build_ui()

    def load_xml(self):
        try:
            self.tree = ET.parse(XML_PATH)
            root = self.tree.getroot()
            self.mod_elem = root
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load XML: {e}")

    def build_ui(self):
        if self.mod_elem is None:
            error_label = ttk.Label(self, text="Error: XML file is invalid.")
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
        for field, entry in self.attr_entries.items():
            self.mod_elem.set(field, entry.get())
        try:
            self.tree.write(XML_PATH, encoding='utf-8', xml_declaration=True)
            messagebox.showinfo("Success", "XML file updated successfully.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to write XML: {e}")


def get_plugin_tab(parent):
    container = ttk.Frame(parent)
    editor = ModMetadataEditor(container)
    editor.pack(fill="both", expand=True)
    return "Mod Metadata", container 