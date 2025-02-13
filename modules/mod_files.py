import os
import xml.etree.ElementTree as ET
import json

def is_logging_enabled():
    """Check if logging is enabled for this module"""
    try:
        config_path = os.path.join(os.path.dirname(__file__), 'logging_config.json')
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                config = json.load(f)
                return config.get("mod_files", False)
    except Exception:
        pass
    return False

def log(message):
    """Module specific logging function"""
    if is_logging_enabled():
        print(f"[ModFiles] {message}")

class ModFiles:
    """Centralized file management for the current mod"""
    def __init__(self, mod_path=None):
        log(f"Initializing ModFiles with path: {mod_path}")
        self.mod_path = os.path.normpath(mod_path) if mod_path else None
        self.files = {
            "unit": None,
            "equipment": None,
            "entities": None,
            "gui": None,
            "mod": None,
            "doctrine_nodes": None,  # New: doctrine nodes file
            "doctrine": None         # New: doctrine file
        }
        if mod_path and os.path.exists(os.path.join(mod_path, "mod.xml")):
            self.scan_mod_directory()
        else:
            log("No valid mod path provided during initialization")

    def scan_mod_directory(self):
        """Scan the mod directory to find all relevant files"""
        if not self.mod_path:
            return

        # Check for mod.xml first - this is required
        mod_xml = os.path.normpath(os.path.join(self.mod_path, "mod.xml"))
        if not os.path.exists(mod_xml):
            log("Error: mod.xml not found. Please select a valid mod directory.")
            return
            
        self.files["mod"] = mod_xml
        log("Found mod.xml")
        
        # Find unit file
        unit_files = []
        unit_dir = os.path.join(self.mod_path, "units")
        if os.path.exists(unit_dir):
            for file in os.listdir(unit_dir):
                # Accept files that:
                # 1. End with _unit.xml or _units.xml
                # 2. Are exactly unit.xml or units.xml
                # 3. End with _unit or _units (fallback)
                if (file.endswith("_unit.xml") or file.endswith("_units.xml") or 
                    file in ["unit.xml", "units.xml"] or 
                    file.endswith("_unit") or file.endswith("_units")):
                    full_path = os.path.normpath(os.path.join(unit_dir, file))
                    try:
                        # Try to parse the file to verify it's valid XML
                        ET.parse(full_path)
                        unit_files.append((full_path, os.path.getsize(full_path)))
                        log(f"Found valid unit file: {file}")
                    except ET.ParseError as e:
                        log(f"Warning: Failed to parse {file}: {str(e)}")
                        continue
        if unit_files:
            # Use the largest unit file
            unit_files.sort(key=lambda x: x[1], reverse=True)
            self.files["unit"] = unit_files[0][0]
            log(f"Found unit file: {os.path.basename(self.files['unit'])}")
        else:
            self.files["unit"] = None
            log("No unit file found")

        # Find doctrine nodes file
        doctrine_nodes_files = []
        if os.path.exists(unit_dir):
            for file in os.listdir(unit_dir):
                if file.endswith("_doctrine_nodes.xml") or file.endswith("_doctrine_nodes"):
                    full_path = os.path.normpath(os.path.join(unit_dir, file))
                    try:
                        ET.parse(full_path)
                        doctrine_nodes_files.append((full_path, os.path.getsize(full_path)))
                        log(f"Found valid doctrine nodes file: {file}")
                    except ET.ParseError as e:
                        log(f"Warning: Failed to parse {file}: {str(e)}")
                        continue
        if doctrine_nodes_files:
            doctrine_nodes_files.sort(key=lambda x: x[1], reverse=True)
            self.files["doctrine_nodes"] = doctrine_nodes_files[0][0]
            log(f"Found doctrine nodes file: {os.path.basename(self.files['doctrine_nodes'])}")
        else:
            self.files["doctrine_nodes"] = None
            log("No doctrine nodes file found")

        # Find doctrine file
        doctrine_files = []
        localization_dir = os.path.join(self.mod_path, "localization")
        if os.path.exists(localization_dir):
            for file in os.listdir(localization_dir):
                if file.endswith("_doctrine.txt") or file.endswith("_doctrines.txt"):
                    full_path = os.path.normpath(os.path.join(localization_dir, file))
                    doctrine_files.append((full_path, os.path.getsize(full_path)))
                    log(f"Found valid doctrine file: {file}")
        if doctrine_files:
            doctrine_files.sort(key=lambda x: x[1], reverse=True)
            self.files["doctrine"] = doctrine_files[0][0]
            log(f"Found doctrine file: {os.path.basename(self.files['doctrine'])}")
        else:
            self.files["doctrine"] = None
            log("No doctrine file found")

        # Find equipment binds file
        equipment_files = []
        equipment_dir = os.path.join(self.mod_path, "equipment")
        if os.path.exists(equipment_dir):
            for file in os.listdir(equipment_dir):
                # Check for files that:
                # 1. End with _binds.xml
                # 2. Are exactly binds.xml
                # 3. End with _binds (fallback)
                if file.endswith("_binds.xml") or file == "binds.xml" or file.endswith("_binds"):
                    full_path = os.path.normpath(os.path.join(equipment_dir, file))
                    try:
                        # Try to parse the file to verify it's valid XML
                        ET.parse(full_path)
                        equipment_files.append((full_path, os.path.getsize(full_path)))
                        log(f"Found valid equipment file: {file}")
                    except ET.ParseError as e:
                        log(f"Warning: Failed to parse {file}: {str(e)}")
                        continue
        if equipment_files:
            # Use the largest binds file
            equipment_files.sort(key=lambda x: x[1], reverse=True)
            self.files["equipment"] = equipment_files[0][0]
            log(f"Using equipment file: {os.path.basename(self.files['equipment'])}")
        else:
            self.files["equipment"] = None
            log("No equipment file found")

        # Find entities file
        entities_files = []
        entities_dir = os.path.join(self.mod_path, "entities")
        if os.path.exists(entities_dir):
            for file in os.listdir(entities_dir):
                # Check for files that:
                # 1. End with .xml and contain 'human'
                # 2. End with _human.xml or _humans.xml
                # 3. End with _human or _humans (fallback)
                if ((file.lower().endswith('.xml') and 'human' in file.lower()) or
                    file.endswith("_human.xml") or file.endswith("_humans.xml") or
                    file.endswith("_human") or file.endswith("_humans")):
                    full_path = os.path.normpath(os.path.join(entities_dir, file))
                    try:
                        # Try to parse the file to verify it's valid XML
                        ET.parse(full_path)
                        entities_files.append((full_path, os.path.getsize(full_path)))
                        log(f"Found valid entities file: {file}")
                    except ET.ParseError as e:
                        log(f"Warning: Failed to parse {file}: {str(e)}")
                        continue
        if entities_files:
            # Use the largest humans file
            entities_files.sort(key=lambda x: x[1], reverse=True)
            self.files["entities"] = entities_files[0][0]
            log(f"Found entities file: {os.path.basename(self.files['entities'])}")
        else:
            self.files["entities"] = None
            log("No human entities file found")

        # Find GUI file
        gui_files = []
        gui_dir = os.path.join(self.mod_path, "gui")
        if os.path.exists(gui_dir):
            for file in os.listdir(gui_dir):
                # Check for files that:
                # 1. End with _deploy.xml
                # 2. Are exactly deploy.xml
                # 3. End with _deploy (fallback)
                if file.endswith("_deploy.xml") or file == "deploy.xml" or file.endswith("_deploy"):
                    full_path = os.path.normpath(os.path.join(gui_dir, file))
                    try:
                        # Try to parse the file to verify it's valid XML
                        ET.parse(full_path)
                        gui_files.append((full_path, os.path.getsize(full_path)))
                        log(f"Found valid GUI file: {file}")
                    except ET.ParseError as e:
                        log(f"Warning: Failed to parse {file}: {str(e)}")
                        continue
        if gui_files:
            # Use the largest deploy file
            gui_files.sort(key=lambda x: x[1], reverse=True)
            self.files["gui"] = gui_files[0][0]
            log(f"Found GUI file: {os.path.basename(self.files['gui'])}")
        else:
            self.files["gui"] = None
            log("No GUI file found")

    def get_file(self, file_type):
        """Get the path to a specific file type"""
        # Check for mod.xml first
        mod_xml = os.path.normpath(os.path.join(self.mod_path, "mod.xml"))
        if not os.path.exists(mod_xml):
            log("Error: mod.xml not found. Please select a valid mod directory.")
            return None
            
        file_path = self.files.get(file_type)
        if file_path and os.path.exists(file_path):
            return file_path
        return None

    def get_mod_name(self):
        """Get the faction name from the Unit element's name attribute"""
        # Check for mod.xml first
        mod_xml = os.path.normpath(os.path.join(self.mod_path, "mod.xml"))
        if not os.path.exists(mod_xml):
            log("Error: mod.xml not found. Please select a valid mod directory.")
            return "FACTION"
            
        if not self.files["unit"] or not os.path.exists(self.files["unit"]):
            log("No unit file found, using default faction name: FACTION")
            return "FACTION"
        try:
            tree = ET.parse(self.files["unit"])
            root = tree.getroot()
            # Find the Unit element and get its name attribute
            unit_elem = root.find(".//Unit")
            if unit_elem is not None:
                faction_name = unit_elem.get("name", "FACTION")
                log(f"Found faction name in unit file: {faction_name}")
                return faction_name
            log("No Unit element found in unit file")
            return "FACTION"
        except Exception as e:
            log(f"Error reading faction name: {e}")
            return "FACTION"

    def get_available_classes(self):
        """Get available classes from the unit file"""
        # Check for mod.xml first
        mod_xml = os.path.normpath(os.path.join(self.mod_path, "mod.xml"))
        if not os.path.exists(mod_xml):
            log("Error: mod.xml not found. Please select a valid mod directory.")
            return []
            
        if not self.files["unit"] or not os.path.exists(self.files["unit"]):
            log("No unit file found")
            return []
        try:
            tree = ET.parse(self.files["unit"])
            root = tree.getroot()
            classes_elem = root.find(".//Classes")
            if classes_elem is not None:
                classes = []
                for cls in classes_elem.findall("Class"):
                    name = cls.get("name")
                    if name:
                        classes.append(str(name))
                        log(f"Found class: {name}")
                return sorted(classes)
            return []
        except Exception as e:
            log(f"Error loading classes: {e}")
            return []

    def get_unit_file(self):
        """Get the unit file path"""
        return self.get_file("unit")

    def get_equipment_file(self):
        """Get the equipment file path"""
        return self.get_file("equipment")

    def get_entities_file(self):
        """Get the entities file path"""
        return self.get_file("entities")

    def get_gui_file(self):
        """Get the GUI file path"""
        return self.get_file("gui")

    def get_doctrine_nodes_file(self):
        """Get the doctrine nodes file path"""
        return self.get_file("doctrine_nodes")

    def get_doctrine_file(self):
        """Get the doctrine file path"""
        return self.get_file("doctrine")

    def create_doctrine_nodes_file(self):
        """Create a new doctrine nodes file with basic structure"""
        if not self.mod_path:
            return False, "No mod path configured"

        unit_dir = os.path.join(self.mod_path, "units")
        if not os.path.exists(unit_dir):
            os.makedirs(unit_dir)

        file_path = os.path.join(unit_dir, "doctrine_nodes.xml")
        if os.path.exists(file_path):
            return False, "File already exists"

        try:
            root = ET.Element("DoctrineNodes")
            tree = ET.ElementTree(root)
            tree.write(file_path, encoding="utf-8", xml_declaration=True)
            self.files["doctrine_nodes"] = file_path
            return True, "Created doctrine nodes file successfully"
        except Exception as e:
            return False, f"Failed to create file: {str(e)}"

    def create_doctrine_file(self):
        """Create a new doctrine file with basic structure"""
        if not self.mod_path:
            return False, "No mod path configured"

        loc_dir = os.path.join(self.mod_path, "localization")
        if not os.path.exists(loc_dir):
            os.makedirs(loc_dir)

        file_path = os.path.join(loc_dir, "doctrine.xml")
        if os.path.exists(file_path):
            return False, "File already exists"

        try:
            root = ET.Element("Strings")
            tree = ET.ElementTree(root)
            tree.write(file_path, encoding="utf-8", xml_declaration=True)
            self.files["doctrine"] = file_path
            return True, "Created doctrine file successfully"
        except Exception as e:
            return False, f"Failed to create file: {str(e)}"

# Global instance for file management
mod_files = ModFiles() 