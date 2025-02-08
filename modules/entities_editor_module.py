import tkinter as tk
from tkinter import ttk, messagebox
import xml.etree.ElementTree as ET
import os
from modules import config_editor_module

PLUGIN_TITLE = "Entities Editor"
ENABLE_LOGGING = False  # Toggle module logging

def log(message):
    """Module specific logging function"""
    if ENABLE_LOGGING:
        print(f"[EntitiesEditor] {message}")

class EntitiesEditor(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.tree = None
        self.entities = []
        self.current_entity = None
        self.config = config_editor_module.load_config()

        self.entity_attr_entries = {}
        self.human_attr_entries = {}
        self.id_attr_entries = {}
        self.fov_attr_entries = {}
        self.brain_attr_entries = {}
        self.move_speed_entries = {}
        self.turn_speed_entries = {}
        self.physical_params_entries = {}
        self.equipment_entry = None

        self.build_ui()
        self.load_xml()

    def get_mod_path(self):
        """Get the current mod path based on configuration"""
        mod_path = self.config.get("mod_path", "")
        current_mod = self.config.get("last_used_mod", "")
        if not mod_path or not current_mod:
            return None
        return os.path.join(mod_path, current_mod)
        
    def get_xml_path(self):
        """Get the current entities XML file path based on configuration"""
        mod_path = self.get_mod_path()
        if not mod_path:
            return None
            
        # Find all *_humans.xml files in the entities directory
        entities_dir = os.path.join(mod_path, "entities")
        if not os.path.exists(entities_dir):
            os.makedirs(entities_dir, exist_ok=True)
            return os.path.join(entities_dir, "humans.xml")  # Default fallback
            
        # Find all *_humans.xml files
        human_files = []
        for file in os.listdir(entities_dir):
            if file.endswith("_humans.xml"):
                full_path = os.path.join(entities_dir, file)
                human_files.append((full_path, os.path.getsize(full_path)))
                
        # If no *_humans.xml files found, use default humans.xml
        if not human_files:
            return os.path.join(entities_dir, "humans.xml")
            
        # Sort by file size (largest first) and return the path
        human_files.sort(key=lambda x: x[1], reverse=True)
        return human_files[0][0]

    def load_xml(self):
        try:
            xml_path = self.get_xml_path()
            if not xml_path:
                messagebox.showerror("Error", "No mod path configured")
                return
                
            if not os.path.exists(xml_path):
                # Create basic structure
                root = ET.Element("Entities")
                # Add a comment explaining the file
                root.append(ET.Comment("Human entity definitions for the mod"))
                tree = ET.ElementTree(root)
                tree.write(xml_path, encoding='utf-8', xml_declaration=True)
                messagebox.showinfo("Info", "Created new humans.xml file with default structure")
                
            self.tree = ET.parse(xml_path)
            root = self.tree.getroot()
            self.entities = root.findall('Entity')
            if not self.entities:
                messagebox.showerror("Error", "No <Entity> elements found in XML.")
                return
            entity_names = [e.get("name", "Unnamed") for e in self.entities]
            self.entity_select_combobox['values'] = entity_names
            self.entity_select_combobox.current(0)
            self.current_entity = self.entities[0]
            self.load_entity(self.current_entity)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load XML: {e}")

    def build_ui(self):
        top_frame = ttk.Frame(self)
        top_frame.pack(fill="x", padx=5, pady=5)
        ttk.Label(top_frame, text="Select Entity:").pack(side="left")
        self.entity_select_combobox = ttk.Combobox(top_frame, state="readonly")
        self.entity_select_combobox.pack(side="left", padx=5)
        self.entity_select_combobox.bind("<<ComboboxSelected>>", self.on_entity_selected)

        entity_frame = ttk.LabelFrame(self, text="Entity Attributes")
        entity_frame.pack(fill="x", padx=5, pady=5)
        for i, field in enumerate(["name", "type", "editorAutoHeight"]):
            ttk.Label(entity_frame, text=field).grid(row=i, column=0, sticky="w", padx=5, pady=2)
            entry = ttk.Entry(entity_frame, width=80)
            entry.grid(row=i, column=1, sticky="w", padx=5, pady=2)
            self.entity_attr_entries[field] = entry

        # Add Physical Params frame
        physical_frame = ttk.LabelFrame(self, text="Physical Parameters")
        physical_frame.pack(fill="x", padx=5, pady=5)
        ttk.Label(physical_frame, text="Health:").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        health_entry = ttk.Entry(physical_frame, width=10)
        health_entry.grid(row=0, column=1, sticky="w", padx=5, pady=2)
        health_entry.insert(0, "100")  # Default value
        self.physical_params_entries["health"] = health_entry

        human_frame = ttk.LabelFrame(self, text="Human Attributes")
        human_frame.pack(fill="x", padx=5, pady=5)
        for i, field in enumerate(["type", "unit", "class"]):
            ttk.Label(human_frame, text=field).grid(row=i, column=0, sticky="w", padx=5, pady=2)
            entry = ttk.Entry(human_frame, width=80)
            entry.grid(row=i, column=1, sticky="w", padx=5, pady=2)
            self.human_attr_entries[field] = entry

        id_frame = ttk.LabelFrame(self, text="Id Attributes")
        id_frame.pack(fill="x", padx=5, pady=5)
        for i, field in enumerate(["name", "portrait", "gender", "voicePack"]):
            ttk.Label(id_frame, text=field).grid(row=i, column=0, sticky="w", padx=5, pady=2)
            entry = ttk.Entry(id_frame, width=80)
            entry.grid(row=i, column=1, sticky="w", padx=5, pady=2)
            self.id_attr_entries[field] = entry

        fov_frame = ttk.LabelFrame(self, text="FOV Attributes")
        fov_frame.pack(fill="x", padx=5, pady=5)
        for i, field in enumerate(["degrees", "distanceMeters", "eyeRadiusMeters"]):
            ttk.Label(fov_frame, text=field).grid(row=i, column=0, sticky="w", padx=5, pady=2)
            entry = ttk.Entry(fov_frame, width=80)
            entry.grid(row=i, column=1, sticky="w", padx=5, pady=2)
            self.fov_attr_entries[field] = entry

        brain_frame = ttk.LabelFrame(self, text="Brain Attributes")
        brain_frame.pack(fill="x", padx=5, pady=5)
        ttk.Label(brain_frame, text="suppressionRecovery").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        brain_entry = ttk.Entry(brain_frame, width=80)
        brain_entry.grid(row=0, column=1, sticky="w", padx=5, pady=2)
        self.brain_attr_entries["suppressionRecovery"] = brain_entry

        mobility_frame = ttk.LabelFrame(self, text="Mobility")
        mobility_frame.pack(fill="x", padx=5, pady=5)
        movespeed_frame = ttk.LabelFrame(mobility_frame, text="MoveSpeed")
        movespeed_frame.pack(fill="x", padx=5, pady=5)
        for i, field in enumerate(["min", "defaultMetersPerSec", "max"]):
            ttk.Label(movespeed_frame, text=field).grid(row=0, column=i, sticky="w", padx=5, pady=2)
            entry = ttk.Entry(movespeed_frame, width=15)
            entry.grid(row=1, column=i, sticky="w", padx=5, pady=2)
            self.move_speed_entries[field] = entry

        turnspeed_frame = ttk.LabelFrame(mobility_frame, text="TurnSpeed")
        turnspeed_frame.pack(fill="x", padx=5, pady=5)
        for i, field in enumerate(["min", "defaultMetersPerSec", "max"]):
            ttk.Label(turnspeed_frame, text=field).grid(row=0, column=i, sticky="w", padx=5, pady=2)
            entry = ttk.Entry(turnspeed_frame, width=15)
            entry.grid(row=1, column=i, sticky="w", padx=5, pady=2)
            self.turn_speed_entries[field] = entry

        equipment_frame = ttk.LabelFrame(self, text="Equipment (comma separated Items)")
        equipment_frame.pack(fill="x", padx=5, pady=5)
        self.equipment_entry = ttk.Entry(equipment_frame, width=80)
        self.equipment_entry.pack(padx=5, pady=5)

        btn_save = ttk.Button(self, text="Save Changes", command=self.save_changes)
        btn_save.pack(pady=10)

    def on_entity_selected(self, event):
        index = self.entity_select_combobox.current()
        self.current_entity = self.entities[index]
        self.load_entity(self.current_entity)

    def load_entity(self, entity):
        for field, entry in self.entity_attr_entries.items():
            entry.delete(0, tk.END)
            entry.insert(0, entity.get(field, ""))
        
        # Load Physical Params
        physical_params = entity.find('PhysicalParams')
        if physical_params is not None:
            health_entry = self.physical_params_entries["health"]
            health_entry.delete(0, tk.END)
            health_entry.insert(0, physical_params.get("health", "100"))
        
        human_elem = entity.find('Human')
        if human_elem is not None:
            for field, entry in self.human_attr_entries.items():
                entry.delete(0, tk.END)
                entry.insert(0, human_elem.get(field, ""))
            
            id_elem = human_elem.find('Id')
            if id_elem is not None:
                for field, entry in self.id_attr_entries.items():
                    entry.delete(0, tk.END)
                    entry.insert(0, id_elem.get(field, ""))
            else:
                for entry in self.id_attr_entries.values():
                    entry.delete(0, tk.END)
            
            fov_elem = human_elem.find('FOV')
            if fov_elem is not None:
                for field, entry in self.fov_attr_entries.items():
                    entry.delete(0, tk.END)
                    entry.insert(0, fov_elem.get(field, ""))
            else:
                for entry in self.fov_attr_entries.values():
                    entry.delete(0, tk.END)
            
            brain_elem = human_elem.find('Brain')
            if brain_elem is not None:
                brain_entry = self.brain_attr_entries["suppressionRecovery"]
                brain_entry.delete(0, tk.END)
                brain_entry.insert(0, brain_elem.get("suppressionRecovery", ""))
            else:
                self.brain_attr_entries["suppressionRecovery"].delete(0, tk.END)
            
            mobility_elem = human_elem.find('Mobility')
            if mobility_elem is not None:
                move_speed_elem = mobility_elem.find('MoveSpeed')
                if move_speed_elem is not None:
                    for field, entry in self.move_speed_entries.items():
                        entry.delete(0, tk.END)
                        entry.insert(0, move_speed_elem.get(field, ""))
                else:
                    for entry in self.move_speed_entries.values():
                        entry.delete(0, tk.END)
                turn_speed_elem = mobility_elem.find('TurnSpeed')
                if turn_speed_elem is not None:
                    for field, entry in self.turn_speed_entries.items():
                        entry.delete(0, tk.END)
                        entry.insert(0, turn_speed_elem.get(field, ""))
                else:
                    for entry in self.turn_speed_entries.values():
                        entry.delete(0, tk.END)
            else:
                for entry in self.move_speed_entries.values():
                    entry.delete(0, tk.END)
                for entry in self.turn_speed_entries.values():
                    entry.delete(0, tk.END)
            
            equipment_elem = human_elem.find('Equipment')
            if equipment_elem is not None:
                items = [itm.get("name", "") for itm in equipment_elem.findall('Item')]
                self.equipment_entry.delete(0, tk.END)
                self.equipment_entry.insert(0, ", ".join(items))
            else:
                self.equipment_entry.delete(0, tk.END)
        else:
            for entries in [self.human_attr_entries, self.id_attr_entries, self.fov_attr_entries, self.brain_attr_entries]:
                for entry in entries.values():
                    entry.delete(0, tk.END)
            for entries in [self.move_speed_entries, self.turn_speed_entries]:
                for entry in entries.values():
                    entry.delete(0, tk.END)
            self.equipment_entry.delete(0, tk.END)

    def save_changes(self):
        if self.current_entity is None:
            return
            
        # Get the XML path
        xml_path = self.get_xml_path()
        if not xml_path:
            messagebox.showerror("Error", "No mod path configured")
            return
            
        for field, entry in self.entity_attr_entries.items():
            self.current_entity.set(field, entry.get())
        
        # Save Physical Params
        physical_params = self.current_entity.find('PhysicalParams')
        if physical_params is None:
            physical_params = ET.SubElement(self.current_entity, 'PhysicalParams')
        physical_params.set("health", self.physical_params_entries["health"].get())
        
        human_elem = self.current_entity.find('Human')
        if human_elem is None:
            human_elem = ET.SubElement(self.current_entity, 'Human')
        for field, entry in self.human_attr_entries.items():
            human_elem.set(field, entry.get())
        
        id_elem = human_elem.find('Id')
        if id_elem is None:
            id_elem = ET.SubElement(human_elem, 'Id')
        for field, entry in self.id_attr_entries.items():
            id_elem.set(field, entry.get())

        fov_elem = human_elem.find('FOV')
        if fov_elem is None:
            fov_elem = ET.SubElement(human_elem, 'FOV')
        for field, entry in self.fov_attr_entries.items():
            fov_elem.set(field, entry.get())

        brain_elem = human_elem.find('Brain')
        if brain_elem is None:
            brain_elem = ET.SubElement(human_elem, 'Brain')
        brain_elem.set("suppressionRecovery", self.brain_attr_entries["suppressionRecovery"].get())

        mobility_elem = human_elem.find('Mobility')
        if mobility_elem is None:
            mobility_elem = ET.SubElement(human_elem, 'Mobility')
        move_speed_elem = mobility_elem.find('MoveSpeed')
        if move_speed_elem is None:
            move_speed_elem = ET.SubElement(mobility_elem, 'MoveSpeed')
        for field, entry in self.move_speed_entries.items():
            move_speed_elem.set(field, entry.get())
        turn_speed_elem = mobility_elem.find('TurnSpeed')
        if turn_speed_elem is None:
            turn_speed_elem = ET.SubElement(mobility_elem, 'TurnSpeed')
        for field, entry in self.turn_speed_entries.items():
            turn_speed_elem.set(field, entry.get())

        equipment_elem = human_elem.find('Equipment')
        if equipment_elem is not None:
            human_elem.remove(equipment_elem)
        equipment_elem = ET.SubElement(human_elem, 'Equipment')
        items_text = self.equipment_entry.get()
        for item in [itm.strip() for itm in items_text.split(",") if itm.strip()]:
            item_elem = ET.SubElement(equipment_elem, 'Item')
            item_elem.set("name", item)
        
        try:
            self.tree.write(xml_path, encoding='utf-8', xml_declaration=True)
            messagebox.showinfo("Success", "XML file updated successfully.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to write XML: {e}")


def get_plugin_tab(parent):
    container = ttk.Frame(parent)
    editor = EntitiesEditor(container)
    editor.pack(fill="both", expand=True)
    return "Entities Editor", container 