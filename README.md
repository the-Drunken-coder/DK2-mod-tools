# Door Kickers 2 Modding Tool

⚠️ **WORK IN PROGRESS - USE AT YOUR OWN RISK** ⚠️

This tool is currently in early development. Many features are incomplete, broken, or may not work as expected. Things that might break:
- File saving/loading may fail
- UI elements might not update properly
- XML validation might be incomplete
- Some editors might crash
- Changes might not be saved correctly

**ALWAYS BACKUP YOUR MOD FILES BEFORE USING THIS TOOL!**

## ⚠️ Important First Startup Note ⚠️
**You will see errors on first startup - THIS IS NORMAL!** 
These errors occur because the file paths are not yet configured. To fix this:
1. Launch the tool
2. Go to the Configuration tab
3. Save your configuration (even if paths are automatically detected)
4. Restart the tool

The errors will disappear after saving your configuration. This is a one-time setup process.

## ⚠️ Important Mod Selection Note ⚠️
**You must select a mod to work on before using any features!**
The tool defaults to your DK2 mods folder location:
```
C:\Program Files (x86)\Steam\steamapps\common\DoorKickers2\mods
```
To select a mod:
1. Go to the Configuration tab
2. Choose your mod from the "Current Mod" dropdown
3. Click "Save Changes"

If your mod isn't listed, verify that:
- Your mod folder exists in the DK2 mods directory
- The mod path is correctly set in the Configuration tab

## Important Notes

### GUI Editor Limitations
⚠️ **The GUI Editor cannot read most existing GUI layouts.** You will need to recreate your GUI layouts from scratch using the GUI editor. This is a known limitation of the current version.

## Installation

### Prerequisites
1. Door Kickers 2 installed via Steam
2. Write permissions to your Documents folder

### Installation Steps
1. Download the latest installer (`DK2ModdingTool_Setup.exe`) from the [Releases](https://github.com/the-Drunken-coder/DK2-mod-tools/releases) page
2. Run the installer
3. Choose your installation directory (defaults to Documents folder)
4. Follow the installation wizard
5. Launch the tool from the Start Menu or Desktop shortcut

### First Time Setup
The tool will automatically:
1. Detect your DK2 installation in the default Steam location
2. Set up the necessary directories
3. Create required configuration files

If the automatic detection fails:
1. Go to the Configuration tab
2. Click "Browse" next to Game Directory and select your DK2 installation folder
3. Click "Browse" next to Mod Directory and select your mods folder (typically in the game directory)
4. Click "Save Changes"

## Features

### Equipment & Bindings Editor
- Configure equipment loadouts for different unit classes
- Manage equipment bindings and relationships
- Visual editor for equipment assignments

### GUI Layout Editor
- Visual editor for creating and modifying unit deployment layouts
- Support for different box sizes (2x1, 4x1, 4x2)
- Drag and drop interface for positioning boxes
- Slot assignment system for equipment classes
- Automatic synchronization with unit XML files

### Units Editor
- Create and edit unit classes
- Manage trooper ranks and regular ranks
- Edit unit attributes and properties
- Preserves equipment slot counts between edits

### Entities Editor
- Edit human entity templates
- Configure AI behavior and properties
- Manage entity attributes

### Mod Management
- Centralized file management
- Automatic file structure creation
- Support for multiple mods

### Additional Features
- XML validation
- Mod packaging
- Configurable logging per module
- Auto-detection of game installation

## Usage

### Creating a New Mod
1. Go to the Configuration tab
2. Click "Create New Mod"
3. Enter your mod details
4. Click "Create"

### Editing an Existing Mod
1. Go to the Configuration tab
2. Select your mod from the dropdown
3. Use the various editor tabs to modify your mod

### GUI Editor Usage
1. Select your mod in the Configuration tab
2. Go to the GUI Editor tab
3. Create a new layout from scratch using the available tools
4. **Remember:** You cannot import existing GUI layouts

## Troubleshooting

### Common Issues
1. **Files not saving:**
   - Ensure you have write permissions to the mod directory
   - Try running as administrator

2. **Game not detected:**
   - Manually set the paths in the Configuration tab
   - Verify your DK2 installation

3. **GUI Editor issues:**
   - Remember that existing GUI layouts must be recreated from scratch
   - Save frequently to avoid losing work

## Development

### Project Structure
```
dk2-modding-tool/
├── modding_tool.py       # Main application
├── utils.py             # Utility functions
├── modules/            # Plugin modules
│   ├── config_editor_module.py
│   ├── entities_editor_module.py
│   ├── equipment_binding_editor_module.py
│   ├── gui_editor_module.py
│   ├── mod_files.py
│   └── units_editor_module.py
└── Example mod/        # Example mod templates
```

### Contributing
1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## Support

If you encounter any issues or have suggestions:
1. Check the [Known Issues](https://github.com/the-Drunken-coder/DK2-mod-tools/issues) section
2. [Submit a Bug Report](https://github.com/the-Drunken-coder/DK2-mod-tools/issues/new?template=bug_report.md)
3. [Request a Feature](https://github.com/the-Drunken-coder/DK2-mod-tools/issues/new?template=feature_request.md)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

### Mod Structure
Any folder in your DK2 mods directory will be treated as a mod. The following structure shows the standard mod layout and file naming conventions:

#### Standard Directory Structure
- `gui/` - GUI layouts
  - `*_deploy.xml` - Deploy screen layouts
  - `*_gui.xml` - General GUI layouts
  - Other GUI XML files
- `units/` - Unit definitions
  - `*_unit.xml` - Unit definitions
  - `*_identities.xml` - Unit identities
- `entities/` - Entity definitions
  - `*_humans.xml` - Human entity definitions
  - `*_entities.xml` - Other entity definitions
- `equipment/` - Equipment definitions
  - `*_binds.xml` - Equipment bindings
  - `*_equipment.xml` - Equipment definitions
- `textures/` - Texture files
  - `*_squad_bg.dds` - Squad backgrounds
  - Other texture files (`.dds`, `.jpg`, `.png`)
- `localization/` - Localization files
  - `*_squadname_pool.txt` - Squad name pools
  - `*_strings.xml` - String tables

#### Common Files
- `mod.xml` - Mod metadata (title, description, author)
- `mod_image.jpg` - Mod preview image

All directories and files are optional - create only what you need for your mod.

### GUI Editor Limitations
⚠️ **The GUI Editor cannot read most existing GUI layouts.** You will need to recreate your GUI layouts from scratch using the GUI editor. This is a known limitation of the current version.

### Equipment Management
The tool manages equipment slots through two integrated systems:

1. **GUI Layout Editor**:
   - Visually assign equipment slots to classes
   - Drag and drop boxes to create the layout
   - Each box can have multiple slots (2x1=2 slots, 4x1=4 slots, 4x2=8 slots)
   - Slots can be assigned to different classes using the dropdown menu

2. **Units Editor**:
   - Displays and manages class definitions
   - The `numSlots` value for each class is automatically managed by the GUI editor
   - Manual edits to `numSlots` in the units editor will be preserved until slots are reassigned in the GUI

### Equipment Slot Rules
- Each class's `numSlots` value determines how many equipment slots are available
- The GUI editor automatically updates these values based on slot assignments
- If you need to change how many slots a class has:
  1. Use the GUI editor to assign/unassign slots to the class
  2. The `numSlots` value will update automatically
  3. Changes are saved to the unit XML file 