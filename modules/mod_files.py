import os
import xml.etree.ElementTree as ET

ENABLE_LOGGING = True  # Toggle module logging

def log(message):
    """Module specific logging function"""
    if ENABLE_LOGGING:
        print(f"[ModFiles] {message}")

class ModFiles:
    """Centralized file management for the current mod"""
    def __init__(self, mod_path=None):
        self.mod_path = mod_path
        self.files = {
            "unit": None,
            "equipment": None,
            "entities": None,
            "gui": None,
            "mod": None
        }
        if mod_path:
            self.scan_mod_directory()

    def scan_mod_directory(self):
        """Scan the mod directory to find all relevant files"""
        if not self.mod_path:
            return

        # Create mod directory if it doesn't exist
        self.ensure_directory(self.mod_path)
        log(f"Scanning mod directory: {os.path.basename(self.mod_path)}")
        
        # Find unit file
        unit_files = []
        unit_dir = self.ensure_directory(os.path.join(self.mod_path, "units"))
        if os.path.exists(unit_dir):
            for file in os.listdir(unit_dir):
                if file.endswith("_unit.xml"):
                    full_path = os.path.join(unit_dir, file)
                    unit_files.append((full_path, os.path.getsize(full_path)))
        if unit_files:
            # Use the largest unit file
            unit_files.sort(key=lambda x: x[1], reverse=True)
            self.files["unit"] = unit_files[0][0]
            log(f"Found unit file: {os.path.basename(self.files['unit'])}")
        else:
            default_unit = os.path.join(unit_dir, "unit.xml")
            self.files["unit"] = default_unit
            log("Using default unit file: unit.xml")

        # Find equipment binds file
        equipment_files = []
        equipment_dir = self.ensure_directory(os.path.join(self.mod_path, "equipment"))
        if os.path.exists(equipment_dir):
            for file in os.listdir(equipment_dir):
                if file.endswith("_binds.xml"):
                    full_path = os.path.join(equipment_dir, file)
                    equipment_files.append((full_path, os.path.getsize(full_path)))
        if equipment_files:
            # Use the largest binds file
            equipment_files.sort(key=lambda x: x[1], reverse=True)
            self.files["equipment"] = equipment_files[0][0]
            log(f"Found equipment file: {os.path.basename(self.files['equipment'])}")
        else:
            default_binds = os.path.join(equipment_dir, "binds.xml")
            self.files["equipment"] = default_binds
            log("Using default equipment file: binds.xml")
            # Create basic equipment file if it doesn't exist
            if not os.path.exists(default_binds):
                log("Creating default equipment binds file")
                root = ET.Element("Equipment")
                tree = ET.ElementTree(root)
                tree.write(default_binds, encoding='utf-8', xml_declaration=True)

        # Find entities file
        entities_files = []
        entities_dir = self.ensure_directory(os.path.join(self.mod_path, "entities"))
        if os.path.exists(entities_dir):
            for file in os.listdir(entities_dir):
                if file.endswith("_humans.xml"):
                    full_path = os.path.join(entities_dir, file)
                    entities_files.append((full_path, os.path.getsize(full_path)))
        if entities_files:
            # Use the largest humans file
            entities_files.sort(key=lambda x: x[1], reverse=True)
            self.files["entities"] = entities_files[0][0]
            log(f"Found entities file: {os.path.basename(self.files['entities'])}")
        else:
            default_humans = os.path.join(entities_dir, "humans.xml")
            self.files["entities"] = default_humans
            log("Using default entities file: humans.xml")

        # Find GUI file
        gui_files = []
        gui_dir = self.ensure_directory(os.path.join(self.mod_path, "gui"))
        if os.path.exists(gui_dir):
            for file in os.listdir(gui_dir):
                if file.endswith("_deploy.xml"):
                    full_path = os.path.join(gui_dir, file)
                    gui_files.append((full_path, os.path.getsize(full_path)))
        if gui_files:
            # Use the largest deploy file
            gui_files.sort(key=lambda x: x[1], reverse=True)
            self.files["gui"] = gui_files[0][0]
            log(f"Found GUI file: {os.path.basename(self.files['gui'])}")
        else:
            default_deploy = os.path.join(gui_dir, "deploy.xml")
            self.files["gui"] = default_deploy
            log("Using default GUI file: deploy.xml")

        # Find mod.xml
        mod_xml = os.path.join(self.mod_path, "mod.xml")
        if os.path.exists(mod_xml):
            self.files["mod"] = mod_xml
            log("Found mod.xml")

    def ensure_directory(self, dir_path):
        """Create directory if it doesn't exist"""
        if not os.path.exists(dir_path):
            log(f"Creating directory: {dir_path}")
            os.makedirs(dir_path, exist_ok=True)
        return dir_path

    def get_file(self, file_type):
        """Get the path to a specific file type"""
        file_path = self.files.get(file_type)
        if file_path:
            # Ensure the directory exists
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            # If it's the equipment file and it doesn't exist, create a basic one
            if file_type == "equipment" and not os.path.exists(file_path):
                log(f"Creating new equipment file: {file_path}")
                root = ET.Element("Equipment")
                tree = ET.ElementTree(root)
                tree.write(file_path, encoding='utf-8', xml_declaration=True)
        return file_path

    def get_mod_name(self):
        """Get the faction name from the Unit element's name attribute"""
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

# Global instance for file management
mod_files = ModFiles() 