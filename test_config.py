from modules.config_editor_module import is_valid_mod_directory, get_mod_info
import os
import sys
from colorama import init, Fore, Style

# Initialize colorama for colored output
init()

def print_color(text, color=Fore.WHITE, style=Style.NORMAL):
    print(f"{style}{color}{text}{Style.RESET_ALL}")

def format_size(size):
    """Format file size in a human-readable format"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024.0:
            return f"{size:.1f}{unit}"
        size /= 1024.0
    return f"{size:.1f}TB"

def list_directory_contents(path, indent="  ", max_depth=3, current_depth=0):
    """List directory contents recursively with detailed information"""
    if current_depth > max_depth:
        print_color(f"{indent}📁 ...", Fore.BLUE)
        return
        
    try:
        items = os.listdir(path)
        # Sort items: directories first, then files, both alphabetically
        dirs = sorted([item for item in items if os.path.isdir(os.path.join(path, item))])
        files = sorted([item for item in items if os.path.isfile(os.path.join(path, item))])
        
        # Print directories first
        for item in dirs:
            item_path = os.path.join(path, item)
            try:
                size = sum(os.path.getsize(os.path.join(dirpath,filename)) 
                          for dirpath, dirnames, filenames in os.walk(item_path)
                          for filename in filenames)
                print_color(f"{indent}📁 {item}/ ({format_size(size)})", Fore.BLUE, Style.BRIGHT)
                list_directory_contents(item_path, indent + "  ", max_depth, current_depth + 1)
            except Exception as e:
                print_color(f"{indent}❌ Error reading directory {item}: {e}", Fore.RED)
        
        # Then print files
        for item in files:
            item_path = os.path.join(path, item)
            try:
                size = os.path.getsize(item_path)
                # Color XML files differently
                if item.endswith('.xml'):
                    print_color(f"{indent}📄 {item} ({format_size(size)})", Fore.YELLOW)
                else:
                    print_color(f"{indent}📄 {item} ({format_size(size)})", Fore.WHITE)
            except Exception as e:
                print_color(f"{indent}❌ Error reading file {item}: {e}", Fore.RED)
                
    except Exception as e:
        print_color(f"{indent}❌ Error reading directory: {e}", Fore.RED)

def test_mod_directory(path, detailed=True):
    """Test a single mod directory"""
    print_color(f"\nTesting mod directory: {path}", Fore.CYAN, Style.BRIGHT)
    
    if not os.path.exists(path):
        print_color(f"Directory does not exist!", Fore.RED)
        return
    
    # Get basic directory info
    print_color("\nDirectory contents:", Fore.YELLOW)
    list_directory_contents(path)
    
    # Test mod validation
    print_color("\nMod validation:", Fore.YELLOW)
    is_valid, result = is_valid_mod_directory(path)
    if is_valid:
        print_color("✅ Valid mod directory", Fore.GREEN)
        if isinstance(result, dict):
            print_color("\nFound files:", Fore.YELLOW)
            for key, value in result.items():
                print_color(f"  {key}: {value}", Fore.GREEN)
    else:
        print_color(f"❌ Invalid mod directory: {result}", Fore.RED)
    
    # Get detailed mod info
    print_color("\nMod info:", Fore.YELLOW)
    info = get_mod_info(path)
    for key, value in info.items():
        if key == "files" and isinstance(value, dict):
            print_color(f"  {key}:", Fore.CYAN)
            for file_key, file_value in value.items():
                print_color(f"    {file_key}: {file_value}", Fore.CYAN)
        else:
            print_color(f"  {key}: {value}", Fore.CYAN)

def test_mods_directory(mods_path):
    """Test all mods in a directory"""
    print_color(f"Testing mods in: {mods_path}\n", Fore.WHITE, Style.BRIGHT)
    
    if not os.path.exists(mods_path):
        print_color(f"Directory does not exist!", Fore.RED)
        return
    
    # If this is a mod directory itself (has mod.xml), test it directly
    if os.path.exists(os.path.join(mods_path, "mod.xml")):
        test_mod_directory(mods_path, detailed=True)
        return
    
    # Otherwise test each subdirectory
    for item in sorted(os.listdir(mods_path)):
        item_path = os.path.join(mods_path, item)
        if os.path.isdir(item_path):
            test_mod_directory(item_path)
            print_color("\n" + "="*80 + "\n", Fore.WHITE)

if __name__ == "__main__":
    # If a path is provided as argument, use it
    if len(sys.argv) > 1:
        path = sys.argv[1]
        if os.path.isdir(path):
            # If path ends with a mod name (like @Baby seals), test just that mod
            if os.path.basename(path).startswith("@"):
                test_mod_directory(path, detailed=True)
            else:
                test_mods_directory(path)
        else:
            print_color(f"Invalid path: {path}", Fore.RED)
    else:
        # Try default Steam path
        default_path = r"C:\Program Files (x86)\Steam\steamapps\common\DoorKickers2\mods"
        if os.path.exists(default_path):
            test_mods_directory(default_path)
        else:
            print_color("Please provide a path to the mods directory as an argument", Fore.YELLOW)
            print_color("Example: python test_config.py \"C:\\Path\\To\\Mods\"", Fore.CYAN)
            print_color("Or test a specific mod: python test_config.py \"@Baby seals\"", Fore.CYAN) 