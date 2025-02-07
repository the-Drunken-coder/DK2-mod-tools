import tkinter as tk
from tkinter import ttk, messagebox
import xml.etree.ElementTree as ET
import os
from pathlib import Path

class EquipmentBindingEditor(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.tree = None
        self.bindings = []
        self.binding_widgets = []
        self.mod_path = os.path.join("Example mod", "Baby seals")
        self.faction_name = "BABY SEALS"
        self.binding_sources = {
            "equipment": {"path": "equipment/seals_binds.xml", "xpath": ".//Bind"},
            "units": {"path": "units/seals_unit.xml", "xpath": ".//Equipment"}
        }
        self.build_ui()
        self.load_all_bindings()

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
        classes = set(["FACTION"])  # Add FACTION as a special class
        unit_xml_path = os.path.join(self.mod_path, "units", "seals_unit.xml")
        try:
            tree = ET.parse(unit_xml_path)
            root = tree.getroot()
            for cls in root.findall(".//Class"):
                name = cls.get("name")
                if name:  # Only add if name exists and is not None
                    classes.add(str(name))  # Convert to string to ensure safe comparison
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load unit classes: {e}")
        return sorted(list(filter(None, classes)))  # Filter out any None values before sorting

    def load_xml_file(self, file_path, xpath):
        try:
            full_path = os.path.join(self.mod_path, file_path)
            if not os.path.exists(full_path):
                return []
            tree = ET.parse(full_path)
            
            # For equipment bindings, we need to handle all binding formats
            if xpath == ".//Bind":
                bindings = []
                for bind in tree.findall(xpath):
                    # Case 1: Multiple to elements (equipment bound to multiple classes)
                    if bind.findall("to"):
                        eqp_value = bind.get("eqp")
                        if eqp_value:
                            for to in bind.findall("to"):
                                to_value = to.get("name")
                                if to_value:
                                    new_bind = ET.Element("Bind")
                                    new_bind.set("eqp", str(eqp_value))
                                    new_bind.set("to", str(to_value))
                                    bindings.append(new_bind)
                    # Case 2: Multiple eqp elements (new format)
                    elif bind.findall("eqp"):
                        to_value = bind.get("to")
                        if to_value:
                            for eqp in bind.findall("eqp"):
                                eqp_value = eqp.get("name")
                                if eqp_value:
                                    new_bind = ET.Element("Bind")
                                    new_bind.set("eqp", str(eqp_value))
                                    new_bind.set("to", str(to_value))
                                    bindings.append(new_bind)
                    # Case 3: Direct attributes
                    else:
                        eqp_value = bind.get("eqp")
                        to_value = bind.get("to")
                        if eqp_value and to_value:
                            new_bind = ET.Element("Bind")
                            new_bind.set("eqp", str(eqp_value))
                            new_bind.set("to", str(to_value))
                            bindings.append(new_bind)
                            
                return bindings
            return tree.findall(xpath)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load {file_path}: {e}")
            return []

    def load_all_bindings(self):
        # Store old widget references before clearing
        old_widgets = self.binding_widgets.copy()
        
        self.all_bindings = {}
        self.binding_trees = {}
        self.binding_widgets = []  # Clear widget references
        
        # Load bindings from all sources
        for source, info in self.binding_sources.items():
            elements = self.load_xml_file(info["path"], info["xpath"])
            self.all_bindings[source] = elements
            if elements:
                tree = ET.parse(os.path.join(self.mod_path, info["path"]))
                self.binding_trees[source] = tree

        # Clear existing UI - properly destroy all widgets
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

        self.build_class_view()
        self.build_source_view()
        self.build_summary_view()

    def is_faction_binding(self, binding):
        """Check if a binding is a faction-level binding"""
        binding_to = binding.get("to", "")
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
        if source in self.binding_sources:
            file_path = os.path.join(self.mod_path, self.binding_sources[source]["path"])
            btn = ttk.Button(parent, text=f"View {source} XML", 
                           command=lambda: self.show_xml_content(file_path))
            return btn
        return None

    def show_xml_content(self, file_path):
        """Show XML content in a new window"""
        try:
            with open(file_path, 'r') as file:
                content = file.read()
            
            # Create new window
            xml_window = tk.Toplevel()
            xml_window.title(f"XML View - {os.path.basename(file_path)}")
            
            # Add text widget with scrollbar
            text_frame = ttk.Frame(xml_window)
            text_frame.pack(fill="both", expand=True, padx=5, pady=5)
            
            text_widget = tk.Text(text_frame, wrap="none")
            yscroll = ttk.Scrollbar(text_frame, orient="vertical", command=text_widget.yview)
            xscroll = ttk.Scrollbar(text_frame, orient="horizontal", command=text_widget.xview)
            
            text_widget.configure(yscrollcommand=yscroll.set, xscrollcommand=xscroll.set)
            
            # Pack scrollbars and text widget
            yscroll.pack(side="right", fill="y")
            xscroll.pack(side="bottom", fill="x")
            text_widget.pack(side="left", fill="both", expand=True)
            
            # Insert content and make read-only
            text_widget.insert("1.0", content)
            text_widget.configure(state="disabled")
            
            # Set window size and position
            xml_window.geometry("800x600")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load XML file: {e}")

    def build_class_view(self):
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
        faction_bindings.extend((b, "equipment") for b in source_bindings)
        
        if faction_bindings:
            for binding, source in faction_bindings:
                self.create_binding_widget(faction_bindings_frame, binding, source)
        
        # Add faction binding button
        add_btn = ttk.Button(faction_frame, text="Add Faction-wide Binding", 
                           command=lambda c=self.faction_name, gf=faction_bindings_frame: self.add_binding(c, gf))
        add_btn.pack(pady=5)
        
        # Then show class-specific bindings
        for cls in [c for c in available_classes if c != "FACTION"]:
            class_frame = ttk.LabelFrame(self.class_frame, text=f"Class: {cls}")
            class_frame.pack(fill="x", padx=5, pady=5, anchor="n")
            
            # Create a container for class bindings
            class_bindings_frame = ttk.Frame(class_frame)
            class_bindings_frame.pack(fill="x", expand=True)
            
            # Get class-specific bindings from equipment source
            class_bindings = []
            source_bindings = [b for b in self.all_bindings.get("equipment", []) 
                             if b.get("to", "") == cls]
            class_bindings.extend((b, "equipment") for b in source_bindings)
            
            if class_bindings:
                for binding, source in class_bindings:
                    self.create_binding_widget(class_bindings_frame, binding, source)
            
            # Add class binding button
            add_btn = ttk.Button(class_frame, text="Add Class-specific Binding", 
                               command=lambda c=cls, gf=class_bindings_frame: self.add_binding(c, gf))
            add_btn.pack(pady=5)

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
            
            # Add remove button
            remove_btn = ttk.Button(frame, text="Remove", 
                                command=lambda b=binding, bf=frame: self.remove_binding(b, bf))
            remove_btn.grid(row=0, column=5, padx=5)
            
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
            file_path = os.path.join(self.mod_path, self.binding_sources["equipment"]["path"])
            
            # Create formatted output
            output = ['<?xml version="1.0" encoding="utf-8"?>']
            output.append('<Equipment>')
            output.append('')
            
            # Add faction bindings in the nested format
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
            file_path = os.path.join(self.mod_path, self.binding_sources["equipment"]["path"])
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(output))

            # Reload the view
            self.load_all_bindings()
            messagebox.showinfo("Success", "Bindings organized successfully")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to organize bindings: {e}")
            raise


def get_plugin_tab(parent):
    container = ttk.Frame(parent)
    editor = EquipmentBindingEditor(container)
    editor.pack(fill="both", expand=True)
    
    # Set initial window size
    parent.update_idletasks()  # Update geometry
    screen_height = parent.winfo_screenheight()
    desired_height = min(screen_height * 0.6, 600)  # 60% of screen height or 600px, whichever is smaller
    parent.winfo_toplevel().geometry(f"800x{int(desired_height)}")
    
    return "Equipment & Binding Editor", container 