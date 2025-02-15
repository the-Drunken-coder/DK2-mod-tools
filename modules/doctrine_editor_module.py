# File: doctrine_editor_module.py
# This module provides a Doctrine Editor plugin for DK2 modding tools
# Adapted from doctrine_test.py

import tkinter as tk
from tkinter import ttk
import xml.etree.ElementTree as ET
import xml.dom.minidom
import os
import logging
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
import tkinter.messagebox as messagebox

# File paths (adjust as needed)
DOCTRINE_TREE_XML = r"C:\Program Files (x86)\Steam\steamapps\common\DoorKickers2\mods\3418188703\gui\raider_doctrine_tree.xml"
DOCTRINE_NODES_XML = r"C:\Program Files (x86)\Steam\steamapps\common\DoorKickers2\mods\3418188703\units\msoc_doctrine_nodes.xml"
UNIT_XML = r"C:\Program Files (x86)\Steam\steamapps\common\DoorKickers2\mods\3418188703\units\msoc_unit.xml"

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants for UI layout
BASE_WIDTH = 1920
BASE_HEIGHT = 1080
MIN_WINDOW_WIDTH = 800
MIN_WINDOW_HEIGHT = 600
GRID_CELL_SIZE_X = 160  # Horizontal spacing between nodes
GRID_CELL_SIZE_Y = 180  # Vertical spacing between nodes
GRID_PADDING = 10
XML_OFFSET_X = 80  # Default X offset for XML export
XML_OFFSET_Y = 88  # Default Y offset for XML export

# Available skills and their descriptions
SKILLS = {
    'SurvivalRate': 'Doubles chance to become incapacitated instead of dying',
    'PistolTransition': 'Auto-switches to pistol when empty on main',
    'SelfFirstAid': 'Heals at end of mission instead of next day',
    'AdvancedLanguage': 'Enables order to send Civilians to nearest exit / out of the room',
    'Backstabbing': 'Melee deals more stun / damage when hitting from behind',
    'PriorityBombers': 'Prioritize suicide bombers and will have a 2x crit chance on them',
    'SpeedyRifles': 'Increases move/turn speed when a rifle is equipped and is not firing',
    'AdvanceIntel': 'Make visible objectives/hostages/bombs (value sets number per level)',
    'HumintNetwork': 'Reveal enemies at mission start (value sets number per level)',
    'Persuasion': 'New order: persuade civilians/surrendered to reveal nearby enemies',
    'Ambush': 'Keeps shooting from stealth UNAWARE bonus for 100ms per-point',
    'Concealment': 'Gives extra concealment equal to skill value',
    'ConcealPistols': 'Reduces pistol concealment penalty by skill amount',
    'BasicLanguage': 'Scares nearby civilians away (skill amount as scare radius)'
}

# Skills that require a value parameter
SKILLS_WITH_VALUES = {
    'AdvanceIntel',
    'HumintNetwork',
    'Persuasion',
    'Ambush',
    'Concealment',
    'ConcealPistols',
    'BasicLanguage'
}

# Equipment types and their modifiable attributes
EQUIPMENT_TYPES = {
    'rifle': {'name': 'Rifles', 'description': 'Standard combat rifles'},
    'smg': {'name': 'Submachine Guns', 'description': 'Close quarters automatic weapons'},
    'shotgun': {'name': 'Shotguns', 'description': 'Close range scatter weapons'},
    'pistol': {'name': 'Handguns', 'description': 'Sidearms and backup weapons'},
    'sniper': {'name': 'Sniper Rifles', 'description': 'Long range precision rifles'},
    'lmg': {'name': 'Light Machine Guns', 'description': 'Support weapons for sustained fire'},
    'launcher': {'name': 'Launchers', 'description': 'Grenade launchers and other explosive weapons'},
    'armor': {'name': 'Body Armor', 'description': 'Protective gear for the torso'},
    'helmet': {'name': 'Helmet', 'description': 'Head protection equipment'},
    'melee': {'name': 'Melee Weapon', 'description': 'Close combat weapons'}
}

# Define which attributes are valid for each equipment type
EQUIPMENT_TYPE_ATTRIBUTES = {
    'rifle': ['readyTime', 'accuracyAdd', 'recoilAdd', 'damageAdd', 'penetrationAdd', 'suppressionAdd', 'reloadTimeAdd', 'weight', 'concealment'],
    'smg': ['readyTime', 'accuracyAdd', 'recoilAdd', 'damageAdd', 'penetrationAdd', 'suppressionAdd', 'reloadTimeAdd', 'weight', 'concealment'],
    'shotgun': ['readyTime', 'accuracyAdd', 'recoilAdd', 'damageAdd', 'penetrationAdd', 'suppressionAdd', 'reloadTimeAdd', 'weight', 'concealment'],
    'pistol': ['readyTime', 'accuracyAdd', 'recoilAdd', 'damageAdd', 'penetrationAdd', 'reloadTimeAdd', 'weight', 'concealment'],
    'sniper': ['readyTime', 'accuracyAdd', 'recoilAdd', 'damageAdd', 'penetrationAdd', 'suppressionAdd', 'reloadTimeAdd', 'weight', 'concealment'],
    'lmg': ['readyTime', 'accuracyAdd', 'recoilAdd', 'damageAdd', 'penetrationAdd', 'suppressionAdd', 'reloadTimeAdd', 'weight', 'concealment'],
    'launcher': ['readyTime', 'accuracyAdd', 'damageAdd', 'reloadTimeAdd', 'weight', 'concealment'],
    'armor': ['protection', 'weight', 'concealment'],
    'helmet': ['protection', 'weight', 'concealment'],
    'melee': ['readyTime', 'damageAdd', 'weight']
}

EQUIPMENT_ATTRIBUTES = {
    'readyTime': {
        'name': 'Ready Time',
        'description': 'Time to ready weapon after movement/actions',
        'format': 'ms',
        'example': '-50',
        'affects': 'Weapon handling speed',
        'category': 'Handling'
    },
    'accuracyAdd': {
        'name': 'Accuracy',
        'description': 'Bonus or penalty to base accuracy',
        'format': 'percentage',
        'example': '+10',
        'affects': 'Hit probability',
        'category': 'Combat'
    },
    'recoilAdd': {
        'name': 'Recoil',
        'description': 'Modifies weapon recoil and control',
        'format': 'percentage',
        'example': '-15',
        'affects': 'Weapon stability',
        'category': 'Combat'
    },
    'damageAdd': {
        'name': 'Damage',
        'description': 'Additional damage dealt by the weapon',
        'format': 'flat value',
        'example': '+5',
        'affects': 'Damage output',
        'category': 'Combat'
    },
    'penetrationAdd': {
        'name': 'Penetration',
        'description': 'Bonus to armor penetration capability',
        'format': 'flat value',
        'example': '+2',
        'affects': 'Armor penetration',
        'category': 'Combat'
    },
    'suppressionAdd': {
        'name': 'Suppression',
        'description': 'Changes effectiveness of suppressing enemies',
        'format': 'percentage',
        'example': '+20',
        'affects': 'Enemy suppression',
        'category': 'Combat'
    },
    'reloadTimeAdd': {
        'name': 'Reload Time',
        'description': 'Time to reload the weapon',
        'format': 'ms',
        'example': '-200',
        'affects': 'Reload speed',
        'category': 'Handling'
    },
    'weight': {
        'name': 'Weight',
        'description': 'Weight modifier affecting mobility',
        'format': 'percentage',
        'example': '-10',
        'affects': 'Movement speed',
        'category': 'General'
    },
    'protection': {
        'name': 'Protection',
        'description': 'Additional protection value (armor/helmet only)',
        'format': 'flat value',
        'example': '+1',
        'affects': 'Damage reduction',
        'category': 'Defense'
    },
    'concealment': {
        'name': 'Concealment',
        'description': 'Affects detection by enemies',
        'format': 'flat value',
        'example': '+2',
        'affects': 'Stealth capability',
        'category': 'General'
    }
}

COLORS = {
    'background': "#211e1d",
    'section': {
        'background': "#2a2724",
        'header': "#312e2a",
        'border': "#3a3631",
        'grid': "#2a2724"
    },
    'text': "#f0e3cc",
    'node': {
        'normal': "#3a3631",
        'selected': "#4a4641",
        'hover': "#4a4641",
        'disabled': "#928a7c",
        'active': "#f97b03"
    }
}

class CreateToolTip:
    """Create a tooltip for a given widget"""
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tooltip = None
        self.widget.bind('<Enter>', self.enter)
        self.widget.bind('<Leave>', self.leave)
    
    def enter(self, event=None):
        x, y, _, _ = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 20
        self.tooltip = tk.Toplevel(self.widget)
        self.tooltip.wm_overrideredirect(True)
        self.tooltip.wm_geometry(f"+{x}+{y}")
        label = tk.Label(
            self.tooltip,
            text=self.text,
            justify='left',
            background=COLORS['section']['background'],
            foreground=COLORS['text'],
            relief='solid',
            borderwidth=1,
            wraplength=180,
            padx=5,
            pady=3
        )
        label.pack()
    
    def leave(self, event=None):
        if self.tooltip:
            self.tooltip.destroy()
            self.tooltip = None

@dataclass
class DoctrineNodeDefinition:
    name: str
    display_name: str
    description: str
    icon: str
    requirements: List[str]
    modifiers: Dict[str, str]
    max_level: int = 1

@dataclass
class DoctrineNode:
    name: str
    x: int
    y: int
    align: str = 'lt'
    width: int = 120
    height: int = 120
    connections: List['DoctrineNode'] = None
    definition: Optional[DoctrineNodeDefinition] = None
    level: int = 1
    
    def __post_init__(self):
        if self.connections is None:
            self.connections = []
    
    def add_connection(self, target_node: 'DoctrineNode'):
        if target_node not in self.connections:
            self.connections.append(target_node)
    
    def remove_connection(self, target_node: 'DoctrineNode'):
        if target_node in self.connections:
            self.connections.remove(target_node)
            
    def get_display_name(self) -> str:
        if self.definition:
            return self.definition.display_name
        return self.name.split('_')[-1]

@dataclass
class Section:
    name: str
    x: int
    y: int
    width: int
    height: int
    align: str = 'lt'
    nodes: List[DoctrineNode] = None
    
    def __post_init__(self):
        if self.nodes is None:
            self.nodes = []
    
    def add_node(self, node: DoctrineNode):
        self.nodes.append(node)
    
    def get_aligned_position(self, base_x: int, base_y: int) -> Tuple[int, int]:
        x = base_x
        y = base_y
        if 'c' in self.align:
            x = base_x - (self.width // 2)
        elif 'r' in self.align:
            x = base_x - self.width
        if 'm' in self.align:
            y = base_y - (self.height // 2)
        elif 'b' in self.align:
            y = base_y - self.height
        return (x, y)


# DoctrineEditor is a Frame to be embedded in a notebook in DK2 modding tools
class DoctrineEditor(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.configure(bg=COLORS['background'])
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        # Data structures
        self.sections: Dict[str, Section] = {}
        self.section_bounds: Dict[str, Dict] = {}
        self.scale_factor = 1.0
        self.last_width = BASE_WIDTH
        self.last_height = BASE_HEIGHT
        self.dragging_node = None
        self.node_definitions = {}
        self.selected_node = None
        
        # Build UI
        self.create_widgets()
        self.load_doctrine_nodes()
        self.load_doctrine_tree()
        
        # Bind canvas events
        self.canvas.tag_bind("node", "<Button-1>", self.on_node_press)
        self.canvas.tag_bind("node", "<B1-Motion>", self.on_node_drag)
        self.canvas.tag_bind("node", "<ButtonRelease-1>", self.on_node_release)
        self.canvas.tag_bind("node", "<Button-3>", self.on_node_right_click)
        
        self.bind('<Configure>', self.on_window_resize)

    def create_widgets(self):
        # Main container
        self.main_container = tk.Frame(self, bg=COLORS['background'])
        self.main_container.grid(row=0, column=0, sticky="nsew")
        self.main_container.grid_rowconfigure(1, weight=1)
        self.main_container.grid_columnconfigure(0, weight=1)
        
        # Toolbar
        toolbar = tk.Frame(self.main_container, bg=COLORS['background'])
        toolbar.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        
        create_node_btn = ttk.Button(toolbar, text="Add Node", command=self.create_new_node)
        create_node_btn.pack(side="left", padx=5)
        
        self.connection_mode = tk.BooleanVar(value=False)
        self.connection_btn = ttk.Checkbutton(toolbar, text="Connection Mode", variable=self.connection_mode, command=self.toggle_connection_mode)
        self.connection_btn.pack(side="left", padx=5)

        save_xml_btn = ttk.Button(toolbar, text="Save to XML", command=self.save_to_xml)
        save_xml_btn.pack(side="right", padx=5)
        
        # Canvas frame
        canvas_frame = tk.Frame(self.main_container, bg=COLORS['background'])
        canvas_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        canvas_frame.grid_rowconfigure(0, weight=1)
        canvas_frame.grid_columnconfigure(0, weight=1)
        
        self.canvas = tk.Canvas(canvas_frame, bg=COLORS['background'], highlightthickness=0, width=MIN_WINDOW_WIDTH, height=MIN_WINDOW_HEIGHT)
        self.v_scrollbar = ttk.Scrollbar(canvas_frame, orient="vertical", command=self.canvas.yview)
        self.h_scrollbar = ttk.Scrollbar(canvas_frame, orient="horizontal", command=self.canvas.xview)
        self.canvas.configure(xscrollcommand=self.h_scrollbar.set, yscrollcommand=self.v_scrollbar.set)
        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.v_scrollbar.grid(row=0, column=1, sticky="ns")
        self.h_scrollbar.grid(row=1, column=0, sticky="ew")
        self.canvas.bind("<MouseWheel>", self.on_mousewheel)
        self.canvas.bind("<Control-MouseWheel>", self.on_zoom)
        
        # Initialize connection variables
        self.connection_source = None

    def on_window_resize(self, event):
        if event.widget == self:
            self.last_width = event.width
            self.last_height = event.height
            width_scale = (event.width - 20) / BASE_WIDTH
            height_scale = (event.height - 20) / BASE_HEIGHT
            self.scale_factor = 1.40 * min(width_scale, height_scale)
            self.draw_doctrine_tree()

    def on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")

    def on_zoom(self, event):
        if event.delta > 0:
            self.scale_factor *= 1.1
        else:
            self.scale_factor *= 0.9
        self.draw_doctrine_tree()
    
    def get_scaled_coords(self, x: int, y: int, width: int, height: int, align: str = 'lt') -> Tuple[int, int, int, int]:
        base_x = x
        base_y = abs(y)
        if 'r' in align:
            base_x = BASE_WIDTH + x
        elif 'c' in align:
            base_x = (BASE_WIDTH // 2) + x
        if 'b' in align:
            base_y = BASE_HEIGHT - y
        elif 'm' in align:
            base_y = (BASE_HEIGHT // 2) + y
        scaled_x = int(base_x * self.scale_factor)
        scaled_y = int(base_y * self.scale_factor)
        scaled_width = int(width * self.scale_factor)
        scaled_height = int(height * self.scale_factor)
        return scaled_x, scaled_y, scaled_width, scaled_height
    
    def load_doctrine_nodes(self):
        try:
            # First try to read the file contents
            with open(DOCTRINE_NODES_XML, 'r', encoding='utf-8') as f:
                content = f.read().strip()
            
            # Clean up the content by removing all XML declarations and extra whitespace
            content = '\n'.join(line for line in content.split('\n') if line.strip())
            if '<?xml' in content:
                # Keep only the first XML declaration
                declarations = content.count('<?xml')
                if declarations > 1:
                    # Remove all declarations and add a single one at the start
                    content = content.replace('<?xml version="1.0" encoding="utf-8"?>', '')
                    content = content.replace('<?xml version=\'1.0\' encoding=\'utf-8\'?>', '')
                    content = '<?xml version="1.0" encoding="utf-8"?>\n' + content.strip()
            
            # If no XML declaration exists, add one
            if not content.startswith('<?xml'):
                content = '<?xml version="1.0" encoding="utf-8"?>\n' + content
            
            # Ensure content starts with DoctrineNodes if not present
            if '<DoctrineNodes>' not in content:
                content = content.replace('<?xml version="1.0" encoding="utf-8"?>\n',
                                       '<?xml version="1.0" encoding="utf-8"?>\n<DoctrineNodes>\n')
                content += '\n</DoctrineNodes>'
            
            # Parse the cleaned content
            root = ET.fromstring(content)
            
            for node_elem in root.findall(".//Node"):
                name = node_elem.get('name')
                if not name:
                    continue
                display_name = node_elem.get('nameUI', name)
                description = node_elem.get('description', '')
                icon = node_elem.get('icon', '')
                max_level = int(node_elem.get('maxLevel', '1'))
                requirements = []
                reqs_elem = node_elem.find('Requirements')
                if reqs_elem is not None:
                    for req in reqs_elem.findall('Requirement'):
                        req_name = req.get('name')
                        if req_name:
                            requirements.append(req_name)
                modifiers = {}
                for modifier in node_elem.findall('.//Modifier'):
                    mod_type = modifier.get('type', '')
                    mod_value = modifier.get('value', '')
                    if mod_type:
                        modifiers[mod_type] = mod_value
                node_def = DoctrineNodeDefinition(
                    name=name,
                    display_name=display_name,
                    description=description,
                    icon=icon,
                    requirements=requirements,
                    modifiers=modifiers,
                    max_level=max_level
                )
                self.node_definitions[name] = node_def
                logger.debug(f"Loaded doctrine node definition: {name}")
        except FileNotFoundError:
            logger.error(f"Doctrine nodes file not found: {DOCTRINE_NODES_XML}")
            messagebox.showerror("Error", f"Doctrine nodes file not found: {DOCTRINE_NODES_XML}")
        except ET.ParseError as e:
            logger.error(f"Error parsing doctrine nodes XML: {e}")
            messagebox.showerror("Error", f"Failed to parse doctrine nodes XML: {e}")
        except Exception as e:
            logger.error(f"Error loading doctrine nodes: {e}")
            messagebox.showerror("Error", f"Failed to load doctrine nodes: {e}")
    
    def load_doctrine_tree(self):
        try:
            tree = ET.parse(DOCTRINE_TREE_XML)
            root = tree.getroot()
            self.sections.clear()
            main_container = root.find(".//Item[@name='#MARSOC_DoctrineTree']")
            if not main_container:
                logger.error("Could not find main doctrine tree container")
                return
            for section_elem in main_container.findall("Item[@name]"):
                section_name = section_elem.get('name', '')
                if not section_name or section_name == '#template_doctrine_button':
                    continue
                origin = section_elem.get('origin', '0 0').split()
                x = int(origin[0]) if len(origin) > 0 else 0
                y = int(origin[1]) if len(origin) > 1 else 0
                width = int(section_elem.get('sizeX', 400))
                height = int(section_elem.get('sizeY', 600))
                align = section_elem.get('align', 'lt')
                section = Section(
                    name=section_name,
                    x=x,
                    y=y,
                    width=width,
                    height=height,
                    align=align
                )
                for node_elem in section_elem.findall("./Item[@name]"):
                    node_name = node_elem.get('name', '')
                    if (node_name and 
                        node_name not in ['#template_doctrine_button', '#doctrinenode_disabled', '#doctrinenode_active', 'level'] and
                        not node_name.startswith('#')):
                        origin = node_elem.get('origin', '0 0').split()
                        # Subtract XML offsets from the loaded coordinates
                        x = int(origin[0]) - XML_OFFSET_X if len(origin) > 0 else 0
                        y = int(origin[1]) + XML_OFFSET_Y if len(origin) > 1 else 0  # Add because Y is negative in game coords
                        align = node_elem.get('align', 'lt')
                        node = DoctrineNode(
                            name=node_name,
                            x=x,
                            y=y,
                            align=align
                        )
                        if node_name in self.node_definitions:
                            node.definition = self.node_definitions[node_name]
                            logger.debug(f"Linked node {node_name} to its definition")
                        else:
                            logger.warning(f"No definition found for node: {node_name}")
                        section.add_node(node)
                        logger.debug(f"Added node {node_name} to section {section.name}")
                self.sections[section.name] = section
                logger.debug(f"Loaded section: {section.name}")
            self.draw_doctrine_tree()
        except Exception as e:
            logger.error(f"Error loading doctrine tree: {e}")
            messagebox.showerror("Error", f"Failed to load doctrine tree: {e}")
    
    def draw_doctrine_tree(self):
        self.canvas.delete("all")
        margin_x, margin_y = 50, 50
        scaled_positions = []
        for s in self.sections.values():
            x, y, _, _ = self.get_scaled_coords(s.x, s.y, s.width, s.height, align=s.align)
            scaled_positions.append((x, y))
        if scaled_positions:
            min_x = min(x for x, y in scaled_positions)
            min_y = min(y for x, y in scaled_positions)
        else:
            min_x, min_y = 0, 0
        offset_x = margin_x - min_x
        offset_y = margin_y - min_y
        for section in self.sections.values():
            self.draw_section(section, offset_x, offset_y)
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
    
    def draw_section(self, section: Section, offset_x: int, offset_y: int):
        x, y, width, height = self.get_scaled_coords(section.x, section.y, section.width, section.height, align=section.align)
        self.canvas.create_rectangle(
            x + offset_x, y + offset_y,
            x + width + offset_x, y + height + offset_y,
            fill=COLORS['section']['background'],
            outline=COLORS['section']['border'],
            width=max(1, int(2 * self.scale_factor))
        )
        header_height = int(72 * self.scale_factor)
        self.canvas.create_rectangle(
            x + offset_x, y + offset_y,
            x + width + offset_x, y + header_height + offset_y,
            fill=COLORS['section']['header'],
            outline=COLORS['section']['border'],
            width=max(1, int(2 * self.scale_factor))
        )
        scaled_cell_size_x = int(GRID_CELL_SIZE_X * self.scale_factor)
        scaled_cell_size_y = int(GRID_CELL_SIZE_Y * self.scale_factor)
        drawable_width = width
        drawable_height = height - header_height
        num_cells_x = (drawable_width - scaled_cell_size_x//2) // scaled_cell_size_x
        num_cells_y = (drawable_height - scaled_cell_size_y//2) // scaled_cell_size_y
        total_grid_width = num_cells_x * scaled_cell_size_x
        total_grid_height = num_cells_y * scaled_cell_size_y
        grid_start_x = x + offset_x + (width - total_grid_width) // 2 + scaled_cell_size_x//2
        grid_start_y = y + offset_y + header_height + (drawable_height - total_grid_height) // 2 + scaled_cell_size_y//2
        for i in range(num_cells_x + 1):
            line_x = grid_start_x + i * scaled_cell_size_x - scaled_cell_size_x//2
            self.canvas.create_line(
                line_x, grid_start_y - scaled_cell_size_y//2,
                line_x, grid_start_y + total_grid_height - scaled_cell_size_y//2,
                fill=COLORS['section']['grid'],
                width=1
            )
        for i in range(num_cells_y + 1):
            line_y = grid_start_y + i * scaled_cell_size_y - scaled_cell_size_y//2
            self.canvas.create_line(
                grid_start_x - scaled_cell_size_x//2, line_y,
                grid_start_x + total_grid_width - scaled_cell_size_x//2, line_y,
                fill=COLORS['section']['grid'],
                width=1
            )
        font_size = int(16 * self.scale_factor)
        self.canvas.create_text(
            x + width // 2 + offset_x,
            y + header_height // 2 + offset_y,
            text=f"@menu_doctrine_branch_{section.name}",
            fill=COLORS['text'],
            font=("Arial", max(8, font_size)),
            anchor="center"
        )
        self.section_bounds[section.name] = {
            'x': x + offset_x,
            'y': y + offset_y,
            'width': width,
            'height': height,
            'header_height': header_height,
            'grid_start_x': grid_start_x - scaled_cell_size_x//2,
            'grid_start_y': grid_start_y - scaled_cell_size_y//2,
            'grid_width': total_grid_width,
            'grid_height': total_grid_height,
            'cell_size_x': scaled_cell_size_x,
            'cell_size_y': scaled_cell_size_y,
            'num_cells_x': num_cells_x,
            'num_cells_y': num_cells_y
        }
        self.draw_nodes(section, x + offset_x, y + offset_y)
    
    def draw_nodes(self, section: Section, section_x: int, section_y: int):
        # Define display-only padding (applied only for visual display in the editor)
        display_padding_x = int(35 * self.scale_factor)
        display_padding_y = int(26 * self.scale_factor)
        for node in section.nodes:
            # Get raw scaled coordinates based on the stored game coordinates (without display padding)
            raw_x, raw_y, node_width, node_height = self.get_scaled_coords(node.x, node.y, node.width, node.height, align=node.align)
            # Apply display padding for visualization
            node_x = raw_x + display_padding_x
            node_y = raw_y + display_padding_y
            node_center_x = section_x + node_x + node_width // 2
            node_center_y = section_y + node_y + node_height // 2
            rect_x1 = node_center_x - node_width // 2
            rect_y1 = node_center_y - node_height // 2
            rect_x2 = node_center_x + node_width // 2
            rect_y2 = node_center_y + node_height // 2
            for target in node.connections:
                raw_tx, raw_ty, target_width, target_height = self.get_scaled_coords(target.x, target.y, target.width, target.height, align=target.align)
                target_x = raw_tx + display_padding_x
                target_y = raw_ty + display_padding_y
                target_center_x = section_x + target_x + target_width // 2
                target_center_y = section_y + target_y + target_height // 2
                self.canvas.create_line(
                    node_center_x, node_center_y,
                    target_center_x, target_center_y,
                    fill="#716b5f",
                    width=max(1, int(2 * self.scale_factor))
                )
            self.canvas.create_rectangle(
                rect_x1, rect_y1,
                rect_x2, rect_y2,
                fill="#3a3631",
                outline="#4a4641",
                width=max(1, int(1 * self.scale_factor)),
                tags=("node", f"{section.name}:{node.name}")
            )
            node_font_size = int(10 * self.scale_factor)
            display_name = node.name.split('_')[-1]
            self.canvas.create_text(
                node_center_x,
                node_center_y,
                text=display_name,
                fill=COLORS['text'],
                font=("Arial", max(6, node_font_size)),
                anchor="center",
                width=node_width,
                tags=("node_text", node.name)
            )
    
    def create_new_node(self):
        dialog = tk.Toplevel(self)
        dialog.title("Create New Node")
        dialog.transient(self)
        dialog.grab_set()
        
        # Create main frame with dark theme
        main_frame = tk.Frame(dialog, bg=COLORS['background'])
        main_frame.pack(expand=True, fill='both', padx=10, pady=10)
        
        # Node name entry
        name_frame = tk.Frame(main_frame, bg=COLORS['background'])
        name_frame.pack(fill='x', pady=5)
        
        tk.Label(
            name_frame,
            text="Node Name:",
            bg=COLORS['background'],
            fg=COLORS['text']
        ).pack(side='left', padx=5)
        
        name_var = tk.StringVar()
        name_entry = ttk.Entry(name_frame, textvariable=name_var)
        name_entry.pack(side='left', padx=5, expand=True, fill='x')
        
        # Character count label
        char_count_label = tk.Label(
            name_frame,
            text="0/48",
            bg=COLORS['background'],
            fg=COLORS['text']
        )
        char_count_label.pack(side='left', padx=5)
        
        def update_char_count(*args):
            count = len(name_var.get())
            char_count_label.config(
                text=f"{count}/48",
                fg='red' if count > 48 else COLORS['text']
            )
        
        name_var.trace('w', update_char_count)
        
        # Section selection
        section_frame = tk.Frame(main_frame, bg=COLORS['background'])
        section_frame.pack(fill='x', pady=5)
        
        tk.Label(
            section_frame,
            text="Section:",
            bg=COLORS['background'],
            fg=COLORS['text']
        ).pack(side='left', padx=5)
        
        section_var = tk.StringVar()
        section_combo = ttk.Combobox(section_frame, textvariable=section_var)
        section_combo['values'] = list(self.sections.keys())
        section_combo.pack(side='left', padx=5, expand=True, fill='x')
        
        # Error label
        error_label = tk.Label(
            main_frame,
            text="",
            bg=COLORS['background'],
            fg='red',
            wraplength=250
        )
        error_label.pack(pady=5)
        
        def validate_and_create():
            name = name_var.get().strip()
            section_name = section_var.get()
            
            # Validate name length
            if len(name) > 48:
                error_label.config(text="Node name must not exceed 48 characters")
                return
            
            # Validate name is not empty
            if not name:
                error_label.config(text="Node name cannot be empty")
                return
            
            # Validate section is selected
            if not section_name:
                error_label.config(text="Please select a section")
                return
            
            # Create the node
            section = self.sections[section_name]
            node = DoctrineNode(name, x=0, y=-160, align='lt')
            section.add_node(node)
            self.draw_doctrine_tree()
            dialog.destroy()
        
        # Buttons
        button_frame = tk.Frame(main_frame, bg=COLORS['background'])
        button_frame.pack(fill='x', pady=10)
        
        ttk.Button(
            button_frame,
            text="Create",
            command=validate_and_create
        ).pack(side='right', padx=5)
        
        ttk.Button(
            button_frame,
            text="Cancel",
            command=dialog.destroy
        ).pack(side='right', padx=5)
        
        # Center the dialog
        dialog.geometry("300x200")
        x = self.winfo_rootx() + (self.winfo_width() // 2) - (300 // 2)
        y = self.winfo_rooty() + (self.winfo_height() // 2) - (200 // 2)
        dialog.geometry(f"+{x}+{y}")
    
    def toggle_connection_mode(self):
        if not self.connection_mode.get():
            self.connection_source = None
    
    def on_node_press(self, event):
        if not self.connection_mode.get():
            node_id = self.canvas.find_closest(self.canvas.canvasx(event.x), self.canvas.canvasy(event.y))[0]
            tags = self.canvas.gettags(node_id)
            if len(tags) < 2 or ':' not in tags[1]:
                # Try to find an overlapping item with the proper compound tag
                overlapping_items = self.canvas.find_overlapping(self.canvas.canvasx(event.x), self.canvas.canvasy(event.y), self.canvas.canvasx(event.x), self.canvas.canvasy(event.y))
                found = False
                for item in overlapping_items:
                    t = self.canvas.gettags(item)
                    if len(t) >= 2 and ':' in t[1]:
                        tags = t
                        found = True
                        break
                if not found:
                    return
            try:
                section_name, node_name = tags[1].split(':')
            except Exception:
                return
            self.dragging_node = {
                'section': section_name,
                'node': node_name,
                'start_x': event.x,
                'start_y': event.y
            }
    
    def on_node_drag(self, event):
        if self.dragging_node:
            snapped_x, snapped_y = self.snap_to_grid(self.dragging_node['section'], event.x, event.y)
            if hasattr(self, 'preview_rect'):
                self.canvas.delete(self.preview_rect)
            preview_size = int(120 * self.scale_factor)
            self.preview_rect = self.canvas.create_rectangle(
                snapped_x - preview_size//2,
                snapped_y - preview_size//2,
                snapped_x + preview_size//2,
                snapped_y + preview_size//2,
                outline="#f97b03",
                dash=(5,),
                width=2
            )
    
    def on_node_release(self, event):
        if self.dragging_node:
            snapped_x, snapped_y = self.snap_to_grid(self.dragging_node['section'], event.x, event.y)
            section = self.sections[self.dragging_node['section']]
            for node in section.nodes:
                if node.name == self.dragging_node['node']:
                    bounds = self.section_bounds[section.name]

                    # Calculate relative position from grid start
                    rel_x = snapped_x - bounds['grid_start_x']
                    rel_y = snapped_y - bounds['grid_start_y']

                    # Convert to cell coordinates
                    cell_x = round(rel_x / bounds['cell_size_x'])
                    cell_y = round(rel_y / bounds['cell_size_y'])

                    # Calculate raw game coordinates without display padding
                    game_x = cell_x * GRID_CELL_SIZE_X
                    game_y = -((cell_y * GRID_CELL_SIZE_Y) + 72)  # 72 is the header height in game coordinates

                    node.x = game_x
                    node.y = game_y
                    break
            if hasattr(self, 'preview_rect'):
                self.canvas.delete(self.preview_rect)
            self.dragging_node = None
            self.draw_doctrine_tree()
    
    def snap_to_grid(self, section_name: str, mouse_x: int, mouse_y: int) -> tuple:
        bounds = self.section_bounds.get(section_name)
        if not bounds:
            return mouse_x, mouse_y
        if (mouse_x < bounds['grid_start_x'] or 
            mouse_x > bounds['grid_start_x'] + bounds['grid_width'] or
            mouse_y < bounds['grid_start_y'] or 
            mouse_y > bounds['grid_start_y'] + bounds['grid_height']):
            return mouse_x, mouse_y
        rel_x = mouse_x - bounds['grid_start_x']
        rel_y = mouse_y - bounds['grid_start_y']
        cell_x = round(rel_x / bounds['cell_size_x'])
        cell_y = round(rel_y / bounds['cell_size_y'])
        cell_x = max(0, min(cell_x, bounds['num_cells_x']))
        cell_y = max(0, min(cell_y, bounds['num_cells_y']))
        snapped_x = bounds['grid_start_x'] + cell_x * bounds['cell_size_x']
        snapped_y = bounds['grid_start_y'] + cell_y * bounds['cell_size_y']
        return snapped_x, snapped_y
    
    def on_node_right_click(self, event):
        node_id = self.canvas.find_closest(self.canvas.canvasx(event.x), self.canvas.canvasy(event.y))[0]
        tags = self.canvas.gettags(node_id)
        if len(tags) < 2:
            return
        try:
            section_name, node_name = tags[1].split(':')
        except Exception:
            return
        
        # Create context menu
        context_menu = tk.Menu(self, tearoff=0)
        context_menu.configure(bg=COLORS['section']['background'], fg=COLORS['text'])
        
        # Add menu items
        context_menu.add_command(
            label="Node Settings", 
            command=lambda: self.show_node_settings(section_name, node_name)
        )
        context_menu.add_separator()
        context_menu.add_command(
            label="Delete Node", 
            command=lambda: self.delete_node(section_name, node_name)
        )
        context_menu.add_command(
            label="Edit Level", 
            command=lambda: self.edit_node_level(section_name, node_name)
        )
        context_menu.add_separator()
        context_menu.add_checkbutton(
            label="Connection Mode",
            variable=self.connection_mode,
            command=self.toggle_connection_mode
        )
        
        # Show the menu at event position
        try:
            context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            context_menu.grab_release()
            
    def edit_node_level(self, section_name: str, node_name: str):
        """Open a dialog to edit the node's level"""
        node = next((node for node in self.sections[section_name].nodes if node.name == node_name), None)
        if not node:
            return
            
        dialog = tk.Toplevel(self)
        dialog.title("Edit Node Level")
        dialog.configure(bg=COLORS['background'])
        dialog.transient(self)
        dialog.grab_set()
        
        # Center the dialog
        dialog.geometry("250x120")
        x = self.winfo_rootx() + (self.winfo_width() // 2) - (250 // 2)
        y = self.winfo_rooty() + (self.winfo_height() // 2) - (120 // 2)
        dialog.geometry(f"+{x}+{y}")
        
        # Create and pack widgets
        frame = tk.Frame(dialog, bg=COLORS['background'])
        frame.pack(expand=True, fill='both', padx=10, pady=10)
        
        tk.Label(frame, text="Node Level:", bg=COLORS['background'], fg=COLORS['text']).pack(pady=5)
        
        level_var = tk.StringVar(value=str(node.level))
        level_entry = ttk.Entry(frame, textvariable=level_var)
        level_entry.pack(pady=5)
        
        def on_ok():
            try:
                new_level = int(level_var.get())
                if new_level < 1:
                    messagebox.showerror("Error", "Level must be greater than 0")
                    return
                node.level = new_level
                self.draw_doctrine_tree()
                dialog.destroy()
            except ValueError:
                messagebox.showerror("Error", "Please enter a valid number")
                
        button_frame = tk.Frame(frame, bg=COLORS['background'])
        button_frame.pack(fill='x', pady=10)
        
        ttk.Button(button_frame, text="OK", command=on_ok).pack(side='right', padx=5)
        ttk.Button(button_frame, text="Cancel", command=dialog.destroy).pack(side='right')
    
    def delete_node(self, section_name: str, node_name: str):
        """Delete a node and all its connections"""
        if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete node '{node_name}'?"):
            try:
                # Find the node to delete
                section = self.sections.get(section_name)
                if not section:
                    logger.error(f"Section {section_name} not found")
                    return
                
                # Find and remove the node from its section
                node_to_delete = None
                for node in section.nodes:
                    if node.name == node_name:
                        node_to_delete = node
                        break
                
                if node_to_delete:
                    # Remove this node from all other nodes' connections
                    for s in self.sections.values():
                        for n in s.nodes:
                            if node_to_delete in n.connections:
                                n.connections.remove(node_to_delete)
                    
                    # Remove the node from its section
                    section.nodes.remove(node_to_delete)
                    
                    # If this was the selected node, clear selection
                    if self.selected_node and self.selected_node.name == node_name:
                        self.selected_node = None
                        self.update_info_panel()
                    
                    # Redraw the tree
                    self.draw_doctrine_tree()
                    logger.info(f"Successfully deleted node {node_name}")
                else:
                    logger.error(f"Node {node_name} not found in section {section_name}")
            except Exception as e:
                logger.error(f"Error deleting node: {str(e)}")
                messagebox.showerror("Error", f"Failed to delete node: {str(e)}")
    
    def save_to_xml(self):
        try:
            # First, check all files exist and are accessible
            required_files = {
                'doctrine_nodes': DOCTRINE_NODES_XML,
                'doctrine_tree': DOCTRINE_TREE_XML,
                'unit': UNIT_XML
            }
            
            for file_type, file_path in required_files.items():
                if not os.path.exists(file_path):
                    raise FileNotFoundError(f"Required {file_type} file not found: {file_path}")
                if not os.access(file_path, os.W_OK):
                    raise PermissionError(f"No write permission for {file_type} file: {file_path}")
            
            # Load all required XML files
            tree_nodes = ET.parse(DOCTRINE_NODES_XML)
            tree_layout = ET.parse(DOCTRINE_TREE_XML)
            tree_unit = ET.parse(UNIT_XML)
            
            root_nodes = tree_nodes.getroot()
            root_layout = tree_layout.getroot()
            root_unit = tree_unit.getroot()
            
            # Track node name changes
            name_changes = []
            active_nodes = set()
            
            # Check for name changes and validate lengths
            for section in self.sections.values():
                for node in section.nodes:
                    if len(node.name) > 48:
                        raise ValueError(f"Node name '{node.name}' exceeds maximum length of 48 characters")
                    
                    # Check if this is a renamed node
                    old_name = None
                    existing_node = root_nodes.find(f".//Node[@name='{node.name}']")
                    if existing_node is None:
                        # Look for a node with matching display name or description
                        for old_node in root_nodes.findall(".//Node"):
                            if (old_node.get('nameUI', '').lower() == f"@{node.name.lower()}_name" or
                                old_node.get('description', '').lower() == f"@{node.name.lower()}_desc"):
                                old_name = old_node.get('name')
                                name_changes.append((old_name, node.name))
                                break
                    
                    active_nodes.add(node.name)
            
            # If there are name changes, show warning dialog
            if name_changes:
                warning_msg = "The following node names have changed:\n\n"
                for old_name, new_name in name_changes:
                    warning_msg += f"• {old_name} → {new_name}\n"
                warning_msg += "\nPlease ensure you update these names in:\n"
                warning_msg += "1. units.xml (for each unit's doctrine)\n"
                warning_msg += "2. gui/doctrine.xml\n\n"
                warning_msg += "Do you want to continue saving?"
                
                if not messagebox.askyesno("Warning - Node Names Changed", warning_msg):
                    return
            
            # Proceed with saving
            new_root = ET.Element("DoctrineNodes")
            for section in self.sections.values():
                for node in section.nodes:
                    existing_node = root_nodes.find(f".//Node[@name='{node.name}']")
                    if existing_node is not None:
                        existing_node.set("nameUI", f"@{node.name.lower()}_name")
                        existing_node.set("description", f"@{node.name.lower()}_desc")
                        existing_node.set("texturePrefix", "data/textures/gui/doctrines/doctrine_empty")
                    else:
                        node_def = ET.SubElement(new_root, "Node")
                        node_def.set("name", node.name)
                        node_def.set("nameUI", f"@{node.name.lower()}_name")
                        node_def.set("description", f"@{node.name.lower()}_desc")
                        node_def.set("texturePrefix", "data/textures/gui/doctrines/doctrine_empty")
                        equip_mod = ET.SubElement(node_def, "EquipmentModifier")
                        equip_mod.set("target", "rifle")
                        equip_mod.set("readyTime", "-50")
                        equip_mod.set("accuracyAdd", "+10")
            
            # Format and save doctrine nodes XML
            xml_str = ET.tostring(new_root, encoding='unicode')
            dom = xml.dom.minidom.parseString(xml_str)
            pretty_xml = dom.toprettyxml(indent='    ')
            lines = [line for line in pretty_xml.split('\n') if line.strip()]
            formatted_xml = '\n'.join(lines)
            
            with open(DOCTRINE_NODES_XML, 'w', encoding='utf-8') as f:
                if formatted_xml.startswith('<?xml'):
                    formatted_xml = formatted_xml[formatted_xml.find('?>')+2:].strip()
                f.write('<?xml version="1.0" encoding="utf-8"?>\n')
                f.write(formatted_xml)
            
            # Update doctrine tree XML
            main_container = root_layout.find(".//Item[@name='#MARSOC_DoctrineTree']")
            if main_container is None:
                logger.error("Could not find main doctrine tree container")
                return
            
            for section_name, section in self.sections.items():
                section_elem = main_container.find(f".//Item[@name='{section_name}']")
                if section_elem is None:
                    continue
                
                for item in section_elem.findall(".//Item[@name]"):
                    if (item.get('name') not in ['#template_doctrine_button', '#doctrinenode_disabled', '#doctrinenode_active', 'level'] and
                        not item.get('name', '').startswith('#')):
                        parent = section_elem
                        parent.remove(item)
                
                for node in section.nodes:
                    node_elem = ET.SubElement(section_elem, "Item")
                    node_elem.set("name", node.name)
                    xml_x = node.x + XML_OFFSET_X
                    xml_y = node.y - XML_OFFSET_Y
                    node_elem.set("origin", f"{xml_x} {xml_y}")
                    node_elem.set("align", node.align)
                    if node.connections:
                        inactive_link = ET.SubElement(node_elem, "Item", name="#child_link_inactive")
                        inactive_image = ET.SubElement(inactive_link, "StaticImage", origin="0 -60", align="t")
                        ET.SubElement(inactive_image, "RenderObject2D", texture="data/textures/gui/square.tga", sizeX="8", sizeY="44", color="716b5f")
                        arrow_image = ET.SubElement(inactive_image, "StaticImage", origin="0 -16", align="b")
                        ET.SubElement(arrow_image, "RenderObject2D", texture="data/textures/gui/doctrines/doctrine_arrow.dds", color="716b5f")
                        active_link = ET.SubElement(node_elem, "Item", name="#child_link_active")
                        active_image = ET.SubElement(active_link, "StaticImage", origin="0 -60", align="t")
                        ET.SubElement(active_image, "RenderObject2D", texture="data/textures/gui/square.tga", sizeX="8", sizeY="44", color="f97b03")
                        arrow_image = ET.SubElement(active_image, "StaticImage", origin="0 -16", align="b")
                        ET.SubElement(arrow_image, "RenderObject2D", texture="data/textures/gui/doctrines/doctrine_arrow.dds", color="f97b03")
            
            # Save doctrine tree XML
            xml_str = ET.tostring(root_layout, encoding='unicode')
            dom = xml.dom.minidom.parseString(xml_str)
            pretty_xml = dom.toprettyxml(indent='    ')
            pretty_xml = '\n'.join(line for line in pretty_xml.split('\n') if line.strip())
            with open(DOCTRINE_TREE_XML, 'w', encoding='utf-8') as f:
                f.write(pretty_xml)
            
            # Update unit XML
            doctrine_elem = root_unit.find('.//Doctrine')
            if doctrine_elem is not None:
                for child in list(doctrine_elem):
                    doctrine_elem.remove(child)
                for section in self.sections.values():
                    for node in section.nodes:
                        unit_node = ET.SubElement(doctrine_elem, 'Node')
                        unit_node.set('name', node.name)
                        if node.level > 1:
                            unit_node.set('numLevels', str(node.level))
                tree_unit.write(UNIT_XML, encoding='utf-8', xml_declaration=True)
            else:
                logger.warning('No <Doctrine> element found in the units file.')
            
            logger.info("Successfully saved doctrine tree and node definitions")
            if name_changes:
                messagebox.showinfo(
                    "Success", 
                    "Files saved successfully.\n\nRemember to update the node names in:\n" +
                    "1. units.xml (for each unit's doctrine)\n" +
                    "2. gui/doctrine.xml"
                )
            else:
                messagebox.showinfo("Success", "Successfully saved to all XML files")
                
        except FileNotFoundError as e:
            error_msg = f"File not found: {str(e)}"
            logger.error(error_msg)
            messagebox.showerror("Error", error_msg)
        except ET.ParseError as e:
            error_msg = f"Error parsing XML file: {str(e)}"
            logger.error(error_msg)
            messagebox.showerror("Error", error_msg)
        except PermissionError as e:
            error_msg = f"Permission denied: {str(e)}"
            logger.error(error_msg)
            messagebox.showerror("Error", error_msg)
        except Exception as e:
            error_msg = f"Error saving doctrine files: {str(e)}"
            logger.error(error_msg)
            messagebox.showerror("Error", error_msg)

    def draw_node(self, node: DoctrineNode, section: Section, canvas_x: int, canvas_y: int):
        x = canvas_x + node.x
        y = canvas_y + node.y
        node_color = COLORS['node']['normal']
        if node == self.selected_node:
            node_color = COLORS['node']['selected']
        elif node.definition and False:  # placeholder for requirement check
            node_color = COLORS['node']['disabled']
        node_id = self.canvas.create_rectangle(
            x, y, x + node.width, y + node.height,
            fill=node_color,
            outline=COLORS['node']['hover'],
            width=2,
            tags=('node', f"{section.name}:{node.name}")
        )
        display_name = node.get_display_name()
        text_id = self.canvas.create_text(
            x + node.width/2,
            y + node.height/2,
            text=display_name,
            fill=COLORS['text'],
            width=node.width - 10,
            justify=tk.CENTER,
            tags=('node_text', node.name)
        )
        self.canvas.tag_bind(node_id, '<Button-1>', lambda e: self.on_node_click(node))
        self.canvas.tag_bind(text_id, '<Button-1>', lambda e: self.on_node_click(node))
    
    def on_node_click(self, node: DoctrineNode):
        self.selected_node = node
        self.update_info_panel()
        self.draw_doctrine_tree()
    
    def update_info_panel(self):
        if not hasattr(self, 'info_panel'):
            self.info_panel = ttk.Frame(self)
            self.info_panel.pack(side=tk.RIGHT, fill=tk.Y, padx=5, pady=5)
            self.node_name_label = ttk.Label(self.info_panel, text="")
            self.node_name_label.pack(anchor=tk.W, pady=2)
            self.node_desc_label = ttk.Label(self.info_panel, text="", wraplength=200)
            self.node_desc_label.pack(anchor=tk.W, pady=2)
            self.node_level_frame = ttk.Frame(self.info_panel)
            self.node_level_frame.pack(anchor=tk.W, pady=2)
            self.node_level_label = ttk.Label(self.node_level_frame, text="Level: ")
            self.node_level_label.pack(side=tk.LEFT)
            self.level_var = tk.StringVar(value="1")
            self.level_spinbox = ttk.Spinbox(self.node_level_frame, from_=1, to=10, width=5, textvariable=self.level_var, command=self.on_level_change)
            self.level_spinbox.pack(side=tk.LEFT)
            self.reqs_label = ttk.Label(self.info_panel, text="Requirements:", font=('TkDefaultFont', 10, 'bold'))
            self.reqs_label.pack(anchor=tk.W, pady=(10,2))
            self.reqs_text = tk.Text(self.info_panel, height=4, width=30)
            self.reqs_text.pack(anchor=tk.W, pady=2)
            self.mods_label = ttk.Label(self.info_panel, text="Modifiers:", font=('TkDefaultFont', 10, 'bold'))
            self.mods_label.pack(anchor=tk.W, pady=(10,2))
            self.mods_text = tk.Text(self.info_panel, height=6, width=30)
            self.mods_text.pack(anchor=tk.W, pady=2)
        if self.selected_node and self.selected_node.definition:
            def_node = self.selected_node.definition
            self.node_name_label.config(text=f"Name: {def_node.display_name}")
            self.node_desc_label.config(text=def_node.description)
            self.level_var.set(str(self.selected_node.level))
            self.level_spinbox.config(to=def_node.max_level)
            self.reqs_text.delete('1.0', tk.END)
            if def_node.requirements:
                for req in def_node.requirements:
                    self.reqs_text.insert(tk.END, f"• {req}\n")
            else:
                self.reqs_text.insert(tk.END, "No requirements")
            self.mods_text.delete('1.0', tk.END)
            if def_node.modifiers:
                for mod_type, value in def_node.modifiers.items():
                    self.mods_text.insert(tk.END, f"• {mod_type}: {value}\n")
            else:
                self.mods_text.insert(tk.END, "No modifiers")
        else:
            self.node_name_label.config(text="")
            self.node_desc_label.config(text="")
            self.level_var.set("1")
            self.reqs_text.delete('1.0', tk.END)
            self.mods_text.delete('1.0', tk.END)
    
    def on_level_change(self):
        if self.selected_node:
            try:
                new_level = int(self.level_var.get())
                if new_level != self.selected_node.level:
                    self.selected_node.level = new_level
                    self.draw_doctrine_tree()
            except ValueError:
                pass

    def show_node_settings(self, section_name: str, node_name: str):
        """Show the node settings dialog"""
        dialog = tk.Toplevel(self)
        dialog.title(f"Node Settings - {node_name}")
        dialog.configure(bg=COLORS['background'])
        dialog.transient(self)
        dialog.grab_set()
        
        # Center the dialog
        dialog.geometry("800x800")
        x = self.winfo_rootx() + (self.winfo_width() // 2) - (800 // 2)
        y = self.winfo_rooty() + (self.winfo_height() // 2) - (800 // 2)
        dialog.geometry(f"+{x}+{y}")
        
        # Create notebook for tabs
        notebook = ttk.Notebook(dialog)
        notebook.pack(expand=True, fill='both', padx=10, pady=10)
        
        # Skills tab
        skills_frame = tk.Frame(notebook, bg=COLORS['background'])
        notebook.add(skills_frame, text='Skills')
        
        # Equipment tab
        equipment_frame = tk.Frame(notebook, bg=COLORS['background'])
        notebook.add(equipment_frame, text='Equipment')
        
        # Load current settings from XML
        current_skills = {}
        current_equipment = {}
        try:
            tree = ET.parse(DOCTRINE_NODES_XML)
            root = tree.getroot()
            node_elem = root.find(f".//Node[@name='{node_name}']")
            if node_elem is not None:
                # Load skills
                for enable in node_elem.findall("Enable"):
                    skill_name = enable.get('name')
                    if skill_name in SKILLS:
                        value = enable.get('value', '')
                        current_skills[skill_name] = value
                
                # Load equipment modifiers
                for equip_mod in node_elem.findall("EquipmentModifier"):
                    target = equip_mod.get('target')
                    if target in EQUIPMENT_TYPES:
                        current_equipment[target] = {
                            attr: equip_mod.get(attr)
                            for attr in EQUIPMENT_ATTRIBUTES
                            if equip_mod.get(attr) is not None
                        }
        except Exception as e:
            logger.error(f"Error loading current settings: {str(e)}")
        
        # Skills tab content
        skills_title = tk.Label(
            skills_frame,
            text="Enable/Disable Skills",
            font=("Arial", 14, "bold"),
            bg=COLORS['background'],
            fg=COLORS['text']
        )
        skills_title.pack(pady=(10, 10))
        
        # Create canvas and scrollbar for skills
        skills_canvas = tk.Canvas(skills_frame, bg=COLORS['background'], highlightthickness=0)
        skills_scrollbar = ttk.Scrollbar(skills_frame, orient="vertical", command=skills_canvas.yview)
        skills_scrollable = tk.Frame(skills_canvas, bg=COLORS['background'])
        
        skills_scrollable.bind(
            "<Configure>",
            lambda e: skills_canvas.configure(scrollregion=skills_canvas.bbox("all"))
        )
        
        skills_canvas.create_window((0, 0), window=skills_scrollable, anchor="nw")
        skills_canvas.configure(yscrollcommand=skills_scrollbar.set)
        
        # Add skills with checkboxes and value entries
        skill_vars = {}
        value_vars = {}
        
        for skill_name, description in SKILLS.items():
            frame = tk.Frame(skills_scrollable, bg=COLORS['background'])
            frame.pack(fill='x', padx=5, pady=2)
            
            initial_value = skill_name in current_skills
            var = tk.BooleanVar(value=initial_value)
            skill_vars[skill_name] = var
            
            cb = ttk.Checkbutton(
                frame,
                text=skill_name,
                variable=var,
                style='Switch.TCheckbutton'
            )
            cb.pack(side='left', padx=5)
            
            if skill_name in SKILLS_WITH_VALUES:
                initial_value = current_skills.get(skill_name, "0")
                value_var = tk.StringVar(value=initial_value)
                value_vars[skill_name] = value_var
                value_entry = ttk.Entry(frame, width=5, textvariable=value_var)
                value_entry.pack(side='left', padx=5)
            
            desc_label = tk.Label(
                frame,
                text=description,
                bg=COLORS['background'],
                fg=COLORS['text'],
                wraplength=400,
                justify='left'
            )
            desc_label.pack(side='left', padx=5, fill='x', expand=True)
        
        skills_canvas.pack(side="left", fill="both", expand=True)
        skills_scrollbar.pack(side="right", fill="y")
        
        # Equipment tab content
        equipment_title = tk.Label(
            equipment_frame,
            text="Equipment Modifiers",
            font=("Arial", 14, "bold"),
            bg=COLORS['background'],
            fg=COLORS['text']
        )
        equipment_title.pack(pady=(10, 10))
        
        # Create canvas and scrollbar for equipment
        equip_canvas = tk.Canvas(equipment_frame, bg=COLORS['background'], highlightthickness=0)
        equip_scrollbar = ttk.Scrollbar(equipment_frame, orient="vertical", command=equip_canvas.yview)
        equip_scrollable = tk.Frame(equip_canvas, bg=COLORS['background'])
        
        equip_scrollable.bind(
            "<Configure>",
            lambda e: equip_canvas.configure(scrollregion=equip_canvas.bbox("all"))
        )
        
        equip_canvas.create_window((0, 0), window=equip_scrollable, anchor="nw")
        equip_canvas.configure(yscrollcommand=equip_scrollbar.set)
        
        # Equipment modifiers
        equipment_vars = {}
        for equip_type, equip_info in EQUIPMENT_TYPES.items():
            # Create a frame for each equipment type
            equip_frame = tk.Frame(equip_scrollable, bg=COLORS['background'])
            equip_frame.pack(fill='x', padx=5, pady=10)
            
            # Equipment type header with description
            header_frame = tk.Frame(equip_frame, bg=COLORS['background'])
            header_frame.pack(fill='x', pady=(0, 5))
            
            tk.Label(
                header_frame,
                text=equip_info['name'],
                font=("Arial", 12, "bold"),
                bg=COLORS['background'],
                fg=COLORS['text']
            ).pack(side='left')
            
            tk.Label(
                header_frame,
                text=f" - {equip_info['description']}",
                font=("Arial", 10),
                bg=COLORS['background'],
                fg=COLORS['text']
            ).pack(side='left', padx=5)
            
            # Create a frame for attributes
            attrs_frame = tk.Frame(equip_frame, bg=COLORS['background'])
            attrs_frame.pack(fill='x', padx=20)
            
            equipment_vars[equip_type] = {}
            current_values = current_equipment.get(equip_type, {})
            
            # Only show attributes valid for this equipment type
            valid_attributes = EQUIPMENT_TYPE_ATTRIBUTES.get(equip_type, [])
            
            # Group attributes by category
            categorized_attrs = {}
            for attr in valid_attributes:
                info = EQUIPMENT_ATTRIBUTES[attr]
                category = info['category']
                if category not in categorized_attrs:
                    categorized_attrs[category] = []
                categorized_attrs[category].append((attr, info))
            
            # Create sections for each category
            for category, attrs in categorized_attrs.items():
                category_frame = tk.Frame(attrs_frame, bg=COLORS['background'])
                category_frame.pack(fill='x', pady=5)
                
                tk.Label(
                    category_frame,
                    text=category,
                    font=("Arial", 10, "bold"),
                    bg=COLORS['background'],
                    fg=COLORS['text']
                ).pack(anchor='w', pady=(5,2))
                
                for attr, info in attrs:
                    # Create frame for each attribute
                    attr_frame = tk.Frame(category_frame, bg=COLORS['background'])
                    attr_frame.pack(fill='x', pady=2)
                    
                    # Main attribute info
                    main_info_frame = tk.Frame(attr_frame, bg=COLORS['background'])
                    main_info_frame.pack(side='left')
                    
                    tk.Label(
                        main_info_frame,
                        text=f"{info['name']}:",
                        font=("Arial", 10),
                        bg=COLORS['background'],
                        fg=COLORS['text']
                    ).pack(side='left')
                    
                    var = tk.StringVar(value=current_values.get(attr, ''))
                    equipment_vars[equip_type][attr] = var
                    
                    entry = ttk.Entry(main_info_frame, width=8, textvariable=var)
                    entry.pack(side='left', padx=5)
                    
                    # Format and example
                    tk.Label(
                        main_info_frame,
                        text=f"({info['format']}, e.g., {info['example']})",
                        font=("Arial", 9),
                        bg=COLORS['background'],
                        fg=COLORS['text']
                    ).pack(side='left', padx=5)
                    
                    # Description and effects
                    desc_frame = tk.Frame(attr_frame, bg=COLORS['background'])
                    desc_frame.pack(fill='x', padx=20)
                    
                    tk.Label(
                        desc_frame,
                        text=info['description'],
                        font=("Arial", 9),
                        bg=COLORS['background'],
                        fg=COLORS['text'],
                        wraplength=400,
                        justify='left'
                    ).pack(anchor='w')
                    
                    tk.Label(
                        desc_frame,
                        text=f"Affects: {info['affects']}",
                        font=("Arial", 9, "italic"),
                        bg=COLORS['background'],
                        fg=COLORS['text']
                    ).pack(anchor='w')
        
        equip_canvas.pack(side="left", fill="both", expand=True)
        equip_scrollbar.pack(side="right", fill="y")
        
        # Add buttons at the bottom
        button_frame = tk.Frame(dialog, bg=COLORS['background'])
        button_frame.pack(fill='x', padx=10, pady=10)
        
        ttk.Button(
            button_frame,
            text="Apply",
            command=lambda: self.apply_node_settings(node_name, skill_vars, value_vars, equipment_vars, dialog)
        ).pack(side='right', padx=5)
        
        ttk.Button(
            button_frame,
            text="Cancel",
            command=dialog.destroy
        ).pack(side='right', padx=5)

    def apply_node_settings(self, node_name: str, skill_vars: Dict[str, tk.BooleanVar], 
                          value_vars: Dict[str, tk.StringVar], equipment_vars: Dict[str, Dict[str, tk.StringVar]], 
                          dialog: tk.Toplevel):
        """Apply the node settings and update the XML"""
        try:
            # Parse the current doctrine nodes XML
            tree = ET.parse(DOCTRINE_NODES_XML)
            root = tree.getroot()
            
            # Find or create the node
            node_elem = root.find(f".//Node[@name='{node_name}']")
            if node_elem is None:
                node_elem = ET.SubElement(root, "Node")
                node_elem.set("name", node_name)
                node_elem.set("nameUI", f"@{node_name.lower()}_name")
                node_elem.set("description", f"@{node_name.lower()}_desc")
                node_elem.set("texturePrefix", "data/textures/gui/doctrines/doctrine_empty")
            
            # Remove all existing effect elements
            for effect_type in ['Enable', 'EquipmentModifier', 'AttackTypeModifier']:
                for elem in node_elem.findall(effect_type):
                    node_elem.remove(elem)
            
            # Add new Enable elements based on selected skills
            for skill_name, var in skill_vars.items():
                if var.get():
                    enable = ET.SubElement(node_elem, "Enable")
                    enable.set("name", skill_name)
                    if skill_name in SKILLS_WITH_VALUES:
                        value = value_vars[skill_name].get()
                        if value.strip():  # Only set value if it's not empty
                            enable.set("value", value)
            
            # Add equipment modifiers
            for equip_type, attrs in equipment_vars.items():
                has_modifiers = any(var.get().strip() for var in attrs.values())
                if has_modifiers:
                    equip_mod = ET.SubElement(node_elem, "EquipmentModifier")
                    equip_mod.set("target", equip_type)
                    for attr, var in attrs.items():
                        value = var.get().strip()
                        if value:
                            equip_mod.set(attr, value)
            
            # Save the XML with proper formatting
            xml_str = ET.tostring(root, encoding='unicode')
            dom = xml.dom.minidom.parseString(xml_str)
            pretty_xml = dom.toprettyxml(indent='    ')
            # Clean up empty lines while preserving structure
            lines = [line for line in pretty_xml.split('\n') if line.strip()]
            formatted_xml = '\n'.join(lines)
            
            # Write the formatted XML to file, ensuring only one XML declaration
            with open(DOCTRINE_NODES_XML, 'w', encoding='utf-8') as f:
                # Remove any existing XML declaration from formatted_xml
                if formatted_xml.startswith('<?xml'):
                    formatted_xml = formatted_xml[formatted_xml.find('?>')+2:].strip()
                f.write('<?xml version="1.0" encoding="utf-8"?>\n')
                f.write(formatted_xml)
            
            dialog.destroy()
            messagebox.showinfo("Success", "Node settings saved successfully!")
            
        except FileNotFoundError:
            error_msg = f"Could not find doctrine nodes file: {DOCTRINE_NODES_XML}"
            logger.error(error_msg)
            messagebox.showerror("Error", error_msg)
        except ET.ParseError as e:
            error_msg = f"Error parsing XML file: {str(e)}"
            logger.error(error_msg)
            messagebox.showerror("Error", error_msg)
        except PermissionError:
            error_msg = f"Permission denied when trying to save to: {DOCTRINE_NODES_XML}"
            logger.error(error_msg)
            messagebox.showerror("Error", error_msg)
        except Exception as e:
            error_msg = f"Error saving node settings: {str(e)}"
            logger.error(error_msg)
            messagebox.showerror("Error", error_msg)

# Plugin entry point
PLUGIN_TITLE = "Doctrine Editor"

def get_plugin_tab(notebook):
    editor = DoctrineEditor(notebook)
    editor.pack(fill='both', expand=True)
    return PLUGIN_TITLE, editor 