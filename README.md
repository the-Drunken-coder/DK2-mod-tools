# Door Kickers 2 Mod Tools 🎮

A comprehensive GUI toolkit for creating and editing mods for Door Kickers 2. This tool simplifies the modding process by providing visual editors for various aspects of the game.

## 🌟 Features

### GUI Editor
- Visual layout editor for deployment screens
- Drag-and-drop interface for unit slots
- Class container management
- Real-time preview of changes
- Automatic XML generation

### Units Editor
- Create and modify unit configurations
- Edit unit classes and properties
- Manage unit equipment and loadouts
- Visual feedback for changes

### Equipment Binding Editor
- Configure equipment bindings
- Manage weapon and gear assignments
- Easy-to-use interface for complex configurations

### Entities Editor
- Create and modify game entities
- Visual property editor
- XML validation and error checking

### Localization Editor
- Manage game text and translations
- Multi-language support
- Easy text entry and editing

### Mod Metadata Editor
- Configure mod information
- Set mod dependencies
- Manage version information

## 🚀 Getting Started

### Prerequisites
- Python 3.8 or higher
- Tkinter (usually comes with Python)
- A copy of Door Kickers 2

### Installation
1. Clone this repository:
```bash
git clone https://github.com/the-Drunken-coder/DK2-mod-tools.git
```

2. Navigate to the project directory:
```bash
cd DK2-mod-tools
```

3. Run the tool:
```bash
python modding_tool.py
```

## 📖 Usage Guide

### Creating a New Mod
1. Launch the tool
2. Select the type of editor you want to use
3. Create or modify your mod components
4. Save your changes

### GUI Editor
- **Adding Boxes**: Use the buttons at the top to add 2x1, 4x1, or 4x2 boxes
- **Moving Boxes**: Drag and drop boxes to position them
- **Editing Properties**: Use the right panel to edit box properties
- **Class Assignment**: Assign slots to different classes using dropdowns
- **Saving**: Changes are auto-saved when modifying slots

### Units Editor
- Select unit types to modify
- Edit properties in the right panel
- Changes are validated in real-time
- Save changes to update unit files

### Equipment Editor
- Modify weapon and gear bindings
- Configure equipment slots
- Set up default loadouts
- Preview changes before saving

## 🔧 File Structure
```
DK2-mod-tools/
├── modding_tool.py          # Main application entry point
├── modules/                 # Editor modules
│   ├── gui_editor_module.py           # GUI layout editor
│   ├── units_editor_module.py         # Unit configuration editor
│   ├── equipment_binding_editor.py    # Equipment binding editor
│   ├── entities_editor_module.py      # Entity editor
│   ├── localization_editor_module.py  # Text/translation editor
│   └── mod_metadata_editor_module.py  # Mod info editor
└── utils.py                # Utility functions
```

## 🎯 XML Structure
The tool generates and modifies several XML files used by Door Kickers 2:

### GUI Layout (seals_deploy.xml)
```xml
<GUIItems>
    <Item name="MOD_NAME">
        <!-- Class containers and slots -->
        <StaticImage name="ClassName">
            <!-- Slot configurations -->
        </StaticImage>
    </Item>
</GUIItems>
```

### Units (units.xml)
```xml
<Units>
    <Unit name="UnitName">
        <!-- Unit properties -->
        <Class name="ClassName">
            <!-- Class-specific properties -->
        </Class>
    </Unit>
</Units>
```

## 🤝 Contributing
Contributions are welcome! Here's how you can help:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License
This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments
- Door Kickers 2 development team for creating an amazing game
- The modding community for their support and feedback
- All contributors to this project

## 🐛 Known Issues
- Some complex XML structures might need manual adjustment
- Visual preview might slightly differ from in-game appearance

## 📞 Support
If you encounter any issues or have questions:
1. Check the [Issues](https://github.com/the-Drunken-coder/DK2-mod-tools/issues) page
2. Create a new issue with detailed information about your problem
3. Join our community discussions

## 🔄 Version History
- v1.0.0 - Initial release
  - Basic GUI editor functionality
  - Unit editor implementation
  - Equipment binding support
  - Entity editor features 