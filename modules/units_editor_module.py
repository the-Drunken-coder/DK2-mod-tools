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
        self.class_entries = []       # List of tuples: (class_elem, {field: entry}, remove_btn)
        self.trooper_rank_entries = []  # List of tuples: (rank_elem, {field: entry})
        self.rank_entries = []          # List of tuples: (rank_elem, {field: entry})
        self.config = config_editor_module.load_config()
        
        # Create main frame to hold both scrollbars
        self.main_frame = ttk.Frame(self)
        self.main_frame.pack(fill="both", expand=True)
        
        # Create canvas with both scrollbars
        self.canvas = tk.Canvas(self.main_frame)
        self.v_scrollbar = ttk.Scrollbar(self.main_frame, orient="vertical", command=self.canvas.yview)
        self.h_scrollbar = ttk.Scrollbar(self.main_frame, orient="horizontal", command=self.canvas.xview)
        self.content_frame = ttk.Frame(self.canvas)
        
        # Configure the canvas
        self.canvas.configure(yscrollcommand=self.v_scrollbar.set, xscrollcommand=self.h_scrollbar.set)
        
        # Grid layout for scrollbars and canvas
        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.v_scrollbar.grid(row=0, column=1, sticky="ns")
        self.h_scrollbar.grid(row=1, column=0, sticky="ew")
        
        # Configure grid weights
        self.main_frame.grid_rowconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)
        
        # Create a window in the canvas for the content frame
        self.canvas_window = self.canvas.create_window((0, 0), window=self.content_frame, anchor="nw")
        
        # Create bottom frame for save button
        self.bottom_frame = ttk.Frame(self)
        self.bottom_frame.pack(fill="x", side="bottom", padx=5, pady=5)
        
        # Create save button in the bottom frame
        self.save_btn = ttk.Button(self.bottom_frame, text="Save Changes", command=self.save_changes)
        self.save_btn.pack(side="right", padx=5)
        
        # Bind events for scrolling
        self.content_frame.bind("<Configure>", self._on_frame_configure)
        self.canvas.bind("<Configure>", self._on_canvas_configure)
        
        # Bind mouse wheel
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind_all("<Shift-MouseWheel>", self._on_shift_mousewheel)
        
        self.load_xml()
        self.build_ui()

    def _on_frame_configure(self, event=None):
        """Reset the scroll region to encompass the inner frame"""
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
    
    def _on_canvas_configure(self, event):
        """When the canvas is resized, resize the inner frame to match"""
        # Ensure minimum width for content
        min_width = max(self.content_frame.winfo_reqwidth(), event.width)
        self.canvas.itemconfig(self.canvas_window, width=min_width)
    
    def _on_mousewheel(self, event):
        """Handle vertical mouse wheel scrolling"""
        self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")

    def _on_shift_mousewheel(self, event):
        """Handle horizontal mouse wheel scrolling with Shift key"""
        self.canvas.xview_scroll(int(-1*(event.delta/120)), "units")

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

    def remove_class(self, class_elem, entries, remove_btn, row_index):
        """Remove a class from both the XML and UI"""
        try:
            # Remove from XML
            classes_elem = self.unit_elem.find('Classes')
            if classes_elem is not None:
                # Find the class element by matching attributes
                for elem in classes_elem.findall('Class'):
                    if all(elem.get(key) == class_elem.get(key) for key in class_elem.keys()):
                        classes_elem.remove(elem)
                        break
            
            # Remove from UI
            for entry in entries.values():
                entry.destroy()
            remove_btn.destroy()
            
            # Remove from class_entries
            self.class_entries = [(ce, e, b) for ce, e, b in self.class_entries 
                                if not all(ce.get(key) == class_elem.get(key) for key in class_elem.keys())]
            
            # Reposition remaining rows
            classes_frame = [w for w in self.content_frame.winfo_children() 
                           if isinstance(w, ttk.LabelFrame) and w.cget("text") == "Classes"][0]
            
            # Update row positions
            for i, (_, entries, btn) in enumerate(self.class_entries):
                new_row = i + 2  # Account for header and button rows
                for j, entry in enumerate(entries.values()):
                    entry.grid(row=new_row, column=j, sticky="ew")
                btn.grid(row=new_row, column=len(entries), sticky="ew")
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to remove class: {str(e)}")
            return

    def create_new_class(self):
        """Create a new trooper class"""
        # Create dialog window
        dialog = tk.Toplevel(self)
        dialog.title("Create New Class")
        dialog.geometry("600x400")
        
        # Center the dialog
        dialog.update_idletasks()
        screen_width = dialog.winfo_screenwidth()
        screen_height = dialog.winfo_screenheight()
        x = (screen_width - 600) // 2
        y = (screen_height - 400) // 2
        dialog.geometry(f"+{x}+{y}")
        
        # Create form fields
        fields = {
            "name": "Class ID (e.g. AssaultClass)",
            "nameUI": "Display Name (e.g. @unit_assault_name)",
            "description": "Description (e.g. @unit_assault_desc)",
            "supply": "Supply Cost",
            "iconTex": "Icon Path (e.g. data/textures/gui/deploy/class_icon.dds)",
            "upgrades": "Upgrades (comma separated)",
            "maxUpgradeable": "Max Upgrades Allowed"
        }
        
        entries = {}
        row = 0
        for field, label in fields.items():
            ttk.Label(dialog, text=label).grid(row=row, column=0, sticky="w", padx=5, pady=2)
            entry = ttk.Entry(dialog, width=50)
            entry.grid(row=row, column=1, sticky="w", padx=5, pady=2)
            entries[field] = entry
            row += 1
            
            # Add default values
            if field == "supply":
                entry.insert(0, "100")
            elif field == "maxUpgradeable":
                entry.insert(0, "2")
            elif field == "upgrades":
                entry.insert(0, "BH_Defence1, BH_Offence1, BH_Defence2, BH_Offence2")
        
        def add_class():
            # Get values from entries
            values = {field: entry.get().strip() for field, entry in entries.items()}
            
            # Validate required fields
            if not values["name"] or not values["nameUI"]:
                messagebox.showerror("Error", "Class ID and Display Name are required")
                return
            
            # Find Classes element or create it
            classes_elem = self.unit_elem.find('Classes')
            if classes_elem is None:
                classes_elem = ET.SubElement(self.unit_elem, 'Classes')
            
            # Create new Class element
            class_elem = ET.SubElement(classes_elem, 'Class')
            for field, value in values.items():
                if value:  # Only set non-empty values
                    class_elem.set(field, value)
            
            # Add to UI
            entry_row = {}
            headers = ["name", "nameUI", "description", "supply", "iconTex", "upgrades", "maxUpgradeable"]
            classes_frame = [w for w in self.content_frame.winfo_children() if isinstance(w, ttk.LabelFrame) and w.cget("text") == "Classes"][0]
            
            # Calculate the correct row index - add 2 to account for the button row and header row
            row_index = len(self.class_entries) + 2
            
            # Use the same column widths as the main UI
            col_widths = {
                "name": 20,
                "nameUI": 20,
                "description": 30,
                "supply": 10,
                "iconTex": 40,
                "upgrades": 40,
                "maxUpgradeable": 15
            }
            
            for j, field in enumerate(headers):
                entry = ttk.Entry(classes_frame, width=col_widths[field])
                entry.grid(row=row_index, column=j, padx=2, pady=2, sticky="ew")
                entry.insert(0, values.get(field, ""))
                entry_row[field] = entry
            
            # Add remove button
            remove_btn = ttk.Button(classes_frame, text="Remove", width=8)
            remove_btn.grid(row=row_index, column=len(headers), padx=2, pady=2)
            remove_btn.configure(command=lambda: self.remove_class(class_elem, entry_row, remove_btn, row_index))
            
            self.class_entries.append((class_elem, entry_row, remove_btn))
            
            # Close dialog
            dialog.destroy()
            
            # Show success message
            messagebox.showinfo("Success", f"Created new class: {values['name']}")
        
        # Add buttons
        button_frame = ttk.Frame(dialog)
        button_frame.grid(row=row, column=0, columnspan=2, pady=20)
        
        ttk.Button(button_frame, text="Create Class", command=add_class).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Cancel", command=dialog.destroy).pack(side="left", padx=5)

    def remove_rank(self, rank_elem, entries, remove_btn, is_trooper_rank=False):
        """Remove a rank from both the XML and UI"""
        try:
            # Remove from XML
            ranks_elem = self.unit_elem.find('TrooperRanks' if is_trooper_rank else 'Ranks')
            if ranks_elem is not None:
                # Find and remove the rank element
                for elem in ranks_elem.findall('Rank'):
                    if all(elem.get(key) == rank_elem.get(key) for key in rank_elem.keys()):
                        ranks_elem.remove(elem)
                        break
            
            # Remove from UI
            for entry in entries.values():
                entry.destroy()
            remove_btn.destroy()
            
            # Remove from entries list
            if is_trooper_rank:
                self.trooper_rank_entries = [(re, e) for re, e in self.trooper_rank_entries 
                                           if not all(re.get(key) == rank_elem.get(key) for key in rank_elem.keys())]
            else:
                self.rank_entries = [(re, e) for re, e in self.rank_entries 
                                   if not all(re.get(key) == rank_elem.get(key) for key in rank_elem.keys())]
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to remove rank: {str(e)}")
            return

    def create_new_rank(self, is_trooper_rank=False):
        """Create a new rank"""
        dialog = tk.Toplevel(self)
        dialog.title("Create New " + ("Trooper Rank" if is_trooper_rank else "Rank"))
        dialog.geometry("500x300")
        
        # Center the dialog
        dialog.update_idletasks()
        screen_width = dialog.winfo_screenwidth()
        screen_height = dialog.winfo_screenheight()
        x = (screen_width - 500) // 2
        y = (screen_height - 300) // 2
        dialog.geometry(f"+{x}+{y}")
        
        # Create form fields
        fields = {
            "xpNeeded": "XP Required",
            "badgeTex": "Badge Texture Path"
        }
        if is_trooper_rank:
            fields["name"] = "Name (e.g. @agent_rank_0)"
        
        entries = {}
        row = 0
        for field, label in fields.items():
            ttk.Label(dialog, text=label).grid(row=row, column=0, sticky="w", padx=5, pady=2)
            entry = ttk.Entry(dialog, width=50)
            entry.grid(row=row, column=1, sticky="w", padx=5, pady=2)
            entries[field] = entry
            
            # Add default values
            if field == "xpNeeded":
                entry.insert(0, "0")
            elif field == "badgeTex" and is_trooper_rank:
                entry.insert(0, "data/textures/gui/customization/rank_01.dds")
            row += 1
        
        def add_rank():
            # Get values from entries
            values = {field: entry.get().strip() for field, entry in entries.items()}
            
            # Validate required fields
            if not values["xpNeeded"]:
                messagebox.showerror("Error", "XP Required is required")
                return
            
            # Find Ranks element or create it
            ranks_elem = self.unit_elem.find('TrooperRanks' if is_trooper_rank else 'Ranks')
            if ranks_elem is None:
                ranks_elem = ET.SubElement(self.unit_elem, 'TrooperRanks' if is_trooper_rank else 'Ranks')
            
            # Create new Rank element
            rank_elem = ET.SubElement(ranks_elem, 'Rank')
            for field, value in values.items():
                if value:  # Only set non-empty values
                    rank_elem.set(field, value)
            
            # Add to UI
            entry_row = {}
            frame = [w for w in self.content_frame.winfo_children() 
                    if isinstance(w, ttk.LabelFrame) and w.cget("text") == ("Trooper Ranks" if is_trooper_rank else "Ranks")][0]
            
            # Calculate row index
            row_index = len(self.trooper_rank_entries if is_trooper_rank else self.rank_entries) + 1
            
            headers = ["name", "xpNeeded", "badgeTex"] if is_trooper_rank else ["xpNeeded", "badgeTex"]
            for j, field in enumerate(headers):
                entry = ttk.Entry(frame, width=30)
                entry.grid(row=row_index, column=j, padx=2, pady=2, sticky="ew")
                entry.insert(0, values.get(field, ""))
                entry_row[field] = entry
            
            # Add remove button
            remove_btn = ttk.Button(frame, text="Remove", width=8)
            remove_btn.grid(row=row_index, column=len(headers), padx=2, pady=2)
            remove_btn.configure(command=lambda: self.remove_rank(rank_elem, entry_row, remove_btn, is_trooper_rank))
            
            if is_trooper_rank:
                self.trooper_rank_entries.append((rank_elem, entry_row))
            else:
                self.rank_entries.append((rank_elem, entry_row))
            
            dialog.destroy()
            messagebox.showinfo("Success", f"Created new {'trooper ' if is_trooper_rank else ''}rank")
        
        # Add buttons
        button_frame = ttk.Frame(dialog)
        button_frame.grid(row=row, column=0, columnspan=2, pady=20)
        
        ttk.Button(button_frame, text="Create Rank", command=add_rank).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Cancel", command=dialog.destroy).pack(side="left", padx=5)

    def build_ui(self):
        # Check if unit_elem is loaded
        if self.unit_elem is None:
            error_label = ttk.Label(self.content_frame, text="Error: XML file is invalid. <Unit> element not found.")
            error_label.pack(fill='both', expand=True, padx=10, pady=10)
            return
        
        # Section: Unit Attributes
        unit_attr_frame = ttk.LabelFrame(self.content_frame, text="Unit Attributes")
        unit_attr_frame.pack(fill="x", padx=5, pady=5)
        
        # List of attributes to edit
        fields = ["name", "nameUI", "description", "flagTex", "flagColor", "rndNameEntry", "voicepack", "incapacitationChance", "incapacitationChanceCrit"]
        for i, field in enumerate(fields):
            ttk.Label(unit_attr_frame, text=field).grid(row=i, column=0, sticky="w", padx=5, pady=2)
            entry = ttk.Entry(unit_attr_frame, width=80)
            entry.grid(row=i, column=1, sticky="w", padx=5, pady=2)
            entry.insert(0, self.unit_elem.get(field, ''))
            self.unit_attr_entries[field] = entry
        
        # Section: Classes with Add Class button
        classes_frame = ttk.LabelFrame(self.content_frame, text="Classes")
        classes_frame.pack(fill="x", padx=5, pady=5)
        
        # Add Class button at the top of Classes section
        add_class_btn = ttk.Button(classes_frame, text="Add New Class", command=self.create_new_class)
        add_class_btn.grid(row=0, column=0, columnspan=8, pady=(0, 10))
        
        classes_elem = self.unit_elem.find('Classes')
        if classes_elem is not None:
            headers = ["name", "nameUI", "description", "supply", "iconTex", "upgrades", "maxUpgradeable"]
            # Set column widths based on content
            col_widths = {
                "name": 20,
                "nameUI": 20,
                "description": 30,
                "supply": 10,
                "iconTex": 40,
                "upgrades": 40,
                "maxUpgradeable": 15
            }
            
            # Header row
            for j, header in enumerate(headers):
                ttk.Label(classes_frame, text=header, relief="groove").grid(
                    row=1, column=j, padx=2, pady=2, sticky="nsew"
                )
                classes_frame.grid_columnconfigure(j, weight=1, minsize=col_widths[header]*7)  # Adjust multiplier as needed
            
            # Add header for remove button column
            ttk.Label(classes_frame, text="Actions", relief="groove").grid(
                row=1, column=len(headers), padx=2, pady=2, sticky="nsew"
            )
            
            row_index = 2
            for class_elem in classes_elem.findall('Class'):
                entry_row = {}
                for j, field in enumerate(headers):
                    entry = ttk.Entry(classes_frame, width=col_widths[field])
                    entry.grid(row=row_index, column=j, padx=2, pady=2, sticky="ew")
                    entry.insert(0, class_elem.get(field, ''))
                    entry_row[field] = entry
                
                # Add remove button for existing classes
                remove_btn = ttk.Button(classes_frame, text="Remove", width=8)
                remove_btn.grid(row=row_index, column=len(headers), padx=2, pady=2)
                remove_btn.configure(command=lambda ce=class_elem, er=entry_row, rb=remove_btn, ri=row_index: 
                                  self.remove_class(ce, er, rb, ri))
                
                self.class_entries.append((class_elem, entry_row, remove_btn))
                row_index += 1
        
        # Section: Trooper Ranks
        trooper_ranks_frame = ttk.LabelFrame(self.content_frame, text="Trooper Ranks")
        trooper_ranks_frame.pack(fill="x", padx=5, pady=5)
        
        # Add Trooper Rank button
        add_trooper_rank_btn = ttk.Button(trooper_ranks_frame, text="Add New Trooper Rank", 
                                        command=lambda: self.create_new_rank(True))
        add_trooper_rank_btn.grid(row=0, column=0, columnspan=4, pady=(0, 10))
        
        headers = ["name", "xpNeeded", "badgeTex"]
        # Set column widths based on content
        col_widths = {
            "name": 15,
            "xpNeeded": 8,
            "badgeTex": 35
        }
        
        for j, header in enumerate(headers):
            ttk.Label(trooper_ranks_frame, text=header, relief="groove").grid(
                row=1, column=j, padx=2, pady=2, sticky="nsew"
            )
            # Configure column to not expand and use exact width
            trooper_ranks_frame.grid_columnconfigure(j, weight=0, minsize=col_widths[header]*7)
        
        # Add header for remove button column
        ttk.Label(trooper_ranks_frame, text="Actions", relief="groove").grid(
            row=1, column=len(headers), padx=2, pady=2, sticky="nsew"
        )
        trooper_ranks_frame.grid_columnconfigure(len(headers), weight=0, minsize=60)
        
        row_index = 2
        trooper_ranks_elem = self.unit_elem.find('TrooperRanks')
        if trooper_ranks_elem is not None:
            for rank_elem in trooper_ranks_elem.findall('Rank'):
                entry_row = {}
                for j, field in enumerate(headers):
                    entry = ttk.Entry(trooper_ranks_frame, width=col_widths[field])
                    entry.grid(row=row_index, column=j, padx=2, pady=2, sticky="w")
                    entry.insert(0, rank_elem.get(field, ''))
                    entry_row[field] = entry
                
                # Add remove button
                remove_btn = ttk.Button(trooper_ranks_frame, text="Remove", width=8)
                remove_btn.grid(row=row_index, column=len(headers), padx=2, pady=2)
                remove_btn.configure(command=lambda re=rank_elem, er=entry_row, rb=remove_btn: 
                                  self.remove_rank(re, er, rb, True))
                
                self.trooper_rank_entries.append((rank_elem, entry_row))
                row_index += 1
        
        # Section: Ranks
        ranks_frame = ttk.LabelFrame(self.content_frame, text="Ranks")
        ranks_frame.pack(fill="x", padx=5, pady=5)
        
        # Add Rank button
        add_rank_btn = ttk.Button(ranks_frame, text="Add New Rank", 
                                command=lambda: self.create_new_rank(False))
        add_rank_btn.grid(row=0, column=0, columnspan=3, pady=(0, 10))
        
        headers = ["xpNeeded", "badgeTex"]
        # Set column widths for ranks
        col_widths = {
            "xpNeeded": 8,
            "badgeTex": 35
        }
        
        for j, header in enumerate(headers):
            ttk.Label(ranks_frame, text=header, relief="groove").grid(
                row=1, column=j, padx=2, pady=2, sticky="nsew"
            )
            # Configure column to not expand and use exact width
            ranks_frame.grid_columnconfigure(j, weight=0, minsize=col_widths[header]*7)
        
        # Add header for remove button column
        ttk.Label(ranks_frame, text="Actions", relief="groove").grid(
            row=1, column=len(headers), padx=2, pady=2, sticky="nsew"
        )
        ranks_frame.grid_columnconfigure(len(headers), weight=0, minsize=60)
        
        row_index = 2
        ranks_elem = self.unit_elem.find('Ranks')
        if ranks_elem is not None:
            for rank_elem in ranks_elem.findall('Rank'):
                entry_row = {}
                for j, field in enumerate(headers):
                    entry = ttk.Entry(ranks_frame, width=col_widths[field])
                    entry.grid(row=row_index, column=j, padx=2, pady=2, sticky="w")
                    entry.insert(0, rank_elem.get(field, ''))
                    entry_row[field] = entry
                
                # Add remove button
                remove_btn = ttk.Button(ranks_frame, text="Remove", width=8)
                remove_btn.grid(row=row_index, column=len(headers), padx=2, pady=2)
                remove_btn.configure(command=lambda re=rank_elem, er=entry_row, rb=remove_btn: 
                                  self.remove_rank(re, er, rb, False))
                
                self.rank_entries.append((rank_elem, entry_row))
                row_index += 1

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
            # Store existing numSlots values before clearing
            existing_slots = {}
            for class_elem in classes_elem.findall('Class'):
                name = class_elem.get('name')
                num_slots = class_elem.get('numSlots')
                if name and num_slots:
                    existing_slots[name] = num_slots
            
            # Clear existing classes to rewrite them with proper formatting
            for child in list(classes_elem):
                classes_elem.remove(child)
            
            # Add classes back with proper formatting
            for class_elem, entries, _ in self.class_entries:
                new_class = ET.SubElement(classes_elem, 'Class')
                # Build ordered attributes string
                attrs = {}
                # Order attributes in the preferred order
                ordered_fields = ["name", "nameUI", "description", "supply", "iconTex", "upgrades", "maxUpgradeable"]
                for field in ordered_fields:
                    if field in entries:
                        value = entries[field].get().strip()
                        if value:  # Only add non-empty values
                            attrs[field] = value
                
                # Set attributes all at once for consistent ordering
                for field, value in attrs.items():
                    new_class.set(field, value)
                
                # Restore the original numSlots value if it existed
                if attrs.get('name') in existing_slots:
                    new_class.set('numSlots', existing_slots[attrs['name']])
                elif class_elem.get('numSlots'):  # If not in existing_slots but class_elem has numSlots, preserve it
                    new_class.set('numSlots', class_elem.get('numSlots'))
                
                # Add proper indentation
                new_class.tail = "\n            "  # Matches vanilla indentation
        
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
        
        # Write back to XML file with proper formatting
        try:
            # Format the entire XML with proper indentation
            ET.indent(self.tree, space="    ")
            self.tree.write(xml_path, encoding='utf-8', xml_declaration=True)
            messagebox.showinfo("Success", "XML file updated successfully.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to write XML: {e}")

def get_plugin_tab(notebook):
    """Create and return the units editor tab"""
    return PLUGIN_TITLE, UnitsEditor(notebook) 