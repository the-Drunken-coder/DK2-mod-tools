import os
import xml.etree.ElementTree as ET
from pathlib import Path
import json
from operator import attrgetter

# Define all known equipment types
EQUIPMENT_TYPES = [
    "Firearm", "Armor", "Grenade", "Utility",
    "Support", "Shield", "HelmetNVG", "Explosive", 
    "Breaching", "Camera", "Tool", "Custom", "Poncho",
    "EmptySupportGear", "TorchKit", "Torch",
    "DemolitionCharge", "Binoculars", "Radio",
    "Scope", "Magazine"
]

# Define type remapping for consolidation
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
    
    def to_dict(self):
        return {
            "name": self.name,
            "type": self.type,
            "category": self.category,
            "inventory_slot": self.inventory_slot,
            "source_file": self.source_file,
            "source_mod": self.source_mod,
            "bindings": sorted(self.bindings) if self.bindings else [],
            "attributes": dict(sorted(self.attributes.items())) if self.attributes else {}
        }
    
    def __str__(self):
        return f"{self.name} ({self.type}) - {self.source_mod}"

def sort_equipment_items(items, sort_by="name", reverse=False):
    """Sort equipment items by specified criteria"""
    if sort_by == "name":
        return sorted(items, key=lambda x: x.name.lower(), reverse=reverse)
    elif sort_by == "type":
        return sorted(items, key=lambda x: (x.type.lower(), x.name.lower()), reverse=reverse)
    elif sort_by == "mod":
        return sorted(items, key=lambda x: (x.source_mod.lower(), x.name.lower()), reverse=reverse)
    elif sort_by == "slot":
        return sorted(items, key=lambda x: (x.inventory_slot.lower() if x.inventory_slot else "zzzz", x.name.lower()), reverse=reverse)
    elif sort_by == "category":
        return sorted(items, key=lambda x: (x.category.lower() if x.category else "zzzz", x.name.lower()), reverse=reverse)
    else:
        return items

def scan_equipment_files(base_path):
    """Scan a directory for equipment files and parse them"""
    equipment_items = []
    bindings = {}  # Store bindings to process later
    unknown_types = set()  # Track any equipment types we haven't seen before
    
    print("\nScanning for equipment files...")
    
    # Walk through all directories
    for root, dirs, files in os.walk(base_path):
        for file in files:
            if file.endswith('.xml'):
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, base_path)
                mod_name = rel_path.split(os.sep)[0] if os.sep in rel_path else "vanilla"
                
                try:
                    tree = ET.parse(file_path)
                    root_elem = tree.getroot()
                    
                    # Process equipment definitions
                    if root_elem.tag == "Equipment":
                        print(f"\nProcessing file: {rel_path}")
                        
                        # Process bindings
                        bindings_found = 0
                        for bind in root_elem.findall(".//Bind"):
                            process_binding(bind, bindings)
                            bindings_found += 1
                        print(f"  Found {bindings_found} bindings")
                        
                        # Process equipment items
                        items_found = 0
                        for elem in root_elem:
                            # Skip Ammo type
                            if elem.tag == "Ammo":
                                continue
                                
                            # Track unknown types (excluding remapped types)
                            if elem.tag not in EQUIPMENT_TYPES and elem.tag not in TYPE_REMAPPING and elem.tag != "Bind":
                                unknown_types.add(elem.tag)
                            
                            # Process known equipment types and remapped types
                            if elem.tag in EQUIPMENT_TYPES or elem.tag in TYPE_REMAPPING:
                                item = create_equipment_item(elem, file_path, mod_name)
                                if item:
                                    equipment_items.append(item)
                                    items_found += 1
                        
                        if items_found > 0:
                            print(f"  Found {items_found} equipment items")
                except ET.ParseError:
                    print(f"Failed to parse XML file: {file_path}")
                except Exception as e:
                    print(f"Error processing file {file_path}: {str(e)}")
    
    # Report any unknown types found
    if unknown_types:
        print("\nFound unknown equipment types:")
        for type_name in sorted(unknown_types):
            print(f"  - {type_name}")
    
    # Apply bindings to equipment items
    apply_bindings(equipment_items, bindings)
    
    return equipment_items

def process_binding(bind_elem, bindings):
    """Process a binding element and add it to the bindings dictionary"""
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

def create_equipment_item(elem, file_path, mod_name):
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

def apply_bindings(equipment_items, bindings):
    """Apply the collected bindings to equipment items"""
    for item in equipment_items:
        if item.name in bindings:
            item.bindings = list(bindings[item.name])

def print_sorted_equipment(items, sort_by="name"):
    """Print equipment items sorted by specified criteria"""
    sorted_items = sort_equipment_items(items, sort_by)
    
    print(f"\nEquipment sorted by {sort_by}:")
    print("-" * 80)
    
    current_group = None
    for item in sorted_items:
        # Get the grouping value based on sort criteria
        if sort_by == "slot":
            group_value = item.inventory_slot or "No Slot"
        elif sort_by == "mod":
            group_value = item.source_mod
        else:
            group_value = getattr(item, sort_by)
        
        # Print group header if it changed
        if group_value != current_group:
            current_group = group_value
            print(f"\n[{current_group}]")
        
        # Print item details
        bindings_str = f" (Used by: {', '.join(item.bindings)})" if item.bindings else ""
        print(f"  {item.name:<30} - {item.type:<10} - {item.source_mod}{bindings_str}")

def main():
    # Get the path to scan from user input
    print("Enter the path to scan for equipment files:")
    base_path = input().strip()
    
    if not os.path.exists(base_path):
        print(f"Error: Path does not exist: {base_path}")
        return
    
    print(f"\nScanning directory: {base_path}")
    equipment_items = scan_equipment_files(base_path)
    
    # Create structured output with collapsible sections
    output = {
        "summary": {
            "total_items": len(equipment_items),
            "types": {},
            "mods": {},
            "slots": {},
            "categories": {}
        },
        "by_type": {},
        "by_mod": {},
        "by_slot": {},
        "by_category": {},
        "all_items": [item.to_dict() for item in equipment_items]  # Keep the flat list for reference
    }
    
    # Build summary counts and grouped sections
    for item in equipment_items:
        item_dict = item.to_dict()
        
        # Update summary counts
        output["summary"]["types"][item.type] = output["summary"]["types"].get(item.type, 0) + 1
        output["summary"]["mods"][item.source_mod] = output["summary"]["mods"].get(item.source_mod, 0) + 1
        output["summary"]["slots"][item.inventory_slot or "None"] = output["summary"]["slots"].get(item.inventory_slot or "None", 0) + 1
        output["summary"]["categories"][item.category or "None"] = output["summary"]["categories"].get(item.category or "None", 0) + 1
        
        # Group by type
        if item.type not in output["by_type"]:
            output["by_type"][item.type] = []
        output["by_type"][item.type].append(item_dict)
        
        # Group by mod
        if item.source_mod not in output["by_mod"]:
            output["by_mod"][item.source_mod] = []
        output["by_mod"][item.source_mod].append(item_dict)
        
        # Group by slot
        slot_key = item.inventory_slot or "None"
        if slot_key not in output["by_slot"]:
            output["by_slot"][slot_key] = []
        output["by_slot"][slot_key].append(item_dict)
        
        # Group by category
        category_key = item.category or "None"
        if category_key not in output["by_category"]:
            output["by_category"][category_key] = []
        output["by_category"][category_key].append(item_dict)
    
    # Sort all lists within groups
    for type_items in output["by_type"].values():
        type_items.sort(key=lambda x: x["name"].lower())
    for mod_items in output["by_mod"].values():
        mod_items.sort(key=lambda x: x["name"].lower())
    for slot_items in output["by_slot"].values():
        slot_items.sort(key=lambda x: x["name"].lower())
    for category_items in output["by_category"].values():
        category_items.sort(key=lambda x: x["name"].lower())
    
    # Sort the summary dictionaries
    output["summary"]["types"] = dict(sorted(output["summary"]["types"].items()))
    output["summary"]["mods"] = dict(sorted(output["summary"]["mods"].items()))
    output["summary"]["slots"] = dict(sorted(output["summary"]["slots"].items()))
    output["summary"]["categories"] = dict(sorted(output["summary"]["categories"].items()))
    
    # Save results to a JSON file
    output_file = "equipment_scan_results.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print(f"\nFound {len(equipment_items)} equipment items")
    print(f"Results saved to: {output_file}")
    
    # Print statistics
    print("\nEquipment types found:")
    for type_name, count in output["summary"]["types"].items():
        print(f"  {type_name}: {count} items")
    
    print("\nMods found:")
    for mod_name, count in output["summary"]["mods"].items():
        print(f"  {mod_name}: {count} items")
    
    print("\nInventory slots found:")
    for slot_name, count in output["summary"]["slots"].items():
        print(f"  {slot_name}: {count} items")
    
    print("\nCategories found:")
    for category_name, count in output["summary"]["categories"].items():
        print(f"  {category_name}: {count} items")
    
    # Print sorted views
    for sort_criteria in ["type", "mod", "slot", "category"]:
        print_sorted_equipment(equipment_items, sort_criteria)

if __name__ == "__main__":
    main() 