import tkinter as tk
from tkinter import ttk, messagebox
import os
import xml.etree.ElementTree as ET
import json
from modules import config_editor_module

PLUGIN_TITLE = "Equipment Search"

# Define equipment types and remapping from scanner
EQUIPMENT_TYPES = [
    "Firearm", "Armor", "Grenade", "Utility",
    "Shield", "HelmetNVG", "Scope"
]

TYPE_REMAPPING = {
    "Lockpick": "Utility",
    "Crowbar": "Utility",
    "Tool": "Utility"
}

class EquipmentItem:
    def __init__(self):
        self.name = ""
        self.type = ""  # Firearm, Armor, etc.
        self.category = ""  # pistol, rifle, etc.
        self.inventory_slot = ""
        self.source_file = ""
        self.source_mod = ""  # vanilla or mod name
        self.bindings = []  # list of classes/units that can use it
        self.attributes = {}  # other attributes like damage, etc.

class EquipmentSearch(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.config = config_editor_module.load_config()
        self.equipment_items = []
        self.current_filters = {}
        
        # Create main layout frames
        self.create_search_frame()
        self.create_filters_frame()
        self.create_results_frame()
        
        # Initial scan of equipment
        self.scan_equipment()

    def create_search_frame(self):
        """Create the search bar and button"""
        search_frame = ttk.LabelFrame(self, text="Search")
        search_frame.pack(fill="x", padx=5, pady=5)
        
        # Search entry
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(search_frame, textvariable=self.search_var)
        self.search_entry.pack(side="left", fill="x", expand=True, padx=5, pady=5)
        
        # Search button
        self.search_btn = ttk.Button(search_frame, text="Search", command=self.perform_search)
        self.search_btn.pack(side="left", padx=5, pady=5)
        
        # Bind Enter key to search
        self.search_entry.bind('<Return>', lambda e: self.perform_search())

    def create_filters_frame(self):
        """Create the filters section"""
        filters_frame = ttk.LabelFrame(self, text="Filters")
        filters_frame.pack(fill="x", padx=5, pady=5)
        
        # Create filter sections - only Type and Mod
        self.create_filter_section(filters_frame, "Type", EQUIPMENT_TYPES)
        self.create_filter_section(filters_frame, "Mod", ["vanilla"])  # Will be populated during scan

    def create_filter_section(self, parent, name, values):
        """Create a collapsible filter section with checkboxes"""
        frame = ttk.Frame(parent)
        frame.pack(fill="x", padx=5, pady=2)
        
        # Create header with toggle button
        header_frame = ttk.Frame(frame)
        header_frame.pack(fill="x")
        
        toggle_btn = ttk.Button(header_frame, text="+", width=2)
        toggle_btn.pack(side="left")
        
        ttk.Label(header_frame, text=name).pack(side="left", padx=5)
        
        # Create content frame for checkboxes
        content_frame = ttk.Frame(frame)
        self.current_filters[name] = {
            'frame': content_frame,
            'visible': False,
            'values': {},
            'vars': {}
        }
        
        # Add checkboxes
        self.update_filter_values(name, values)
        
        # Configure toggle button
        toggle_btn.configure(command=lambda: self.toggle_filter_section(name))

    def update_filter_values(self, filter_name, values):
        """Update the values in a filter section"""
        filter_data = self.current_filters[filter_name]
        content_frame = filter_data['frame']
        
        # Clear existing checkboxes
        for widget in content_frame.winfo_children():
            widget.destroy()
        
        # Create new checkboxes
        filter_data['values'] = {}
        filter_data['vars'] = {}
        
        for value in sorted(values):
            var = tk.BooleanVar(value=True)
            cb = ttk.Checkbutton(content_frame, text=value, variable=var,
                               command=self.perform_search)
            cb.pack(anchor="w", padx=20)
            filter_data['values'][value] = cb
            filter_data['vars'][value] = var

    def toggle_filter_section(self, name):
        """Toggle visibility of a filter section"""
        filter_data = self.current_filters[name]
        if filter_data['visible']:
            filter_data['frame'].pack_forget()
        else:
            filter_data['frame'].pack(fill="x")
        filter_data['visible'] = not filter_data['visible']

    def create_results_frame(self):
        """Create the results treeview"""
        results_frame = ttk.LabelFrame(self, text="Results")
        results_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Create treeview with scrollbars
        self.tree = ttk.Treeview(results_frame, columns=("Name", "Type", "Category", "Slot", "Mod", "Bindings"),
                                show="headings")
        
        # Configure scrollbars
        vsb = ttk.Scrollbar(results_frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(results_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        # Configure columns
        self.tree.heading("Name", text="Name", command=lambda: self.sort_treeview("Name"))
        self.tree.heading("Type", text="Type", command=lambda: self.sort_treeview("Type"))
        self.tree.heading("Category", text="Category", command=lambda: self.sort_treeview("Category"))
        self.tree.heading("Slot", text="Slot", command=lambda: self.sort_treeview("Slot"))
        self.tree.heading("Mod", text="Mod", command=lambda: self.sort_treeview("Mod"))
        self.tree.heading("Bindings", text="Bindings", command=lambda: self.sort_treeview("Bindings"))
        
        # Set column widths
        self.tree.column("Name", width=150)
        self.tree.column("Type", width=100)
        self.tree.column("Category", width=100)
        self.tree.column("Slot", width=100)
        self.tree.column("Mod", width=100)
        self.tree.column("Bindings", width=200)
        
        # Grid layout
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        
        # Configure grid weights
        results_frame.grid_rowconfigure(0, weight=1)
        results_frame.grid_columnconfigure(0, weight=1)
        
        # Bind double-click event
        self.tree.bind('<Double-1>', self.show_item_details)

    def scan_equipment(self):
        """Scan equipment files from the game directory"""
        game_path = self.config.get("game_path", "")
        if not game_path or not os.path.exists(game_path):
            messagebox.showerror("Error", "Game path not configured or invalid")
            return
            
        equipment_path = os.path.join(game_path, "data", "equipment")
        mods_path = os.path.join(game_path, "mods")
        
        # Reset equipment items
        self.equipment_items = []
        
        # Track unique values for filters
        mods = {"vanilla"}
        
        # Scan vanilla equipment
        if os.path.exists(equipment_path):
            self.scan_directory(equipment_path, "vanilla")
        
        # Scan mod equipment
        if os.path.exists(mods_path):
            for mod in os.listdir(mods_path):
                mod_equipment_path = os.path.join(mods_path, mod, "equipment")
                if os.path.exists(mod_equipment_path):
                    self.scan_directory(mod_equipment_path, mod)
                    mods.add(mod)
        
        # Update filter sections
        self.update_filter_values("Mod", mods)
        
        # Perform initial search
        self.perform_search()

    def scan_directory(self, directory, mod_name):
        """Scan a directory for equipment files"""
        for root, _, files in os.walk(directory):
            for file in files:
                if file.endswith('.xml'):
                    try:
                        file_path = os.path.join(root, file)
                        tree = ET.parse(file_path)
                        root_elem = tree.getroot()
                        
                        if root_elem.tag == "Equipment":
                            self.process_equipment_file(root_elem, file_path, mod_name)
                    except ET.ParseError:
                        continue

    def process_equipment_file(self, root_elem, file_path, mod_name):
        """Process an equipment XML file"""
        # Process bindings first
        bindings = {}
        for bind in root_elem.findall(".//Bind"):
            self.process_binding(bind, bindings)
        
        # Process equipment items
        for elem in root_elem:
            if elem.tag == "Ammo":
                continue
                
            if elem.tag in EQUIPMENT_TYPES or elem.tag in TYPE_REMAPPING:
                item = self.create_equipment_item(elem, file_path, mod_name)
                if item:
                    # Apply bindings
                    if item.name in bindings:
                        item.bindings = list(bindings[item.name])
                    self.equipment_items.append(item)

    def process_binding(self, bind_elem, bindings):
        """Process a binding element"""
        # Format 1: <Bind eqp="X" to="Y"/>
        eqp = bind_elem.get("eqp")
        to = bind_elem.get("to")
        
        if eqp and to:
            if eqp not in bindings:
                bindings[eqp] = set()
            bindings[eqp].add(to)
            return
        
        # Format 2: <Bind eqp="X"><to name="Y"/></Bind>
        if eqp:
            for to_elem in bind_elem.findall("to"):
                to = to_elem.get("name")
                if to:
                    if eqp not in bindings:
                        bindings[eqp] = set()
                    bindings[eqp].add(to)
            return
        
        # Format 3: <Bind to="Y"><eqp name="X"/></Bind>
        if to:
            for eqp_elem in bind_elem.findall("eqp"):
                eqp = eqp_elem.get("name")
                if eqp:
                    if eqp not in bindings:
                        bindings[eqp] = set()
                    bindings[eqp].add(to)

    def create_equipment_item(self, elem, file_path, mod_name):
        """Create an EquipmentItem from an XML element"""
        item = EquipmentItem()
        item.name = elem.get("name", "")
        
        # Apply type remapping if needed
        original_type = elem.tag
        item.type = TYPE_REMAPPING.get(original_type, original_type)
        
        item.category = elem.get("category", "")
        item.inventory_slot = elem.get("inventoryBinding", "")
        item.source_file = file_path
        item.source_mod = mod_name
        
        # Extract additional attributes
        params_elem = elem.find("Params")
        if params_elem is not None:
            item.attributes = {key: value for key, value in params_elem.attrib.items()}
        
        return item

    def perform_search(self, event=None):
        """Perform the search with current filters"""
        # Clear current results
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Get search text
        search_text = self.search_var.get().lower()
        
        # Get active filters
        active_filters = {
            'Type': [k for k, v in self.current_filters['Type']['vars'].items() if v.get()],
            'Mod': [k for k, v in self.current_filters['Mod']['vars'].items() if v.get()]
        }
        
        # Filter and display items
        for item in self.equipment_items:
            # Check if item matches filters
            if item.type not in active_filters['Type']:
                continue
            if item.source_mod not in active_filters['Mod']:
                continue
            
            # Check if item matches search text
            if search_text and search_text not in item.name.lower():
                continue
            
            # Add item to treeview
            self.tree.insert("", "end", values=(
                item.name,
                item.type,
                item.category or "",
                item.inventory_slot or "",
                item.source_mod,
                ", ".join(item.bindings) if item.bindings else ""
            ))

    def sort_treeview(self, col):
        """Sort treeview by column"""
        # Get all items
        items = [(self.tree.set(item, col), item) for item in self.tree.get_children("")]
        
        # Sort items
        items.sort()
        
        # Rearrange items in sorted positions
        for index, (_, item) in enumerate(items):
            self.tree.move(item, "", index)

    def show_item_details(self, event):
        """Show detailed information about the selected item"""
        selection = self.tree.selection()
        if not selection:
            return
            
        # Get selected item values
        values = self.tree.item(selection[0])['values']
        name = values[0]
        
        # Find the corresponding equipment item
        for item in self.equipment_items:
            if item.name == name:
                # Create details window
                details = tk.Toplevel(self)
                details.title(f"Equipment Details - {name}")
                details.geometry("800x600")
                
                # Create text widget with scrollbar
                frame = ttk.Frame(details)
                frame.pack(fill="both", expand=True)
                
                text = tk.Text(frame, wrap="word", padx=10, pady=10)
                scrollbar = ttk.Scrollbar(frame, orient="vertical", command=text.yview)
                text.configure(yscrollcommand=scrollbar.set)
                
                text.pack(side="left", fill="both", expand=True)
                scrollbar.pack(side="right", fill="y")
                
                # Insert basic details with formatting
                text.tag_configure("header", font=("TkDefaultFont", 10, "bold"))
                text.tag_configure("subheader", font=("TkDefaultFont", 9, "bold"))
                text.tag_configure("value", font=("TkDefaultFont", 9))
                
                # Basic Info Section
                text.insert("end", "Basic Information\n", "header")
                text.insert("end", "-" * 50 + "\n")
                text.insert("end", f"Name: {item.name}\n", "value")
                text.insert("end", f"Type: {item.type}\n", "value")
                text.insert("end", f"Category: {item.category}\n", "value")
                text.insert("end", f"Inventory Slot: {item.inventory_slot}\n", "value")
                text.insert("end", f"Source Mod: {item.source_mod}\n", "value")
                text.insert("end", "\n")
                
                # Try to parse the source XML for detailed stats
                try:
                    tree = ET.parse(item.source_file)
                    root = tree.getroot()
                    
                    # Find the equipment element
                    for elem in root.findall(f".//{item.type}[@name='{item.name}']"):
                        # Stats Section
                        text.insert("end", "Equipment Stats\n", "header")
                        text.insert("end", "-" * 50 + "\n")
                        
                        # Direct attributes
                        for key, value in elem.attrib.items():
                            if key != "name":  # Skip name as it's already shown
                                text.insert("end", f"{key}: {value}\n", "value")
                        
                        # Parameters section
                        params = elem.find("Params")
                        if params is not None:
                            text.insert("end", "\nParameters\n", "subheader")
                            text.insert("end", "-" * 25 + "\n")
                            for key, value in sorted(params.attrib.items()):
                                text.insert("end", f"{key}: {value}\n", "value")
                        
                        # Ammo section
                        ammo = elem.find("Ammo")
                        if ammo is not None:
                            text.insert("end", "\nAmmo Information\n", "subheader")
                            text.insert("end", "-" * 25 + "\n")
                            for key, value in sorted(ammo.attrib.items()):
                                text.insert("end", f"{key}: {value}\n", "value")
                        
                        # Firing section
                        firing = elem.find("Firing")
                        if firing is not None:
                            text.insert("end", "\nFiring Characteristics\n", "subheader")
                            text.insert("end", "-" * 25 + "\n")
                            for key, value in sorted(firing.attrib.items()):
                                text.insert("end", f"{key}: {value}\n", "value")
                        
                        # Protection section (for armor)
                        protection = elem.find("Protection")
                        if protection is not None:
                            text.insert("end", "\nProtection Stats\n", "subheader")
                            text.insert("end", "-" * 25 + "\n")
                            for key, value in sorted(protection.attrib.items()):
                                text.insert("end", f"{key}: {value}\n", "value")
                                
                        # NVG section (for HelmetNVG)
                        if item.type == "HelmetNVG":
                            text.insert("end", "\nNVG Characteristics\n", "subheader")
                            text.insert("end", "-" * 25 + "\n")
                            
                            # Get mobility modifiers
                            mobility = elem.find("MobilityModifiers")
                            if mobility is not None:
                                text.insert("end", "Mobility Modifiers:\n", "value")
                                text.insert("end", f"  Move Speed: {mobility.get('moveSpeedModifierPercent', 'N/A')}%\n", "value")
                                text.insert("end", f"  Turn Speed: {mobility.get('turnSpeedModifierPercent', 'N/A')}%\n", "value")
                                text.insert("end", "\n", "value")
                            
                            # Get FOV parameters from ModifiableParams
                            modifiable_params = elem.find("ModifiableParams")
                            if modifiable_params is not None:
                                text.insert("end", "FOV Parameters:\n", "value")
                                text.insert("end", f"  FOV Degrees: {modifiable_params.get('fovDegrees', 'N/A')}\n", "value")
                                text.insert("end", f"  FOV Radius (meters): {modifiable_params.get('fovRadiusMeters', 'N/A')}\n", "value")
                                text.insert("end", f"  FOV Range (meters): {modifiable_params.get('fovRangeMeters', 'N/A')}\n", "value")
                            
                except Exception as e:
                    text.insert("end", f"\nError loading detailed stats: {str(e)}\n", "value")
                
                # Bindings Section
                if item.bindings:
                    text.insert("end", "\nUnit/Class Bindings\n", "header")
                    text.insert("end", "-" * 50 + "\n")
                    for binding in sorted(item.bindings):
                        text.insert("end", f"- {binding}\n", "value")
                
                # Make text widget read-only
                text.configure(state="disabled")
                
                # Center the window
                details.update_idletasks()
                width = details.winfo_width()
                height = details.winfo_height()
                x = (details.winfo_screenwidth() // 2) - (width // 2)
                y = (details.winfo_screenheight() // 2) - (height // 2)
                details.geometry(f'+{x}+{y}')
                break

def get_plugin_tab(notebook):
    """Create and return the equipment search tab"""
    return PLUGIN_TITLE, EquipmentSearch(notebook) 