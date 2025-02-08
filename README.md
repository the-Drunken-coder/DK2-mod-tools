# Door Kickers 2 Modding Tool

⚠️ **WORK IN PROGRESS - USE AT YOUR OWN RISK** ⚠️

This tool is currently in early development. Many features are incomplete, broken, or may not work as expected. Things that might break:
- File saving/loading may fail
- UI elements might not update properly
- XML validation might be incomplete
- Some editors might crash
- Changes might not be saved correctly

**ALWAYS BACKUP YOUR MOD FILES BEFORE USING THIS TOOL!**

## Important Notes

### GUI Editor Limitations
⚠️ **The GUI Editor cannot read most existing GUI layouts.** You will need to recreate your GUI layouts from scratch using the GUI editor. This is a known limitation of the current version.

## Installation

### Prerequisites
1. Door Kickers 2 installed via Steam
2. Write permissions to your Documents folder

### Installation Steps
1. Download the latest installer (`DK2ModdingTool_Setup.exe`) from the [Releases](https://github.com/yourusername/dk2-modding-tool/releases) page
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
- Visual drag-and-drop interface for deploy screen layout
- Support for 2x1, 4x1, and 4x2 unit boxes
- Class-specific slot assignments
- Real-time preview of changes
- **Note:** Cannot import existing GUI layouts - must be recreated from scratch

### Units Editor
- Edit unit templates and properties
- Configure ranks and trooper ranks
- Manage unit attributes and equipment

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

## License

MIT License - See LICENSE file for details 