import tkinter as tk
from tkinter import ttk, messagebox
import xml.etree.ElementTree as ET
import os
from pathlib import Path
from modules import config_editor_module
from modding_tool import get_equipment_file, get_unit_file, mod_files

PLUGIN_TITLE = "Equipment & Bindings"
ENABLE_LOGGING = True  # Toggle module logging

def log(message):
    """Module specific logging function"""
    if ENABLE_LOGGING:
        print(f"[EquipmentBindingEditor] {message}")

class EquipmentBindingEditor(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.tree = None
        self.bindings = []
        self.binding_widgets = []
        self.config = config_editor_module.load_config()
        self.clipboard = None  # Store copied binding
        
        # Get mod path and initialize ModFiles
        mod_path = self.get_mod_path()
        if mod_path:
            mod_files.mod_path = mod_path
            mod_files.scan_mod_directory()
            self.faction_name = mod_files.get_mod_name()
            log(f"Initialized with faction name: {self.faction_name}")
        else:
            self.faction_name = "FACTION"
            log("No mod path, using default faction name: FACTION")
            
        self.binding_sources = {
            "equipment": {"path": "equipment/binds.xml", "xpath": ".//Bind"}
        }
        self.build_ui()
        self.load_all_bindings()

    def get_mod_path(self):
        """Get the current mod path based on configuration"""
        mod_path = self.config.get("mod_path", "")
        current_mod = self.config.get("last_used_mod", "")
        if not mod_path or not current_mod:
            log(f"Invalid configuration - mod_path: {mod_path}, current_mod: {current_mod}")
            return None
        full_path = os.path.normpath(os.path.join(mod_path, current_mod))
        log(f"Using mod path: {full_path}")
        return full_path

    def get_equipment_xml_path(self):
        """Get the equipment binds XML file path"""
        mod_path = self.get_mod_path()
        if not mod_path:
            return None
        return get_equipment_file(mod_path)

    def get_unit_xml_path(self):
        """Get the unit XML file path"""
        mod_path = self.get_mod_path()
        if not mod_path:
            return None
        return get_unit_file(mod_path)

    def build_ui(self):
        # Create main container with tabs
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True)

        # Create tabs for different binding views
        self.create_by_class_tab()
        self.create_by_source_tab()
        self.create_summary_tab()

        # Button container
        button_frame = ttk.Frame(self)
        button_frame.pack(pady=5)

        # Organize button
        self.btn_organize = ttk.Button(button_frame, text="Organize Bindings", command=self.organize_bindings)
        self.btn_organize.pack(side="left", padx=5)

        # Global save button
        self.btn_save = ttk.Button(button_frame, text="Save All Changes", command=self.save_all_changes)
        self.btn_save.pack(side="left", padx=5)

    def create_scrollable_frame(self, parent):
        canvas = tk.Canvas(parent)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        return scrollable_frame

    def create_by_class_tab(self):
        class_tab = ttk.Frame(self.notebook)
        self.class_frame = self.create_scrollable_frame(class_tab)
        self.notebook.add(class_tab, text="By Class")

    def create_by_source_tab(self):
        source_tab = ttk.Frame(self.notebook)
        self.source_frame = self.create_scrollable_frame(source_tab)
        self.notebook.add(source_tab, text="By Source")

    def create_summary_tab(self):
        summary_tab = ttk.Frame(self.notebook)
        self.summary_frame = self.create_scrollable_frame(summary_tab)
        self.notebook.add(summary_tab, text="Summary")

    def get_available_classes(self):
        """Get available classes from the unit file"""
        from modding_tool import mod_files
        # Only scan if the path has changed
        if mod_files.mod_path != self.get_mod_path():
            mod_files.mod_path = self.get_mod_path()
            mod_files.scan_mod_directory()
            log("Rescanned mod directory due to path change")
        classes = mod_files.get_available_classes()
        log(f"Available classes: {classes}")
        return classes

    def load_xml_file(self, file_path, xpath):
        """Load XML file and return bindings"""
        try:
            mod_path = self.get_mod_path()
            if not mod_path:
                messagebox.showerror("Error", "No mod path configured")
                return []
            
            # Get the appropriate XML path based on the source
            if file_path == "equipment/binds.xml":
                full_path = get_equipment_file(mod_path)
            elif file_path == "units/unit.xml":
                full_path = get_unit_file(mod_path)
            else:
                full_path = os.path.normpath(os.path.join(mod_path, file_path))
            
            if not full_path or not os.path.exists(full_path):
                messagebox.showerror("Error", f"File not found: {os.path.basename(file_path)}\nPlease create the file first.")
                return []
            
            tree = ET.parse(full_path)
            root = tree.getroot()
            
            # Find all elements matching the XPath
            elements = root.findall(xpath)
            return elements
            
        except ET.ParseError as e:
            messagebox.showerror("XML Error", f"Failed to parse {os.path.basename(file_path)}: {str(e)}")
            return []
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load {os.path.basename(file_path)}: {str(e)}")
            return []

    def load_all_bindings(self):
        """Load all bindings from XML files"""
        log("Loading all bindings...")
        
        # Store old widget references before clearing
        old_widgets = self.binding_widgets.copy()
        
        self.all_bindings = {}
        self.binding_trees = {}
        self.binding_widgets = []  # Clear widget references
        
        # Load bindings from equipment source
        log("Loading bindings from equipment...")
        elements = self.load_xml_file(self.binding_sources["equipment"]["path"], 
                                    self.binding_sources["equipment"]["xpath"])
        if elements:
            log(f"Found {len(elements)} bindings in equipment")
            self.all_bindings["equipment"] = elements
            
            try:
                file_path = get_equipment_file(self.get_mod_path())
                if os.path.exists(file_path):
                    log(f"Loading equipment tree from: {os.path.basename(file_path)}")
                    tree = ET.parse(file_path)
                    self.binding_trees["equipment"] = tree
            except Exception as e:
                log(f"Warning: Failed to load equipment tree: {e}")
        else:
            log("No bindings found in equipment")
            self.all_bindings["equipment"] = []

        # Clear existing UI - properly destroy all widgets
        log("Clearing old widgets...")
        for widget in old_widgets:
            if "eqp_entry" in widget:
                widget["eqp_entry"].destroy()
            if "to_entry" in widget:
                widget["to_entry"].destroy()
            if "entries" in widget:
                for entry in widget["entries"].values():
                    entry.destroy()

        for child in self.class_frame.winfo_children():
            child.destroy()
        for child in self.source_frame.winfo_children():
            child.destroy()
        for child in self.summary_frame.winfo_children():
            child.destroy()

        # Force update to ensure all widgets are properly destroyed
        self.update_idletasks()

        log("Rebuilding views...")
        self.build_class_view()
        self.build_source_view()
        self.build_summary_view()

    def is_faction_binding(self, binding):
        """Check if a binding is a faction-level binding"""
        binding_to = binding.get("to", "")
        # Check both the current faction name and "FACTION" as fallback
        return binding_to == self.faction_name

    def get_effective_bindings(self, cls):
        """Get all bindings that apply to a class, including faction-level bindings"""
        effective_bindings = []
        for source, bindings in self.all_bindings.items():
            for binding in bindings:
                binding_to = binding.get("to", "")
                
                # Include bindings in these cases:
                # 1. We're viewing FACTION and it's a faction binding
                # 2. It's a direct class binding
                # 3. It's a faction-wide binding that applies to this class
                if (cls == "FACTION" and binding_to == self.faction_name) or \
                   (binding_to == cls) or \
                   (binding_to == self.faction_name and cls != "FACTION"):
                    effective_bindings.append((binding, source))
        return effective_bindings

    def create_xml_viewer_button(self, parent, source):
        """Create a button to view the XML file for a source"""
        mod_path = self.get_mod_path()
        if not mod_path:
            log("No mod path configured - skipping XML viewer button creation")
            return None
            
        if source in self.binding_sources:
            # Normalize path to fix slashes
            file_path = os.path.normpath(os.path.join(mod_path, self.binding_sources[source]["path"]))
            btn = ttk.Button(parent, text=f"View {source} XML", 
                           command=lambda: self.show_xml_content(file_path))
            return btn
        return None

    def show_xml_content(self, file_path):
        """Show XML content in a new window"""
        try:
            # Get the correct file path using the same method as load_xml_file
            mod_path = self.get_mod_path()
            if not mod_path:
                messagebox.showerror("Error", "No mod path configured")
                return
            
            # Get the appropriate XML path based on the source
            if os.path.basename(os.path.dirname(file_path)) == "equipment":
                full_path = get_equipment_file(mod_path)
            else:
                full_path = file_path
            
            if not full_path:
                messagebox.showerror("Error", "Could not determine file path")
                return
            
            log(f"Viewing XML file: {os.path.basename(full_path)}")
            
            # Check if directory exists
            if not os.path.exists(os.path.dirname(full_path)):
                messagebox.showerror("Error", "Directory does not exist. Please create it first.")
                return
            
            # Check if file exists
            if not os.path.exists(full_path):
                messagebox.showerror("Error", "File does not exist. Please create it first.")
                return
            
            # Create viewer window
            viewer = tk.Toplevel(self)
            viewer.title(f"XML Viewer - {os.path.basename(full_path)}")
            viewer.geometry("800x600")
            
            # Add text area
            text_area = tk.Text(viewer, wrap=tk.NONE)
            text_area.pack(fill=tk.BOTH, expand=True)
            
            # Add scrollbars
            y_scrollbar = ttk.Scrollbar(viewer, orient=tk.VERTICAL, command=text_area.yview)
            y_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            x_scrollbar = ttk.Scrollbar(viewer, orient=tk.HORIZONTAL, command=text_area.xview)
            x_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
            
            text_area.configure(yscrollcommand=y_scrollbar.set, xscrollcommand=x_scrollbar.set)
            
            # Load and display content
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
            text_area.insert('1.0', content)
            text_area.configure(state='disabled')  # Make read-only
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to show XML content: {str(e)}")
            return

    def build_class_view(self):
        log("\nBuilding class view...")
        available_classes = self.get_available_classes()
        
        # Add XML viewer buttons at the top
        buttons_frame = ttk.Frame(self.class_frame)
        buttons_frame.pack(fill="x", padx=5, pady=5)
        for source in self.binding_sources:
            btn = self.create_xml_viewer_button(buttons_frame, source)
            if btn:
                btn.pack(side="left", padx=2)
        
        # First show faction bindings
        faction_frame = ttk.LabelFrame(self.class_frame, text=f"Faction: {self.faction_name}")
        faction_frame.pack(fill="x", padx=5, pady=5, anchor="n")
        
        # Create a container for faction bindings
        faction_bindings_frame = ttk.Frame(faction_frame)
        faction_bindings_frame.pack(fill="x", expand=True)
        
        # Get all faction bindings from equipment source
        faction_bindings = []
        source_bindings = [b for b in self.all_bindings.get("equipment", []) 
                         if self.is_faction_binding(b)]
        log(f"Found {len(source_bindings)} faction bindings")
        faction_bindings.extend((b, "equipment") for b in source_bindings)
        
        if faction_bindings:
            for binding, source in faction_bindings:
                self.create_binding_widget(faction_bindings_frame, binding, source)
        
        # Add faction binding buttons frame
        faction_buttons_frame = ttk.Frame(faction_frame)
        faction_buttons_frame.pack(pady=5)
        
        # Add New button
        add_btn = ttk.Button(faction_buttons_frame, text="Add Faction-wide Binding", 
                           command=lambda c=self.faction_name, gf=faction_bindings_frame: self.add_binding(c, gf))
        add_btn.pack(side="left", padx=2)
        
        # Add Paste button if we have something in clipboard
        if self.clipboard:
            paste_btn = ttk.Button(faction_buttons_frame, text=f"Paste {self.clipboard['eqp']}", 
                               command=lambda c=self.faction_name, gf=faction_bindings_frame: self.paste_binding(gf, c))
            paste_btn.pack(side="left", padx=2)
        
        # Then show class-specific bindings
        for cls in available_classes:
            log(f"Processing class: {cls}")
            class_frame = ttk.LabelFrame(self.class_frame, text=f"Class: {cls}")
            class_frame.pack(fill="x", padx=5, pady=5, anchor="n")
            
            # Create a container for class bindings
            class_bindings_frame = ttk.Frame(class_frame)
            class_bindings_frame.pack(fill="x", expand=True)
            
            # Get class-specific bindings from equipment source
            class_bindings = []
            source_bindings = [b for b in self.all_bindings.get("equipment", []) 
                             if b.get("to", "") == cls]
            log(f"Found {len(source_bindings)} bindings for class {cls}")
            class_bindings.extend((b, "equipment") for b in source_bindings)
            
            if class_bindings:
                for binding, source in class_bindings:
                    self.create_binding_widget(class_bindings_frame, binding, source)
            
            # Add buttons frame
            buttons_frame = ttk.Frame(class_frame)
            buttons_frame.pack(pady=5)
            
            # Add New button
            add_btn = ttk.Button(buttons_frame, text="Add Class-specific Binding", 
                               command=lambda c=cls, gf=class_bindings_frame: self.add_binding(c, gf))
            add_btn.pack(side="left", padx=2)
            
            # Add Paste button if we have something in clipboard
            if self.clipboard:
                paste_btn = ttk.Button(buttons_frame, text=f"Paste {self.clipboard['eqp']}", 
                                   command=lambda c=cls, gf=class_bindings_frame: self.paste_binding(gf, c))
                paste_btn.pack(side="left", padx=2)

    def build_source_view(self):
        # Add XML viewer buttons at the top
        buttons_frame = ttk.Frame(self.source_frame)
        buttons_frame.pack(fill="x", padx=5, pady=5)
        for source in self.binding_sources:
            btn = self.create_xml_viewer_button(buttons_frame, source)
            if btn:
                btn.pack(side="left", padx=2)

        # Only show equipment bindings
        source = "equipment"
        bindings = self.all_bindings.get(source, [])
        source_frame = ttk.LabelFrame(self.source_frame, text=f"Source: {source}")
        source_frame.pack(fill="x", padx=5, pady=5, anchor="n")
        
        if not bindings:
            ttk.Label(source_frame, text="No bindings found").pack(pady=5)
        else:
            for binding in bindings:
                self.create_binding_widget(source_frame, binding, source)

    def build_summary_view(self):
        # Create summary statistics
        stats_frame = ttk.LabelFrame(self.summary_frame, text="Binding Statistics")
        stats_frame.pack(fill="x", padx=5, pady=5)
        
        # Count faction-wide bindings (only from equipment)
        faction_bindings = sum(1 for binding in self.all_bindings.get("equipment", []) 
                             if self.is_faction_binding(binding))
        
        ttk.Label(stats_frame, text=f"Faction-wide Bindings: {faction_bindings}").pack(anchor="w", padx=5)
        
        total_bindings = len(self.all_bindings.get("equipment", []))
        ttk.Label(stats_frame, text=f"Total Equipment Bindings: {total_bindings}").pack(anchor="w", padx=5)

        # Create class distribution
        class_stats = {}
        for binding in self.all_bindings.get("equipment", []):
            binding_to = binding.get("to", "")
            if binding_to == self.faction_name:
                cls = "FACTION"
            else:
                cls = binding_to
            class_stats[cls] = class_stats.get(cls, 0) + 1

        if class_stats:
            class_frame = ttk.LabelFrame(self.summary_frame, text="Bindings by Class")
            class_frame.pack(fill="x", padx=5, pady=5)
            for cls, count in sorted(class_stats.items()):
                ttk.Label(class_frame, text=f"{cls}: {count} bindings").pack(anchor="w", padx=5)

    def create_binding_widget(self, parent_frame, binding, source):
        binding_frame = ttk.Frame(parent_frame)
        binding_frame.pack(fill="x", expand=True, padx=5, pady=2)
        
        # Source indicator
        ttk.Label(binding_frame, text=f"[{source}]").grid(row=0, column=0, sticky="w", padx=2)
        
        # Equipment binding fields
        if source == "equipment":
            self.create_equipment_binding_fields(binding_frame, binding, source)
        else:
            self.create_other_binding_fields(binding_frame, binding, source)

    def create_equipment_binding_fields(self, frame, binding, source):
        try:
            # eqp field
            ttk.Label(frame, text="eqp:").grid(row=0, column=1, sticky="w", padx=2)
            eqp_entry = ttk.Entry(frame, width=30)
            eqp_entry.grid(row=0, column=2, sticky="w", padx=2)
            eqp_value = binding.get("eqp", "")
            if eqp_value:
                eqp_entry.insert(0, eqp_value)
            
            # to field (readonly since it's determined by the section)
            ttk.Label(frame, text="to:").grid(row=0, column=3, sticky="w", padx=2)
            to_entry = ttk.Entry(frame, width=30)
            to_value = binding.get("to", "")
            if to_value:
                to_entry.insert(0, to_value)
            to_entry.configure(state="readonly")  # Set readonly after inserting text
            to_entry.grid(row=0, column=4, sticky="w", padx=2)
            
            # Store widget references
            self.binding_widgets.append({
                "source": source,
                "binding": binding,
                "eqp_entry": eqp_entry,
                "to_entry": to_entry
            })
            
            # Add buttons frame
            buttons_frame = ttk.Frame(frame)
            buttons_frame.grid(row=0, column=5, padx=5)
            
            # Add copy button
            copy_btn = ttk.Button(buttons_frame, text="Copy", 
                                command=lambda b=binding: self.copy_binding(b))
            copy_btn.pack(side="left", padx=2)
            
            # Add remove button
            remove_btn = ttk.Button(buttons_frame, text="Remove", 
                                command=lambda b=binding, bf=frame: self.remove_binding(b, bf))
            remove_btn.pack(side="left", padx=2)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to create binding fields: {e}")
            raise

    def create_other_binding_fields(self, frame, binding, source):
        # Display other binding attributes
        col = 1
        entries = {}
        for key, value in binding.attrib.items():
            ttk.Label(frame, text=f"{key}:").grid(row=0, column=col, sticky="w", padx=2)
            entry = ttk.Entry(frame, width=20)
            entry.grid(row=0, column=col+1, sticky="w", padx=2)
            entry.insert(0, value)
            entries[key] = entry
            col += 2
            
        self.binding_widgets.append({
            "source": source,
            "binding": binding,
            "entries": entries
        })

    def add_binding(self, cls, group_frame):
        # Add new binding to equipment bindings
        if "equipment" not in self.binding_trees:
            messagebox.showerror("Error", "Equipment bindings file not found")
            return
            
        tree = self.binding_trees["equipment"]
        root = tree.getroot()
        
        # Create new binding
        new_binding = ET.Element("Bind")
        new_binding.set("eqp", "")
        new_binding.set("to", cls)
        
        # Add the new binding to the XML tree
        root.append(new_binding)
        
        # Ensure the group frame is properly configured
        group_frame.pack_configure(fill="x", expand=True)
        
        # Create UI for the new binding
        self.create_binding_widget(group_frame, new_binding, "equipment")
        
        # Add to our bindings list
        if "equipment" not in self.all_bindings:
            self.all_bindings["equipment"] = []
        self.all_bindings["equipment"].append(new_binding)
        
        # Update the frame
        group_frame.update_idletasks()

    def remove_binding(self, binding, binding_frame):
        try:
            # Remove binding from the XML tree
            if "equipment" in self.binding_trees:
                root = self.binding_trees["equipment"].getroot()
                for elem in root.findall(".//Bind"):
                    if (elem.get("eqp") == binding.get("eqp") and 
                        elem.get("to") == binding.get("to")):
                        root.remove(elem)
                        break
            
            # Remove from our bindings list
            if "equipment" in self.all_bindings:
                self.all_bindings["equipment"] = [b for b in self.all_bindings["equipment"] 
                                                if not (b.get("eqp") == binding.get("eqp") and 
                                                      b.get("to") == binding.get("to"))]
            
            # Remove widget references
            self.binding_widgets = [w for w in self.binding_widgets if w["binding"] != binding]
            
            # Remove from UI and update parent frame
            parent = binding_frame.master
            binding_frame.destroy()
            
            # If parent frame is now empty, update its appearance
            if not any(isinstance(child, ttk.Frame) for child in parent.winfo_children()):
                parent.pack_configure(expand=False)
            
            parent.update_idletasks()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to remove binding: {e}")

    def save_all_changes(self):
        try:
            # Get the current XML tree or create a new one
            if "equipment" not in self.binding_trees:
                tree = ET.ElementTree(ET.Element("Equipment"))
            else:
                tree = self.binding_trees["equipment"]
            
            # Get the root and clear it
            root = tree.getroot()
            for child in root:
                root.remove(child)
            
            # Group bindings by target (faction and classes)
            faction_bindings = []
            class_bindings = {}
            
            # Update XML from widget values
            for widget_ref in self.binding_widgets:
                if widget_ref["source"] == "equipment":
                    try:
                        eqp_entry = widget_ref.get("eqp_entry")
                        to_entry = widget_ref.get("to_entry")
                        
                        if not eqp_entry or not to_entry:
                            continue
                            
                        if not eqp_entry.winfo_exists() or not to_entry.winfo_exists():
                            continue
                            
                        eqp_value = eqp_entry.get().strip()
                        to_value = to_entry.get().strip()
                        
                        # Skip empty bindings
                        if not eqp_value or not to_value:
                            continue
                        
                        if to_value == self.faction_name:
                            faction_bindings.append(eqp_value)
                        else:
                            if to_value not in class_bindings:
                                class_bindings[to_value] = []
                            class_bindings[to_value].append(eqp_value)
                            
                    except tk.TclError:
                        continue  # Skip if widget has been destroyed

            # Write the XML content
            file_path = os.path.normpath(os.path.join(self.get_mod_path(), self.binding_sources["equipment"]["path"]))
            
            # Create formatted output
            output = ['<?xml version="1.0" encoding="utf-8"?>']
            output.append('<Equipment>')
            output.append('')
            
            # Add faction bindings
            if faction_bindings:
                output.append('<!-- Overall faction bindings -->')
                output.append(f'\t<Bind to="{self.faction_name}">')
                for eqp in sorted(set(faction_bindings)):  # Use set to remove duplicates
                    output.append(f'\t\t<eqp name="{eqp}"/>')
                output.append('\t</Bind>')
                output.append('')

            # Add class-specific bindings
            if class_bindings:
                output.append('<!-- Class-specific bindings -->')
                for cls in sorted(class_bindings.keys()):
                    if not cls:  # Skip empty class names
                        continue
                    output.append(f'<!-- {cls} equipment -->')
                    output.append(f'\t<Bind to="{cls}">')
                    for eqp in sorted(set(class_bindings[cls])):  # Use set to remove duplicates
                        output.append(f'\t\t<eqp name="{eqp}"/>')
                    output.append('\t</Bind>')
                    output.append('')

            output.append('</Equipment>')

            # Write the content
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(output))
            
            messagebox.showinfo("Success", "Changes saved successfully")
            
            # Reload to show the current bindings
            self.load_all_bindings()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save changes: {e}")
            raise  # Re-raise the exception for debugging

    def indent_xml(self, elem, level=0):
        """Add proper indentation to XML elements"""
        i = "\n" + level * "\t"
        if len(elem):
            if not elem.text or not elem.text.strip():
                elem.text = i + "\t"
            if not elem.tail or not elem.tail.strip():
                elem.tail = i
            for subelem in elem:
                self.indent_xml(subelem, level + 1)
            if not elem.tail or not elem.tail.strip():
                elem.tail = i
        else:
            if level and (not elem.tail or not elem.tail.strip()):
                elem.tail = i

    def organize_bindings(self):
        try:
            if "equipment" not in self.binding_trees:
                messagebox.showerror("Error", "Equipment bindings file not found")
                return

            # Collect and organize bindings
            faction_bindings = set()  # Use set to avoid duplicates
            class_bindings = {}    # {class_name: set(equipment_list)}

            # Go through all bindings
            for binding in self.all_bindings.get("equipment", []):
                eqp = binding.get("eqp", "")
                to = binding.get("to", "")
                
                if not eqp or not to:  # Skip empty bindings
                    continue
                    
                if to == self.faction_name:
                    faction_bindings.add(eqp)
                else:
                    if to not in class_bindings:
                        class_bindings[to] = set()
                    class_bindings[to].add(eqp)

            # Create new XML content
            output = ['<?xml version="1.0" encoding="utf-8"?>']
            output.append('<Equipment>')
            output.append('')
            
            # Add faction bindings in the nested format
            if faction_bindings:
                output.append('<!-- Overall faction bindings -->')
                output.append(f'\t<Bind to="{self.faction_name}">')
                for eqp in sorted(faction_bindings):
                    if eqp:  # Only add non-empty equipment
                        output.append(f'\t\t<eqp name="{eqp}"/>')
                output.append('\t</Bind>')
                output.append('')

            # Add class-specific bindings in the same nested format
            if class_bindings:
                output.append('<!-- Class-specific bindings -->')
                # For each class
                for cls in sorted(class_bindings.keys()):
                    if not cls:  # Skip empty class names
                        continue
                    # Add comment for this class
                    output.append(f'<!-- {cls} equipment -->')
                    output.append(f'\t<Bind to="{cls}">')
                    # Add all equipment for this class
                    for eqp in sorted(class_bindings[cls]):
                        if eqp:  # Only add non-empty equipment
                            output.append(f'\t\t<eqp name="{eqp}"/>')
                    output.append('\t</Bind>')
                    output.append('')  # Add empty line between classes

            output.append('</Equipment>')

            # Write the organized content
            file_path = os.path.normpath(os.path.join(self.get_mod_path(), self.binding_sources["equipment"]["path"]))
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(output))

            # Reload the view
            self.load_all_bindings()
            messagebox.showinfo("Success", "Bindings organized successfully")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to organize bindings: {e}")
            raise

    def copy_binding(self, binding):
        """Copy a binding to clipboard"""
        self.clipboard = {
            "eqp": binding.get("eqp", ""),
            "to": binding.get("to", "")
        }
        # Rebuild just the buttons frames to show paste buttons
        self.rebuild_class_buttons()
        messagebox.showinfo("Success", f"Copied binding: {self.clipboard['eqp']}")

    def paste_binding(self, binding_frame, target_class):
        """Paste a binding from clipboard"""
        if not self.clipboard:
            messagebox.showerror("Error", "No binding in clipboard")
            return
            
        try:
            # Create new binding with copied eqp and target class
            new_binding = ET.Element("Bind")
            new_binding.set("eqp", self.clipboard["eqp"])
            new_binding.set("to", target_class)
            
            # Add to XML tree
            if "equipment" in self.binding_trees:
                root = self.binding_trees["equipment"].getroot()
                root.append(new_binding)
                
                # Add to bindings list
                if "equipment" not in self.all_bindings:
                    self.all_bindings["equipment"] = []
                self.all_bindings["equipment"].append(new_binding)
                
                # Create UI for the new binding
                self.create_binding_widget(binding_frame.master, new_binding, "equipment")
                
                messagebox.showinfo("Success", 
                    f"Pasted binding {self.clipboard['eqp']} to {target_class}")
            else:
                messagebox.showerror("Error", "Equipment bindings file not found")
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to paste binding: {e}")
            raise

    def rebuild_class_buttons(self):
        """Rebuild just the button sections of each class frame"""
        # Update faction buttons
        faction_frame = None
        class_frames = {}
        
        # Find all frames
        for child in self.class_frame.winfo_children():
            if isinstance(child, ttk.LabelFrame):
                if child.cget("text").startswith("Faction:"):
                    faction_frame = child
                elif child.cget("text").startswith("Class:"):
                    class_name = child.cget("text").replace("Class: ", "")
                    class_frames[class_name] = child
        
        # Update faction frame buttons
        if faction_frame:
            # Find and remove only the buttons frame
            for child in faction_frame.winfo_children():
                if isinstance(child, ttk.Frame):
                    # Check if this is the buttons frame (has buttons as direct children)
                    if any(isinstance(grandchild, ttk.Button) for grandchild in child.winfo_children()):
                        child.destroy()
            
            # Add new buttons frame
            buttons_frame = ttk.Frame(faction_frame)
            buttons_frame.pack(pady=5)
            
            # Add New button
            add_btn = ttk.Button(buttons_frame, text="Add Faction-wide Binding", 
                               command=lambda c=self.faction_name, gf=faction_frame.winfo_children()[0]: self.add_binding(c, gf))
            add_btn.pack(side="left", padx=2)
            
            # Add Paste button if we have something in clipboard
            if self.clipboard:
                paste_btn = ttk.Button(buttons_frame, text=f"Paste {self.clipboard['eqp']}", 
                                   command=lambda c=self.faction_name, gf=faction_frame.winfo_children()[0]: self.paste_binding(gf, c))
                paste_btn.pack(side="left", padx=2)
        
        # Update class frames buttons
        for cls, frame in class_frames.items():
            # Find and remove only the buttons frame
            for child in frame.winfo_children():
                if isinstance(child, ttk.Frame):
                    # Check if this is the buttons frame (has buttons as direct children)
                    if any(isinstance(grandchild, ttk.Button) for grandchild in child.winfo_children()):
                        child.destroy()
            
            # Add new buttons frame
            buttons_frame = ttk.Frame(frame)
            buttons_frame.pack(pady=5)
            
            # Add New button
            add_btn = ttk.Button(buttons_frame, text="Add Class-specific Binding", 
                               command=lambda c=cls, gf=frame.winfo_children()[0]: self.add_binding(c, gf))
            add_btn.pack(side="left", padx=2)
            
            # Add Paste button if we have something in clipboard
            if self.clipboard:
                paste_btn = ttk.Button(buttons_frame, text=f"Paste {self.clipboard['eqp']}", 
                                   command=lambda c=cls, gf=frame.winfo_children()[0]: self.paste_binding(gf, c))
                paste_btn.pack(side="left", padx=2)

def get_plugin_tab(notebook):
    """Create and return the equipment binding editor tab"""
    return PLUGIN_TITLE, EquipmentBindingEditor(notebook) 