import tkinter as tk
from tkinter import ttk, messagebox
import xml.etree.ElementTree as ET
import os
import shutil

def get_plugin_tab(parent):
    container = ttk.Frame(parent)
    editor = GUIEditor(container)
    editor.pack(fill="both", expand=True)
    return "GUI Editor", container

class DraggableFrame(tk.Frame):
    def __init__(self, parent, editor, title, color, row_index, width_cells=2, height_cells=1, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.title = title
        self.parent = parent
        self.editor = editor
        self.cell_size = 95  # Width of each column (380/4)
        self.row_height = 148
        self.row_index = row_index
        self.width_cells = width_cells  # Number of cells wide (1, 2, or 4)
        self.height_cells = height_cells  # Number of cells high (1 or 2)
        self.class_text = "ASSAULTER"  # Add default class text
        self.slot_classes = {}  # Dictionary to store class assignments for each slot
        
        # Calculate total number of slots
        self.total_slots = width_cells * height_cells
        
        # Initialize slot classes with default value
        for i in range(self.total_slots):
            self.slot_classes[i] = "unusedClass"  # Default to unusedClass
        
        # Calculate size based on cells
        if width_cells == 2:
            width = 184  # Fixed width for 2x1
            height = 142  # Fixed height for 2x1
        else:  # 4x1 or 4x2
            width = 374  # Fixed width for 4x1 and 4x2
            height = 142 if height_cells == 1 else 290  # Height based on rows
        
        self.configure(width=width, height=height, bg=color)
        self.pack_propagate(False)
        
        # Add label
        self.label = tk.Label(self, text=title, fg='white', bg=color, font=('Arial', 10, 'bold'))
        self.label.pack(pady=5)
        
        # Bind mouse events
        self.bind('<Button-1>', self.on_click)
        self.bind('<B1-Motion>', self.on_drag)
        self.bind('<ButtonRelease-1>', self.on_drop)
        self.bind('<Button-3>', self.on_right_click)  # Right click to delete
        
        # Selection state
        self.selected = False
        self.original_color = color
        
        self.drag_start_x = 0
        self.drag_start_y = 0
    
    def get_visual_position(self):
        """Convert XML position to visual position"""
        if self.width_cells == 2:  # 2x1 box
            # Start in left position by default
            return 0, max(0, self.row_index * self.row_height)  # Ensure Y is never negative
        else:  # 4x1 or 4x2
            return 2, max(0, self.row_index * self.row_height)  # Ensure Y is never negative

    def get_xml_position(self):
        """Convert visual position to XML position"""
        # Base Y positions for each row
        row_y_positions = [
            71,    # Row 0
            -77,   # Row 1
            -225,  # Row 2
            -373,  # Row 3
            -521,  # Row 4
            -669,  # Row 5
            -817,  # Row 6
            -965,  # Row 7
            -1113, # Row 8
            -1261  # Row 9
        ]
        
        # Y offsets for each box type
        y_offsets = {
            "2x1": 0,      # 2x1 boxes have no offset
            "4x1": 0,    # 4x1 boxes offset by -80
            "4x2": -74      # 4x2 boxes offset by 74
        }
        
        # Get the base Y position for this row
        base_y = row_y_positions[self.row_index]
        
        if self.width_cells == 2:  # 2x1 box
            # Convert visual position to XML position for 2x1 boxes
            visual_x = self.winfo_x()
            if visual_x < 50:  # Left position
                return -98, base_y + y_offsets["2x1"]
            elif visual_x < 150:  # Middle position
                return 0, base_y + y_offsets["2x1"]
            else:  # Right position
                return 98, base_y + y_offsets["2x1"]
        elif self.height_cells == 2:  # 4x2 box
            return -3, base_y + y_offsets["4x2"]
        else:  # 4x1 box
            return -2, base_y + y_offsets["4x1"]

    def on_click(self, event):
        self.drag_start_x = event.x
        self.drag_start_y = event.y
        self.start_x = self.winfo_x()
        self.start_y = self.winfo_y()
        self.select()
        self.editor.update_info_panel(self)
    
    def on_drag(self, event):
        x = self.winfo_x() + event.x - self.drag_start_x
        y = self.winfo_y() + event.y - self.drag_start_y
        
        # Allow free movement during drag, but keep within container width
        x = max(0, min(x, 380 - self.winfo_width()))
        y = max(0, y)
        self.place(x=x, y=y)
    
    def on_drop(self, event):
        # Get nearest row
        row_index = max(0, round(self.winfo_y() / self.row_height))
        
        # Calculate y position
        visual_y = row_index * self.row_height
        
        # For 2x1 boxes, snap to one of three positions (left, middle, right)
        if self.width_cells == 2:
            current_x = self.winfo_x()
            # Define snap positions for 2x1 boxes
            left_pos = 0      # Left position (XML: -98)
            mid_pos = 98     # Middle position (XML: 0)
            right_pos = 196  # Right position (XML: 98)
            
            # Find closest snap position
            positions = [left_pos, mid_pos, right_pos]
            visual_x = min(positions, key=lambda x: abs(x - current_x))
        else:  # 4x1 or 4x2
            visual_x = 2  # Fixed x position for 4x1/4x2
        
        # Update row index
        self.row_index = row_index
        
        # Place the frame at the correct position
        self.place(x=visual_x, y=visual_y)
        self.editor.update_row_markers()
    
    def select(self):
        # Deselect all other frames
        for frame in self.editor.draggable_frames.values():
            if frame != self:
                frame.deselect()
        
        # Select this frame
        if not self.selected:
            self.selected = True
            self.configure(bg=self.darken_color(self.original_color))
            self.label.configure(bg=self.darken_color(self.original_color))
    
    def deselect(self):
        if self.selected:
            self.selected = False
            self.configure(bg=self.original_color)
            self.label.configure(bg=self.original_color)
    
    def darken_color(self, color):
        color = color.lstrip('#')
        rgb = tuple(int(color[i:i+2], 16) for i in (0, 2, 4))
        darkened = tuple(int(c * 0.8) for c in rgb)
        return '#{:02x}{:02x}{:02x}'.format(*darkened)

    def on_right_click(self, event):
        if messagebox.askyesno("Delete Box", "Do you want to delete this box?"):
            self.editor.remove_box(self)

    def set_class_text(self, text):
        self.class_text = text

    def set_slot_class(self, slot_index, class_name):
        print(f"\nSetting slot class:")
        print(f"  Box: {self.title}")
        print(f"  Slot: {slot_index}")
        print(f"  Old class: {self.slot_classes.get(slot_index, 'None')}")
        print(f"  New class: {class_name}")
        
        # Add back the Class suffix for storage
        self.slot_classes[slot_index] = class_name + "Class" if class_name != "unused" else "unusedClass"
        print(f"  Final class value: {self.slot_classes[slot_index]}")
        self.editor.save_layout(show_popup=False)

    def get_slot_class(self, slot_index):
        class_name = self.slot_classes.get(slot_index, "unusedClass")
        # Remove Class suffix for display
        if class_name != "unusedClass":
            class_name = class_name[:-5]  # Remove 'Class' suffix for display
        else:
            class_name = "unused"
        print(f"Getting slot class for {self.title} slot {slot_index}: {class_name}")
        return class_name

    def get_xml_origin(self):
        x, y = self.get_xml_position()
        return f"{x} {y}"

    def get_slot_container_origin(self):
        if self.width_cells == 2:  # 2x1 box
            return "-45 -24"
        else:  # 4x1 or 4x2
            if self.height_cells == 2:  # 4x2 box
                return ["-138 30", "-138 -70"]  # Return both row origins
            else:  # 4x1 box
                return "-138 -24"

    def get_header_color(self):
        if self.width_cells == 2:  # 2x1 box
            return "cb893ecc"
        else:  # 4x1 or 4x2 box
            return "cd853fcc"

class GUIEditor(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.cell_size = 95  # Width of each column (380/4)
        self.row_height = 148
        self.row_markers = []
        self.draggable_frames = {}
        self.row_containers = {}
        self.next_box_number = 1
        self.selected_box = None
        self.available_classes = []  # Store available classes from XML
        self.load_available_classes()  # Load classes when initializing
        self.build_ui()
    
    def load_available_classes(self):
        try:
            xml_path = "Example mod/Baby seals/units/seals_unit.xml"
            tree = ET.parse(xml_path)
            root = tree.getroot()
            
            # Find all Class elements and get their name attributes (not nameUI)
            classes = root.findall(".//Class")
            self.available_classes = []
            for cls in classes:
                class_name = cls.get("name", "")
                if class_name:
                    # Remove the "Class" suffix for display
                    display_name = class_name[:-5] if class_name.endswith("Class") else class_name
                    print(f"Found class with name: {class_name}, display as: {display_name}")
                    self.available_classes.append(display_name)
            
            if not self.available_classes:
                print("Warning: No classes found in units XML")
                self.available_classes = ["Assaulter"]  # Default fallback
                
        except Exception as e:
            print(f"Failed to load classes from XML: {e}")
            self.available_classes = ["Assaulter"]  # Default fallback
    
    def build_ui(self):
        # Main container
        self.main_container = tk.Frame(self, width=460)
        self.main_container.pack(expand=True, fill='both')
        self.main_container.pack_propagate(False)
        
        # Add box controls at the top
        control_bar = tk.Frame(self, bg='#1a1a1a')
        control_bar.pack(side='top', fill='x', pady=5)
        
        ttk.Label(control_bar, text="Add Box:", style='Light.TLabel').pack(side='left', padx=5)
        
        ttk.Button(control_bar, text="2x1", command=lambda: self.add_box(2)).pack(side='left', padx=2)
        ttk.Button(control_bar, text="4x1", command=lambda: self.add_box(4)).pack(side='left', padx=2)
        ttk.Button(control_bar, text="4x2", command=lambda: self.add_box(4, height_cells=2)).pack(side='left', padx=2)
        
        # Row marker container (left)
        self.marker_container = tk.Frame(self.main_container, width=40, bg='#1a1a1a')
        self.marker_container.pack(side='left', fill='y')
        
        # Create canvas and scrollbar for grid
        self.canvas = tk.Canvas(self.main_container, width=380, bg='#1a1a1a')
        self.scrollbar = ttk.Scrollbar(self.main_container, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        # Pack scrollbar and canvas
        self.scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        
        # Grid container (middle)
        self.grid_container = tk.Frame(self.canvas, bg='#1a1a1a')
        self.canvas.create_window((0, 0), window=self.grid_container, anchor="nw")
        
        # Create row containers
        for i in range(10):  # Support up to 10 rows
            row_frame = tk.Frame(self.grid_container, width=380, height=self.row_height, bg='#1a1a1a')
            row_frame.pack(fill='x', expand=False)
            row_frame.pack_propagate(False)
            self.row_containers[i] = row_frame
            
            # Add grid lines
            separator = ttk.Separator(row_frame, orient='horizontal')
            separator.place(relx=0, rely=1, relwidth=1)
            
            # Add row label
            label = tk.Label(row_frame, text=f"Row {i+1}", fg='#666666', bg='#1a1a1a')
            label.place(x=10, y=10)
        
        # Draw vertical grid lines
        for i in range(5):  # 0 to 4 for 4 columns
            x = i * self.cell_size
            line = tk.Frame(self.grid_container, width=1, bg='#333333')
            line.place(x=x, y=0, relheight=1)
            self.row_markers.append(line)  # Add to markers so they get cleaned up properly
        
        # Info panel (right)
        self.info_panel = tk.Frame(self.main_container, width=150, bg='#1a1a1a')
        self.info_panel.pack(side='right', fill='y')
        
        # Info panel contents
        self.info_title = tk.Label(self.info_panel, text="Box Settings", bg='#cb893e', fg='black', width=20)
        self.info_title.pack(fill='x', pady=(0, 10))
        
        # Settings container
        settings_frame = tk.Frame(self.info_panel, bg='#211e1d')
        settings_frame.pack(fill='x', padx=5, pady=5)
        
        # Display name setting
        display_name_label = tk.Label(settings_frame, text="Display Name:", bg='#211e1d', fg='white')
        display_name_label.pack(fill='x')
        
        self.class_text_entry = ttk.Entry(settings_frame)
        self.class_text_entry.pack(fill='x', pady=(0, 10))
        self.class_text_entry.bind('<Return>', self.update_class_text)
        self.class_text_entry.bind('<FocusOut>', self.update_class_text)
        
        # Slot settings frame
        self.slot_settings_frame = tk.Frame(settings_frame, bg='#211e1d')
        self.slot_settings_frame.pack(fill='x', pady=5)
        
        # Info display
        self.info_content = tk.Text(self.info_panel, height=6, width=20, bg='#211e1d', fg='white', 
                                  font=('Courier', 9))
        self.info_content.pack(fill='both', expand=True, padx=5)
        self.info_content.config(state='disabled')

        # Configure scrolling
        self.grid_container.bind('<Configure>', self.on_frame_configure)
        self.canvas.bind('<Configure>', self.on_canvas_configure)
        self.canvas.bind_all('<MouseWheel>', self.on_mousewheel)

        # Control panel
        control_panel = tk.Frame(self, bg='#1a1a1a')
        control_panel.pack(side='bottom', fill='x', pady=5)
        
        save_button = tk.Button(control_panel, text="Save Layout", command=self.save_layout, 
                              bg='#cb893e', fg='black', padx=20)
        save_button.pack(side='right', padx=10)
        
        self.coord_label = tk.Label(control_panel, text="Coordinates: ", bg='black', fg='white')
        self.coord_label.pack(side='left', fill='x', expand=True)
        
        self.grid_container.bind('<Motion>', self.update_coordinates)
        
        # Initialize row markers
        self.update_row_markers()
        
        # Schedule a one-time reload after UI is built
        self.after(100, self.reload_xml)
    
    def on_frame_configure(self, event=None):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
    
    def on_canvas_configure(self, event):
        # Update the width of the frame to fit the canvas
        self.canvas.itemconfig(self.canvas.find_withtag("all")[0], width=event.width)
    
    def on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
    
    def get_nearest_row_y(self, y):
        row_index = round(y / self.row_height)
        return row_index * self.row_height
    
    def get_next_row_y(self, y):
        row_index = (y // self.row_height) + 1
        return row_index * self.row_height
    
    def get_row_index(self, y):
        return y // self.row_height
    
    def update_row_markers(self):
        for marker in self.row_markers:
            marker.destroy()
        self.row_markers.clear()
        
        frames = []
        for widget in self.grid_container.winfo_children():
            if isinstance(widget, DraggableFrame):
                frames.append((widget.row_index, widget))
        
        used_rows = sorted(set(frame[0] for frame in frames))
        for row in used_rows:
            marker = tk.Frame(self.marker_container, height=20, width=40, bg='#cb893e')
            marker.place(x=0, y=row * self.row_height + 10)
            label = tk.Label(marker, text=str(row), fg='black', bg='#cb893e')
            label.pack(pady=2)
            self.row_markers.append(marker)
            
            line = tk.Frame(self.grid_container, width=8, height=self.row_height, bg='#f97b03')
            line.place(x=-16, y=row * self.row_height)
            self.row_markers.append(line)
    
    def update_coordinates(self, event):
        grid_x = event.x // self.cell_size
        grid_y = event.y // self.row_height
        self.coord_label.config(text=f"Grid Position: x={grid_x}, y={grid_y} | Pixels: x={event.x}, y={event.y}")
    
    def update_class_text(self, event=None):
        if self.selected_box:
            new_text = self.class_text_entry.get().strip()
            if new_text:
                self.selected_box.set_class_text(new_text)
                # Save the changes immediately, but don't show popup
                self.save_layout(show_popup=False)
    
    def update_info_panel(self, frame):
        print(f"\nUpdating info panel for box: {frame.title}")
        self.selected_box = frame
        self.info_content.config(state='normal')
        self.info_content.delete(1.0, tk.END)
        
        # Update the class text entry
        self.class_text_entry.delete(0, tk.END)
        self.class_text_entry.insert(0, frame.class_text)
        
        # Clear existing slot dropdowns
        for widget in self.slot_settings_frame.winfo_children():
            widget.destroy()
        
        # Add title for slots section
        slots_title = tk.Label(self.slot_settings_frame, text="Slot Assignments:", bg='#211e1d', fg='white')
        slots_title.pack(fill='x', pady=(0, 5))
        
        # Add slot class selection dropdowns
        for i in range(frame.total_slots):
            slot_frame = ttk.Frame(self.slot_settings_frame)
            slot_frame.pack(fill='x', pady=2)
            
            current_class = frame.get_slot_class(i)
            
            # Create slot label with current class
            slot_label = ttk.Label(slot_frame, text=f"Slot {i+1} [{current_class}]:")
            slot_label.pack(side='left', padx=5)
            
            print(f"Creating dropdown for slot {i}:")
            print(f"  Current class: {current_class}")
            print(f"  Available classes: {['unused'] + self.available_classes}")
            
            # Create a StringVar for the dropdown
            slot_var = tk.StringVar(value=current_class)
            
            # Create the dropdown
            slot_dropdown = ttk.Combobox(slot_frame, textvariable=slot_var, values=["unused"] + self.available_classes, state='readonly')
            slot_dropdown.pack(side='left', fill='x', expand=True, padx=5)
            
            # Create a callback function that captures the current values
            def make_callback(slot_index, dropdown, frame, label):
                def callback(*args):
                    selected_class = dropdown.get()
                    print(f"\n{'='*50}")
                    print(f"DROPDOWN CHANGE DETECTED")
                    print(f"Box: {frame.title}")
                    print(f"Slot: {slot_index}")
                    print(f"Previous class: {frame.get_slot_class(slot_index)}")
                    print(f"New class: {selected_class}")
                    print(f"Box position: {frame.get_xml_origin()}")
                    
                    # Update the slot class
                    frame.set_slot_class(slot_index, selected_class)
                    
                    # Update the label to show new class
                    label.config(text=f"Slot {slot_index+1} [{selected_class}]:")
                    
                    # Calculate slot position
                    xml_x, xml_y = frame.get_xml_position()
                    print(f"XML position: x={xml_x}, y={xml_y}")
                    
                    if frame.width_cells == 2:  # 2x1 box
                        base_x = xml_x + (-45)
                        if xml_x == 98:  # Right position
                            x_pos = base_x + (0 if slot_index == 0 else 90)
                        elif xml_x == 0:  # Middle position
                            x_pos = base_x + (0 if slot_index == 0 else 90)
                        else:  # Left position (-98)
                            x_pos = base_x + (0 if slot_index == 0 else 90)
                        y_pos = xml_y + (-24)
                    else:  # 4x1 or 4x2 box
                        base_x = -2 + (-138)
                        x_pos = base_x + (slot_index % 4 * 90)
                        if frame.height_cells == 2:  # 4x2 box
                            container_y = -299
                            if slot_index >= 4:  # Second row
                                y_pos = container_y + (-3) - 70
                            else:  # First row
                                y_pos = container_y + (-3) + 30
                        else:  # 4x1 box
                            y_pos = xml_y + (-24)
                    
                    print(f"Calculated slot position:")
                    print(f"  Base X: {base_x}")
                    print(f"  Final X: {x_pos}")
                    print(f"  Final Y: {y_pos}")
                    print(f"Moving slot to {selected_class}Class container")
                    
                    # Save the layout to update XML
                    self.save_layout(show_popup=False)
                    print("Layout saved with updated slot position")
                    print("="*50)
                return callback
            
            # Bind both the trace and the dropdown selection event
            callback = make_callback(i, slot_dropdown, frame, slot_label)
            slot_var.trace_add('write', callback)
            slot_dropdown.bind('<<ComboboxSelected>>', callback)
            
            print(f"  Added change callbacks for slot {i}")
        
        info_text = f"""Box: {frame.title}
Position: ({frame.winfo_x()}, {frame.winfo_y()})
Grid Pos: ({frame.winfo_x()//self.cell_size}, {frame.winfo_y()//self.row_height})
Width: {frame.winfo_width()}px
Height: {frame.winfo_height()}px
Row Index: {frame.row_index}"""
        
        self.info_content.insert(1.0, info_text)
        self.info_content.config(state='disabled')
        print("Info panel update complete")
    
    def get_mod_name(self):
        try:
            mod_xml_path = "Example mod/Baby seals/mod.xml"
            tree = ET.parse(mod_xml_path)
            root = tree.getroot()
            return root.get("title", "BABY SEALS")  # Default to BABY SEALS if not found
        except Exception as e:
            print(f"Failed to read mod name: {e}")
            return "BABY SEALS"
    
    def save_layout(self, show_popup=True):
        try:
            xml_path = "Example mod/Baby seals/gui/seals_deploy.xml"
            mod_name = self.get_mod_name().upper()
            
            print("Starting save_layout")
            
            # Create the base XML structure
            root = ET.Element("GUIItems")
            
            # Add EventActionBatch
            event_batch = ET.SubElement(root, "EventActionBatch", name="GAME_GUI_LOADTIME_ACTIONS")
            ET.SubElement(event_batch, "Action", type="Show", target=mod_name)
            
            # Add main container
            container = ET.SubElement(root, "Item", name=mod_name, origin="0 -454", 
                                   hidden="true", align="rt", sizeX="380")
            
            # Add OnOpen action
            on_open = ET.SubElement(container, "OnOpen")
            ET.SubElement(on_open, "Action", type="AddMeToParent", target="#unit_header")
            
            # Sort frames by row index to maintain order
            sorted_frames = sorted(self.draggable_frames.items(), key=lambda x: x[1].row_index)
            
            # Add each row first (UI elements)
            for title, frame in sorted_frames:
                print(f"Processing frame {title}")
                # Get correct dimensions based on frame type
                if frame.width_cells == 2:
                    size_x = 184
                    size_y = 142
                else:
                    size_x = 374
                    size_y = 142 if frame.height_cells == 1 else 290
                
                # Create class container with correct origin
                xml_x, xml_y = frame.get_xml_position()
                class_container = ET.SubElement(container, "StaticImage", 
                                             name=title + "Class",
                                             origin=f"{xml_x} {xml_y}")
                
                # Add background
                ET.SubElement(class_container, "RenderObject2D",
                            texture="data/textures/gui/square.tga",
                            sizeX=str(size_x),
                            sizeY=str(size_y),
                            color="211e1dcc")
                
                # Add class header
                header = ET.SubElement(class_container, "StaticImage", 
                                     name="#ClassHeader",
                                     origin="0 0",
                                     align="t")
                
                ET.SubElement(header, "RenderObject2D",
                            texture="data/textures/gui/square.tga",
                            sizeX=str(size_x),
                            sizeY="46",
                            color=frame.get_header_color())
                
                # Add diagonal bars decoration
                bars = ET.SubElement(class_container, "StaticImage", origin="0 0", align="lt")
                ET.SubElement(bars, "RenderObject2D",
                            texture="data/textures/gui/deploy/deploy_class_diagonalbars.dds",
                            color="0c0b0b33")
                
                # Add left bar
                left_bar = ET.SubElement(class_container, "StaticImage",
                                       name="#ClassBackgroundLeftBar",
                                       origin="-16 0",
                                       align="lt")
                ET.SubElement(left_bar, "RenderObject2D",
                            texture="data/textures/gui/square.tga",
                            sizeX="8",
                            sizeY=str(size_y),
                            color="f97b0380")
                
                # Add class name text
                text_y_offset = 123 if frame.height_cells == 2 else 50
                class_name = ET.SubElement(class_container, "StaticText",
                                         name="#ClassName",
                                         origin=f"-6 {text_y_offset}",
                                         text=frame.class_text,
                                         align="r",
                                         font="header_4",
                                         textColor="211e1d")
                
                # Add class icon
                class_icon = ET.SubElement(class_container, "StaticImage",
                                         name="#ClassIcon",
                                         origin=f"8 {text_y_offset}",
                                         align="l")
                ET.SubElement(class_icon, "RenderObject2D",
                            texture="data/textures/gui/deploy/class_name_icon_assaulter.dds",
                            color="ffffffff")
                
                # Add deployment slots
                slot_count = 0
                if frame.height_cells == 2:  # 4x2 box
                    origins = frame.get_slot_container_origin()
                    slots_per_row = 4
                    
                    # Create first row of slots
                    first_row = ET.SubElement(class_container, "Item", origin=origins[0])
                    for slot in range(slots_per_row):
                        slot_x = slot * 90
                        slot_img = ET.SubElement(first_row, "StaticImage",
                                               name=f"#slot{slot_count}",
                                               origin=f"{slot_x} 0")
                        ET.SubElement(slot_img, "RenderObject2D",
                                    texture="data/textures/gui/deploy/deploy_trooperbackground_01.tga")
                        slot_count += 1
                    
                    # Create second row of slots
                    second_row = ET.SubElement(class_container, "Item", origin=origins[1])
                    for slot in range(slots_per_row):
                        slot_x = slot * 90
                        slot_img = ET.SubElement(second_row, "StaticImage",
                                               name=f"#slot{slot_count}",
                                               origin=f"{slot_x} 0")
                        ET.SubElement(slot_img, "RenderObject2D",
                                    texture="data/textures/gui/deploy/deploy_trooperbackground_01.tga")
                        slot_count += 1
                else:  # 2x1 or 4x1 box
                    slots_row = ET.SubElement(class_container, "Item", origin=frame.get_slot_container_origin())
                    for slot in range(frame.width_cells):
                        slot_x = slot * 90
                        slot_img = ET.SubElement(slots_row, "StaticImage",
                                               name=f"#slot{slot_count}",
                                               origin=f"{slot_x} 0")
                        ET.SubElement(slot_img, "RenderObject2D",
                                    texture="data/textures/gui/deploy/deploy_trooperbackground_01.tga")
                        slot_count += 1
            
            # Create class-specific parent Items after UI elements
            global_slot_count = 0  # Track total slots across all classes
            for class_name in self.available_classes + ["unused"]:
                class_item = ET.SubElement(container, "StaticImage", 
                                         name=f"{class_name}Class",
                                         origin="0 0")
                
                # Add slots for this class
                for frame in sorted_frames:
                    frame = frame[1]  # Get the frame object from the tuple
                    for slot_idx in range(frame.total_slots):
                        current_class = frame.get_slot_class(slot_idx)
                        if current_class + "Class" == class_name + "Class":
                            # Calculate slot position
                            xml_x, xml_y = frame.get_xml_position()
                            if frame.width_cells == 2:  # 2x1 box
                                base_x = xml_x + (-45)
                                x_pos = base_x + (slot_idx * 90)
                                y_pos = xml_y + (-24)
                            else:  # 4x1 or 4x2 box
                                base_x = -2 + (-138)
                                x_pos = base_x + ((slot_idx % 4) * 90)
                                if frame.height_cells == 2:  # 4x2 box
                                    container_y = -299
                                    y_pos = container_y + (-3) + (30 if slot_idx < 4 else -70)
                                else:  # 4x1 box
                                    y_pos = xml_y + (-24)
                            
                            # Add the slot to the class container with a unique global slot number
                            slot_img = ET.SubElement(class_item, "StaticImage",
                                                   name=f"#slot{global_slot_count}",
                                                   origin=f"{x_pos} {y_pos}")
                            ET.SubElement(slot_img, "RenderObject2D",
                                        texture="data/textures/gui/deploy/deploy_trooperbackground_01.tga")
                            global_slot_count += 1
            
            print(f"Writing XML to {xml_path}")
            # Write to file while preserving formatting
            xml_str = '<?xml version="1.0" ?>\n'
            xml_str += ET.tostring(root, encoding='unicode', method='xml')
            
            # Basic XML pretty printing
            import xml.dom.minidom
            dom = xml.dom.minidom.parseString(xml_str)
            pretty_xml = dom.toprettyxml(indent='\t')
            
            # Remove any indentation before the XML declaration
            pretty_xml = pretty_xml.lstrip()
            
            with open(xml_path, 'w', encoding='utf-8') as file:
                file.write(pretty_xml)
            
            if show_popup:
                messagebox.showinfo("Success", "Layout saved successfully!")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save layout: {str(e)}")
            print(f"Save layout error details: {str(e)}")

    def add_box(self, width_cells, height_cells=1):
        title = f"Row {self.next_box_number}"
        # Start at row 0 to prevent clipping
        frame = DraggableFrame(self.grid_container, self, title, "#cb893e", 0, width_cells, height_cells)
        
        # Get initial visual position
        visual_x, visual_y = frame.get_visual_position()
        frame.place(x=visual_x, y=visual_y)
        
        self.draggable_frames[title] = frame
        self.next_box_number += 1
        self.update_row_markers()

    def remove_box(self, box):
        # Remove from draggable_frames
        for key, value in list(self.draggable_frames.items()):
            if value == box:
                del self.draggable_frames[key]
                break
        box.destroy()
        self.update_row_markers()
        # Clear info panel if the removed box was selected
        if self.selected_box == box:
            self.selected_box = None
            self.info_content.config(state='normal')
            self.info_content.delete(1.0, tk.END)
            self.info_content.config(state='disabled')
            # Clear class text entry
            self.class_text_entry.delete(0, tk.END)
            # Clear slot settings
            for widget in self.slot_settings_frame.winfo_children():
                widget.destroy()

    def __str__(self):
        """String representation of the editor state"""
        return f"GUIEditor(boxes={len(self.draggable_frames)}, next_box={self.next_box_number})"

    def __repr__(self):
        """Detailed representation of the editor state"""
        return f"GUIEditor(boxes={list(self.draggable_frames.keys())}, next_box={self.next_box_number})"

    def reload_xml(self):
        try:
            xml_path = "Example mod/Baby seals/gui/seals_deploy.xml"
            tree = ET.parse(xml_path)
            root = tree.getroot()
            
            # Clear existing frames
            for frame in list(self.draggable_frames.values()):
                frame.destroy()
            self.draggable_frames.clear()
            self.next_box_number = 1
            
            # Find the main container (BABY SEALS)
            container = root.find(".//Item[@name='BABY SEALS']")
            if container is not None:
                # First, load any existing slot assignments from class containers
                existing_slots = {}  # Store slot assignments from class containers
                for class_item in container.findall("StaticImage"):
                    class_name = class_item.get("name", "")
                    if class_name.endswith("Class") and not class_name.startswith("Row"):
                        for slot in class_item.findall(".//StaticImage"):
                            if slot.get("name", "").startswith("#slot"):
                                origin = slot.get("origin", "0 0")
                                existing_slots[origin] = class_name
                print(f"Found existing slot assignments: {existing_slots}")
                
                # Process each StaticImage that represents a box (not a class container)
                for class_elem in container.findall("StaticImage"):
                    name = class_elem.get("name", "")
                    # Only process boxes (Row X), skip class containers
                    if not name.endswith("Class") or not name.startswith("Row"):
                        continue
                        
                    # Get the XML origin
                    origin = class_elem.get("origin", "0 0").split()
                    xml_x = int(origin[0])
                    xml_y = int(origin[1])
                    
                    # Determine box type and row index based on XML position and size
                    render_obj = class_elem.find("RenderObject2D")
                    if render_obj is not None:
                        size_x = int(render_obj.get("sizeX", "184"))
                        size_y = int(render_obj.get("sizeY", "148"))
                    
                    if size_x == 184:  # 2x1 box
                        width_cells = 2
                        height_cells = 1
                        # Convert XML position to visual position
                        if xml_x == -98:  # Left
                            visual_x = 0
                        elif xml_x == 0:  # Middle
                            visual_x = 98
                        else:  # Right (98)
                            visual_x = 196
                        
                        # Calculate row index based on Y position
                        if xml_y == 71:  # First row
                            row_index = 0
                        else:
                            # Calculate how many rows down from 71
                            row_index = (71 - xml_y) // 148
                        
                    elif size_x == 374 and size_y == 142:  # 4x1 box
                        width_cells = 4
                        height_cells = 1
                        visual_x = 2
                        # Calculate row index same way as 2x1 boxes
                        if xml_y == 71:  # First row
                            row_index = 0
                        else:
                            row_index = (71 - xml_y) // 148
                        
                    elif size_x == 374 and size_y == 290:  # 4x2 box
                        width_cells = 4
                        height_cells = 2
                        visual_x = 2
                        # Calculate row index same way as other boxes
                        if xml_y == 71:  # First row
                            row_index = 0
                        else:
                            row_index = (71 - xml_y) // 148
                    else:
                        continue

                    # Create the frame
                    title = name.replace("Class", "")
                    frame = DraggableFrame(self.grid_container, self, title, "#cb893e", 
                                         row_index, width_cells, height_cells)

                    # Position the frame
                    visual_y = row_index * self.row_height
                    frame.place(x=visual_x, y=visual_y)
                    
                    # Set display name
                    class_name_elem = class_elem.find(".//StaticText[@name='#ClassName']")
                    if class_name_elem is not None:
                        display_name = class_name_elem.get("text", "ASSAULTER")
                        frame.set_class_text(display_name)
                    
                    # Calculate slot positions and find their assignments
                    if frame.width_cells == 2:  # 2x1 box
                        base_x = xml_x + (-45)
                        for slot_idx in range(2):
                            x_pos = base_x + (slot_idx * 90)
                            y_pos = xml_y + (-24)
                            slot_origin = f"{x_pos} {y_pos}"
                            
                            # Find which class container has this slot
                            assigned_class = "unusedClass"
                            for class_container in container.findall("StaticImage"):
                                class_name = class_container.get("name", "")
                                if class_name.endswith("Class") and not class_name.startswith("Row"):
                                    for slot in class_container.findall(".//StaticImage"):
                                        if slot.get("origin", "") == slot_origin:
                                            assigned_class = class_name
                                            break
                            
                            # Set the slot's class (remove "Class" suffix for display)
                            if assigned_class != "unusedClass":
                                frame.set_slot_class(slot_idx, assigned_class[:-5])
                            else:
                                frame.set_slot_class(slot_idx, "unused")
                            
                    else:  # 4x1 or 4x2 box
                        base_x = -2 + (-138)
                        for row in range(height_cells):
                            for col in range(4):
                                slot_idx = row * 4 + col
                                x_pos = base_x + (col * 90)
                                if height_cells == 2:  # 4x2 box
                                    container_y = -299
                                    y_pos = container_y + (-3) + (30 if row == 0 else -70)
                                else:  # 4x1 box
                                    y_pos = xml_y + (-24)
                                
                                slot_origin = f"{x_pos} {y_pos}"
                                
                                # Find which class container has this slot
                                assigned_class = "unusedClass"
                                for class_container in container.findall("StaticImage"):
                                    class_name = class_container.get("name", "")
                                    if class_name.endswith("Class") and not class_name.startswith("Row"):
                                        for slot in class_container.findall(".//StaticImage"):
                                            if slot.get("origin", "") == slot_origin:
                                                assigned_class = class_name
                                                break
                                
                                # Set the slot's class (remove "Class" suffix for display)
                                if assigned_class != "unusedClass":
                                    frame.set_slot_class(slot_idx, assigned_class[:-5])
                                else:
                                    frame.set_slot_class(slot_idx, "unused")
                    
                    self.draggable_frames[title] = frame
                    
                    # Update next box number
                    try:
                        row_num = int(title.split()[1])
                        self.next_box_number = max(self.next_box_number, row_num + 1)
                    except (IndexError, ValueError):
                        pass
            
            self.update_row_markers()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to reload XML: {str(e)}")
            print(f"XML reload error details: {str(e)}")