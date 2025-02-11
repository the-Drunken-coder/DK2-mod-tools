import tkinter as tk
from tkinter import ttk, messagebox
import xml.etree.ElementTree as ET
import os
import json
from modules import config_editor_module

PLUGIN_TITLE = "Entities Editor"

def is_logging_enabled():
    """Check if logging is enabled for this module"""
    try:
        config_path = os.path.join(os.path.dirname(__file__), 'logging_config.json')
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                config = json.load(f)
                return config.get("entities_editor", False)
    except Exception:
        pass
    return False

def log(message):
    """Module specific logging function"""
    if is_logging_enabled():
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
            
        # Find all XML files in the entities directory
        entities_dir = os.path.join(mod_path, "entities")
        if not os.path.exists(entities_dir):
            return None
            
        # First try files with 'human' in the name
        human_files = []
        for file in os.listdir(entities_dir):
            if file.lower().endswith('.xml'):
                full_path = os.path.join(entities_dir, file)
                human_files.append((full_path, os.path.getsize(full_path)))
        
        # Sort by size (largest first)
        human_files.sort(key=lambda x: x[1], reverse=True)
        
        # Check each file for type="Human"
        for file_path, _ in human_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if 'type="Human"' in content:
                        log(f"Found human entities in file: {os.path.basename(file_path)}")
                        return file_path
            except Exception as e:
                log(f"Error reading file {file_path}: {e}")
                continue
        
        # If no file found with type="Human", return None
        log("No file found containing human entities")
        return None

    def load_xml(self):
        try:
            xml_path = self.get_xml_path()
            if not xml_path:
                messagebox.showinfo("Info", "No human entities file found. Please create one in your mod's entities folder.")
                return
                
            if not os.path.exists(xml_path):
                messagebox.showinfo("Info", "No human entities file found. Please create one in your mod's entities folder.")
                return
                
            self.tree = ET.parse(xml_path)
            self.unit_elem = self.tree.getroot()
            
            self.entities = self.unit_elem.findall('Entity')
            if not self.entities:
                messagebox.showinfo("Info", "No entities found. Create a new entity to get started.")
                return
            
            entity_names = [e.get("name", "Unnamed") for e in self.entities]
            self.entity_select_combobox['values'] = entity_names
            self.entity_select_combobox.current(0)
            self.current_entity = self.entities[0]
            self.load_entity(self.current_entity)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load XML: {e}")
            print(f"XML load error details: {str(e)}")  # For debugging

    def build_ui(self):
        top_frame = ttk.Frame(self)
        top_frame.pack(fill="x", padx=5, pady=5)
        
        # Add New Entity button
        ttk.Button(top_frame, text="Create New Entity", command=self.create_new_entity).pack(side="left", padx=5)
        
        ttk.Label(top_frame, text="Select Entity:").pack(side="left", padx=(10,5))
        self.entity_select_combobox = ttk.Combobox(top_frame, state="readonly")
        self.entity_select_combobox.pack(side="left", padx=5)
        self.entity_select_combobox.bind("<<ComboboxSelected>>", self.on_entity_selected)
        
        # Add Delete Entity button
        ttk.Button(top_frame, text="Delete Entity", command=self.delete_current_entity,
                  style="Delete.TButton").pack(side="left", padx=5)
        
        # Create a style for the delete button (red text)
        delete_style = ttk.Style()
        delete_style.configure("Delete.TButton", foreground="red")

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

    def create_new_entity(self):
        """Create a new entity dialog"""
        dialog = tk.Toplevel(self)
        dialog.title("Create New Entity")
        dialog.geometry("800x600")  # Made wider and taller for more fields
        
        # Create main frame with scrollbar
        main_frame = ttk.Frame(dialog)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        canvas = tk.Canvas(main_frame)
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Pack scrollbar elements
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        row = 0
        # Basic Entity Attributes
        ttk.Label(scrollable_frame, text="Basic Entity Attributes:", font=("TkDefaultFont", 10, "bold")).grid(
            row=row, column=0, columnspan=2, sticky="w", padx=5, pady=(5,2))
        row += 1
        
        fields = {
            "name": "Entity Name (e.g. assaulter_01)",
            "type": "Entity Type (e.g. Human)",
            "editorAutoHeight": "Editor Auto Height (e.g. false)"
        }
        
        entries = {}
        for field, label in fields.items():
            ttk.Label(scrollable_frame, text=label).grid(row=row, column=0, sticky="w", padx=5, pady=2)
            entry = ttk.Entry(scrollable_frame, width=50)
            entry.grid(row=row, column=1, sticky="w", padx=5, pady=2)
            entries[field] = entry
            row += 1
            
            # Add default values
            if field == "type":
                entry.insert(0, "Human")
            elif field == "editorAutoHeight":
                entry.insert(0, "false")
        
        # Visual Elements Section
        ttk.Label(scrollable_frame, text="Visual Elements:", font=("TkDefaultFont", 10, "bold")).grid(
            row=row, column=0, columnspan=2, sticky="w", padx=5, pady=(10,2))
        row += 1
        
        # RenderObject3D entries
        render_objects = []
        def add_render_object():
            nonlocal row
            render_frame = ttk.LabelFrame(scrollable_frame, text=f"RenderObject3D {len(render_objects)+1}")
            render_frame.grid(row=row, column=0, columnspan=2, sticky="ew", padx=5, pady=2)
            
            render_entries = {}
            render_entries["model"] = ttk.Entry(render_frame, width=70)
            render_entries["model"].insert(0, "data/models/humans/ranger_assaulter.khm")
            ttk.Label(render_frame, text="Model:").pack(anchor="w", padx=5)
            render_entries["model"].pack(fill="x", padx=5, pady=2)
            
            render_entries["diffuseTex"] = ttk.Entry(render_frame, width=70)
            render_entries["diffuseTex"].insert(0, "data/models/humans/ranger_assaulter.dds")
            ttk.Label(render_frame, text="Texture:").pack(anchor="w", padx=5)
            render_entries["diffuseTex"].pack(fill="x", padx=5, pady=2)
            
            # Optional attributes
            render_entries["windAnimated"] = tk.BooleanVar(value=False)
            ttk.Checkbutton(render_frame, text="Wind Animated", variable=render_entries["windAnimated"]).pack(anchor="w", padx=5)
            
            # Specular settings frame
            specular_frame = ttk.Frame(render_frame)
            specular_frame.pack(fill="x", padx=5, pady=2)
            render_entries["specular"] = {
                "shininess": ttk.Entry(specular_frame, width=10),
                "intensity": ttk.Entry(specular_frame, width=10)
            }
            ttk.Label(specular_frame, text="Specular Shininess:").pack(side="left", padx=2)
            render_entries["specular"]["shininess"].pack(side="left", padx=2)
            ttk.Label(specular_frame, text="Intensity:").pack(side="left", padx=2)
            render_entries["specular"]["intensity"].pack(side="left", padx=2)
            
            render_objects.append(render_entries)
            row += 1
        
        ttk.Button(scrollable_frame, text="Add RenderObject3D", command=add_render_object).grid(
            row=row, column=0, columnspan=2, pady=5)
        row += 1
        
        # Breakable section
        ttk.Label(scrollable_frame, text="Breakable Settings:", font=("TkDefaultFont", 10, "bold")).grid(
            row=row, column=0, columnspan=2, sticky="w", padx=5, pady=(10,2))
        row += 1
        
        breakable_frame = ttk.Frame(scrollable_frame)
        breakable_frame.grid(row=row, column=0, columnspan=2, sticky="ew", padx=5, pady=2)
        breakable_entries = {
            "template": ttk.Entry(breakable_frame, width=30),
            "breakOnDamage": ttk.Entry(breakable_frame, width=20),
            "deleteOnDeath": tk.BooleanVar(value=False)
        }
        
        ttk.Label(breakable_frame, text="Template:").pack(side="left", padx=2)
        breakable_entries["template"].pack(side="left", padx=2)
        breakable_entries["template"].insert(0, "GenericTrooperGibs")
        
        ttk.Label(breakable_frame, text="Break On:").pack(side="left", padx=2)
        breakable_entries["breakOnDamage"].pack(side="left", padx=2)
        breakable_entries["breakOnDamage"].insert(0, "explosive")
        
        ttk.Checkbutton(breakable_frame, text="Delete On Death", 
                        variable=breakable_entries["deleteOnDeath"]).pack(side="left", padx=2)
        row += 1
        
        # Human Attributes Section
        ttk.Label(scrollable_frame, text="Human Attributes:", font=("TkDefaultFont", 10, "bold")).grid(
            row=row, column=0, columnspan=2, sticky="w", padx=5, pady=(10,2))
        row += 1
        
        human_fields = {
            "type": "Human Type (e.g. GoodGuy)",
            "unit": "Unit Name (e.g. FACTION)",
            "class": "Class Name (e.g. AssaultClass)"
        }
        
        human_entries = {}
        for field, label in human_fields.items():
            ttk.Label(scrollable_frame, text=label).grid(row=row, column=0, sticky="w", padx=5, pady=2)
            entry = ttk.Entry(scrollable_frame, width=50)
            entry.grid(row=row, column=1, sticky="w", padx=5, pady=2)
            human_entries[field] = entry
            row += 1
            
            # Add default values
            if field == "type":
                entry.insert(0, "GoodGuy")
            elif field == "unit":
                entry.insert(0, "FACTION")
        
        def add_entity():
            # Get values from entries
            values = {field: entry.get().strip() for field, entry in entries.items()}
            human_values = {field: entry.get().strip() for field, entry in human_entries.items()}
            
            # Validate required fields
            if not values["name"] or not values["type"]:
                messagebox.showerror("Error", "Entity Name and Type are required")
                return
            
            # Create new Entity element
            entity = ET.Element("Entity")
            for field, value in values.items():
                if value:  # Only set non-empty values
                    entity.set(field, value)
            
            # Add RenderObject3D elements
            for render_obj in render_objects:
                render_elem = ET.SubElement(entity, "RenderObject3D")
                render_elem.set("model", render_obj["model"].get())
                render_elem.set("diffuseTex", render_obj["diffuseTex"].get())
                
                if render_obj["windAnimated"].get():
                    render_elem.set("windAnimated", "1")
                
                # Add Specular if values are provided
                if render_obj["specular"]["shininess"].get() or render_obj["specular"]["intensity"].get():
                    specular = ET.SubElement(render_elem, "Specular")
                    if render_obj["specular"]["shininess"].get():
                        specular.set("shininess", render_obj["specular"]["shininess"].get())
                    if render_obj["specular"]["intensity"].get():
                        specular.set("intensity", render_obj["specular"]["intensity"].get())
            
            # Add Breakable element
            breakable = ET.SubElement(entity, "Breakable")
            breakable.set("template", breakable_entries["template"].get())
            breakable.set("breakOnDamage", breakable_entries["breakOnDamage"].get())
            breakable.set("deleteOnDeath", "true" if breakable_entries["deleteOnDeath"].get() else "false")
            
            # Add PhysicalParams
            physical = ET.SubElement(entity, "PhysicalParams")
            physical.set("health", "100")
            
            # Create Human subelement
            human = ET.SubElement(entity, "Human")
            for field, value in human_values.items():
                if value:  # Only set non-empty values
                    human.set(field, value)
            
            # Add default subelements
            id_elem = ET.SubElement(human, "Id")
            id_elem.set("name", values["name"] + "Template")
            id_elem.set("portrait", "data/textures/portraits/ranger2.dds")
            id_elem.set("gender", "0")
            id_elem.set("voicePack", "nws_male")
            
            fov_elem = ET.SubElement(human, "FOV")
            fov_elem.set("degrees", "90")
            fov_elem.set("distanceMeters", "999")
            fov_elem.set("eyeRadiusMeters", "0.6")
            
            brain_elem = ET.SubElement(human, "Brain")
            brain_elem.set("suppressionRecovery", "30.0")
            
            mobility_elem = ET.SubElement(human, "Mobility")
            
            move_speed = ET.SubElement(mobility_elem, "MoveSpeed")
            move_speed.set("min", "1.1")
            move_speed.set("defaultMetersPerSec", "2.28")
            move_speed.set("max", "10")
            
            turn_speed = ET.SubElement(mobility_elem, "TurnSpeed")
            turn_speed.set("min", "6")
            turn_speed.set("defaultMetersPerSec", "13")
            turn_speed.set("max", "20")
            
            equipment_elem = ET.SubElement(human, "Equipment")
            
            # Add to XML tree
            if not hasattr(self, 'unit_elem') or self.unit_elem is None:
                self.unit_elem = ET.Element("Entities")
                self.tree = ET.ElementTree(self.unit_elem)
            
            self.unit_elem.append(entity)
            if not hasattr(self, 'entities'):
                self.entities = []
            self.entities.append(entity)
            
            # Update combobox
            entity_names = [e.get("name", "Unnamed") for e in self.entities]
            self.entity_select_combobox['values'] = entity_names
            self.entity_select_combobox.set(values["name"])
            
            # Select the new entity
            self.current_entity = entity
            self.load_entity(entity)
            
            # Close dialog
            dialog.destroy()
            
            # Show success message
            messagebox.showinfo("Success", f"Created new entity: {values['name']}")
        
        # Add buttons at the bottom
        button_frame = ttk.Frame(dialog)
        button_frame.pack(side="bottom", fill="x", padx=10, pady=10)
        
        ttk.Button(button_frame, text="Create Entity", command=add_entity).pack(side="right", padx=5)
        ttk.Button(button_frame, text="Cancel", command=dialog.destroy).pack(side="right", padx=5)
        
        # Add initial RenderObject3D
        add_render_object()

    def delete_current_entity(self):
        """Delete the currently selected entity"""
        if not self.current_entity:
            messagebox.showerror("Error", "No entity selected")
            return
        
        entity_name = self.current_entity.get("name", "Unnamed")
        if not messagebox.askyesno("Confirm Delete", 
                                  f"Are you sure you want to delete entity '{entity_name}'?\nThis cannot be undone."):
            return
        
        try:
            # Remove from XML tree
            self.unit_elem.remove(self.current_entity)
            # Remove from entities list
            self.entities.remove(self.current_entity)
            
            # Update combobox
            entity_names = [e.get("name", "Unnamed") for e in self.entities]
            self.entity_select_combobox['values'] = entity_names
            
            # Select first entity if any remain
            if self.entities:
                self.entity_select_combobox.current(0)
                self.current_entity = self.entities[0]
                self.load_entity(self.current_entity)
            else:
                self.entity_select_combobox.set('')
                self.current_entity = None
                # Clear all entries
                for entries in [self.entity_attr_entries, self.human_attr_entries, 
                              self.id_attr_entries, self.fov_attr_entries, 
                              self.brain_attr_entries, self.move_speed_entries,
                              self.turn_speed_entries, self.physical_params_entries]:
                    for entry in entries.values():
                        entry.delete(0, tk.END)
                if self.equipment_entry:
                    self.equipment_entry.delete(0, tk.END)
            
            # Save changes to file
            xml_path = self.get_xml_path()
            if xml_path:
                self.tree.write(xml_path, encoding='utf-8', xml_declaration=True)
                messagebox.showinfo("Success", f"Entity '{entity_name}' deleted successfully")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to delete entity: {str(e)}")


def get_plugin_tab(parent):
    container = ttk.Frame(parent)
    editor = EntitiesEditor(container)
    editor.pack(fill="both", expand=True)
    return "Entities Editor", container 