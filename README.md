# Door Kickers 2 Modding Tool

⚠️ **WORK IN PROGRESS - USE AT YOUR OWN RISK** ⚠️

This tool is currently in early development. Many features are incomplete, broken, or may not work as expected. Things that might break:
- File saving/loading may fail
- UI elements might not update properly
- XML validation might be incomplete
- Some editors might crash
- Changes might not be saved correctly

**ALWAYS BACKUP YOUR MOD FILES BEFORE USING THIS TOOL!**

---

A graphical tool to help create and edit mods for Door Kickers 2. This tool provides a user-friendly interface for editing various aspects of DK2 mods, including unit configurations, equipment bindings, GUI layouts, and more.

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

## Installation

### Option 1: Windows Installer (Recommended)
1. Download the latest installer from the [Releases](https://github.com/yourusername/dk2-modding-tool/releases) page
2. Run the installer
3. Follow the installation wizard
4. Launch the tool from the Start Menu or Desktop shortcut

### Option 2: Manual Installation (For Developers)
1. Clone this repository
2. Install Python 3.8 or higher
3. Install dependencies:
```bash
pip install -r requirements.txt
```
4. Run the tool:
```bash
python modding_tool.py
```

## First Time Setup

1. Launch the tool
2. The tool will attempt to auto-detect your DK2 installation
3. If auto-detection fails, you can manually set:
   - Game Directory: Your DK2 installation folder
   - Mod Directory: Your mods folder (typically in the game directory)
4. Select your mod from the dropdown
5. Start editing!

## Module Details

### Equipment & Bindings Editor
- Create and edit equipment bindings
- Assign equipment to specific classes
- Visual feedback for binding relationships

### GUI Layout Editor
- Design deploy screen layouts
- Drag-and-drop interface for unit boxes
- Configure class assignments per slot
- Support for multiple box types:
  - 2x1 (2 slots)
  - 4x1 (4 slots)
  - 4x2 (8 slots)

### Units Editor
- Edit unit properties
- Configure ranks and progression
- Manage unit attributes
- Set equipment loadouts

### Entities Editor
- Edit human entity templates
- Configure AI behavior
- Set movement and combat properties
- Manage equipment loadouts

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

### Logging System
Each module has its own logging toggle at the top of the file:
```python
ENABLE_LOGGING = False  # Toggle module logging
```
Set to `True` to enable detailed logging for that specific module.

### Building from Source

#### Prerequisites
- Python 3.8 or higher
- Inno Setup 6 or higher (for installer creation)
- Required Python packages:
  ```
  pip install -r requirements-build.txt
  ```

#### Build Steps
1. Set up the build environment:
```bash
python setup_build_env.py
```

2. Build the executable:
```bash
python build_installer.py
```

The installer will be created in the `installer` directory.

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

MIT License - See LICENSE file for details 