import tkinter as tk
from tkinter import ttk, messagebox
import xml.etree.ElementTree as ET
import os
from utils import load_xml as util_load_xml
from modules import config_editor_module

PLUGIN_TITLE = "Units Editor"
ENABLE_LOGGING = False  # Toggle module logging

def log(message):
    """Module specific logging function"""
    if ENABLE_LOGGING:
        print(f"[UnitsEditor] {message}")

class UnitsEditor(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.tree = None
        self.unit_elem = None
        self.unit_attr_entries = {}
        self.class_entries = []       # List of tuples: (class_elem, {field: entry})
        self.trooper_rank_entries = []  # List of tuples: (rank_elem, {field: entry})
        self.rank_entries = []          # List of tuples: (rank_elem, {field: entry})
        self.config = config_editor_module.load_config()
        
        self.load_xml()
        self.build_ui()

    def get_xml_path(self):
        """Get the current unit XML file path based on configuration"""
        mod_path = self.config.get("mod_path", "")
        current_mod = self.config.get("last_used_mod", "")
        if not mod_path or not current_mod:
            return None
        
        # Get the full mod directory path
        mod_dir = os.path.join(mod_path, current_mod, "units")
        if not os.path.exists(mod_dir):
            os.makedirs(mod_dir, exist_ok=True)
            return os.path.join(mod_dir, "unit.xml")  # Default fallback
        
        # Find all *_unit.xml files
        unit_files = []
        for file in os.listdir(mod_dir):
            if file.endswith("_unit.xml"):
                full_path = os.path.join(mod_dir, file)
                unit_files.append((full_path, os.path.getsize(full_path)))
        
        # If no *_unit.xml files found, use default unit.xml
        if not unit_files:
            return os.path.join(mod_dir, "unit.xml")
        
        # Sort by file size (largest first) and return the path
        unit_files.sort(key=lambda x: x[1], reverse=True)
        return unit_files[0][0]

    def load_xml(self):
        xml_path = self.get_xml_path()
        if not xml_path:
            messagebox.showerror("Error", "No mod path configured")
            return
            
        if not os.path.exists(xml_path):
            # Create a new unit XML file with basic structure
            root = ET.Element("root")
            unit = ET.SubElement(root, "Unit")
            classes = ET.SubElement(unit, "Classes")
            ranks = ET.SubElement(unit, "Ranks")
            trooper_ranks = ET.SubElement(unit, "TrooperRanks")
            self.tree = ET.ElementTree(root)
            self.unit_elem = unit
            return
            
        self.tree, root = util_load_xml(xml_path)
        if root:
            self.unit_elem = root.find('Unit')
            if self.unit_elem is None:
                messagebox.showerror("Error", "No <Unit> element found in the XML file. Please ensure the XML structure is correct.")
        else:
            self.unit_elem = None

    def build_ui(self):
        # Check if unit_elem is loaded
        if self.unit_elem is None:
            error_label = ttk.Label(self, text="Error: XML file is invalid. <Unit> element not found.")
            error_label.pack(fill='both', expand=True, padx=10, pady=10)
            return
        
        # Section: Unit Attributes
        unit_attr_frame = ttk.LabelFrame(self, text="Unit Attributes")
        unit_attr_frame.pack(fill="x", padx=5, pady=5)
        
        # List of attributes to edit
        fields = ["name", "nameUI", "description", "flagTex", "flagColor", "rndNameEntry", "voicepack", "incapacitationChance", "incapacitationChanceCrit"]
        for i, field in enumerate(fields):
            ttk.Label(unit_attr_frame, text=field).grid(row=i, column=0, sticky="w", padx=5, pady=2)
            entry = ttk.Entry(unit_attr_frame, width=80)
            entry.grid(row=i, column=1, sticky="w", padx=5, pady=2)
            entry.insert(0, self.unit_elem.get(field, ''))
            self.unit_attr_entries[field] = entry
        
        # Section: Classes
        classes_frame = ttk.LabelFrame(self, text="Classes")
        classes_frame.pack(fill="x", padx=5, pady=5)
        
        classes_elem = self.unit_elem.find('Classes')
        if classes_elem is not None:
            headers = ["name", "nameUI", "description", "numSlots", "supply", "iconTex", "upgrades", "maxUpgradeable"]
            # Header row
            for j, header in enumerate(headers):
                ttk.Label(classes_frame, text=header, relief="groove").grid(row=0, column=j, padx=2, pady=2, sticky="nsew")
            row_index = 1
            for class_elem in classes_elem.findall('Class'):
                entry_row = {}
                for j, field in enumerate(headers):
                    entry = ttk.Entry(classes_frame, width=15)
                    entry.grid(row=row_index, column=j, padx=2, pady=2)
                    entry.insert(0, class_elem.get(field, ''))
                    entry_row[field] = entry
                self.class_entries.append((class_elem, entry_row))
                row_index += 1
        
        # Section: Trooper Ranks
        trooper_ranks_frame = ttk.LabelFrame(self, text="Trooper Ranks")
        trooper_ranks_frame.pack(fill="x", padx=5, pady=5)
        headers = ["name", "xpNeeded", "badgeTex"]
        for j, header in enumerate(headers):
            ttk.Label(trooper_ranks_frame, text=header, relief="groove").grid(row=0, column=j, padx=2, pady=2, sticky="nsew")
        row_index = 1
        trooper_ranks_elem = self.unit_elem.find('TrooperRanks')
        if trooper_ranks_elem is not None:
            for rank_elem in trooper_ranks_elem.findall('Rank'):
                entry_row = {}
                for j, field in enumerate(headers):
                    entry = ttk.Entry(trooper_ranks_frame, width=15)
                    entry.grid(row=row_index, column=j, padx=2, pady=2)
                    entry.insert(0, rank_elem.get(field, ''))
                    entry_row[field] = entry
                self.trooper_rank_entries.append((rank_elem, entry_row))
                row_index += 1
        
        # Section: Ranks
        ranks_frame = ttk.LabelFrame(self, text="Ranks")
        ranks_frame.pack(fill="x", padx=5, pady=5)
        headers = ["xpNeeded", "badgeTex"]
        for j, header in enumerate(headers):
            ttk.Label(ranks_frame, text=header, relief="groove").grid(row=0, column=j, padx=2, pady=2, sticky="nsew")
        row_index = 1
        ranks_elem = self.unit_elem.find('Ranks')
        if ranks_elem is not None:
            for rank_elem in ranks_elem.findall('Rank'):
                entry_row = {}
                for j, field in enumerate(headers):
                    entry = ttk.Entry(ranks_frame, width=15)
                    entry.grid(row=row_index, column=j, padx=2, pady=2)
                    entry.insert(0, rank_elem.get(field, ''))
                    entry_row[field] = entry
                self.rank_entries.append((rank_elem, entry_row))
                row_index += 1
        
        # Save Button
        btn_save = ttk.Button(self, text="Save Changes", command=self.save_changes)
        btn_save.pack(pady=10)

    def save_changes(self):
        xml_path = self.get_xml_path()
        if not xml_path:
            messagebox.showerror("Error", "No mod path configured")
            return
            
        # Update unit attributes
        for field, entry in self.unit_attr_entries.items():
            self.unit_elem.set(field, entry.get())
        
        # Update Classes
        classes_elem = self.unit_elem.find('Classes')
        if classes_elem is not None:
            for class_elem, entries in self.class_entries:
                for field, entry in entries.items():
                    class_elem.set(field, entry.get())
        
        # Update Trooper Ranks
        trooper_ranks_elem = self.unit_elem.find('TrooperRanks')
        if trooper_ranks_elem is not None:
            for rank_elem, entries in self.trooper_rank_entries:
                for field, entry in entries.items():
                    rank_elem.set(field, entry.get())
        
        # Update Ranks
        ranks_elem = self.unit_elem.find('Ranks')
        if ranks_elem is not None:
            for rank_elem, entries in self.rank_entries:
                for field, entry in entries.items():
                    rank_elem.set(field, entry.get())
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(xml_path), exist_ok=True)
        
        # Write back to XML file
        try:
            self.tree.write(xml_path, encoding='utf-8', xml_declaration=True)
            messagebox.showinfo("Success", "XML file updated successfully.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to write XML: {e}")

def get_plugin_tab(notebook):
    """Create and return the units editor tab"""
    return PLUGIN_TITLE, UnitsEditor(notebook) 