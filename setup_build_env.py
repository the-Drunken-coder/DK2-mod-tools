import os
import sys
import urllib.request
import subprocess
import tempfile
import winreg
import argparse
from pathlib import Path

def download_file(url, filename):
    """Download a file with progress indicator"""
    print(f"Downloading {filename}...")
    try:
        urllib.request.urlretrieve(
            url, 
            filename,
            lambda count, block_size, total_size: print(
                f"Progress: {count * block_size * 100 / total_size:.1f}%", 
                end='\r'
            ) if total_size > 0 else None
        )
        print("\nDownload completed!")
        return True
    except Exception as e:
        print(f"Error downloading file: {e}")
        return False

def is_inno_setup_installed():
    """Check if Inno Setup is installed"""
    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, 
                           r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\Inno Setup 6_is1",
                           0, winreg.KEY_READ | winreg.KEY_WOW64_32KEY) as key:
            return True
    except WindowsError:
        return False

def install_inno_setup():
    """Download and install Inno Setup"""
    if is_inno_setup_installed():
        print("Inno Setup is already installed!")
        return True

    print("Installing Inno Setup...")
    inno_url = "https://files.jrsoftware.org/is/6/innosetup-6.2.2.exe"
    
    # Create temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        installer_path = os.path.join(temp_dir, "innosetup.exe")
        
        # Download installer
        if not download_file(inno_url, installer_path):
            return False
        
        # Run installer silently
        try:
            subprocess.run([installer_path, "/VERYSILENT", "/SUPPRESSMSGBOXES", 
                          "/NORESTART", "/SP-"], check=True)
            print("Inno Setup installed successfully!")
            return True
        except subprocess.CalledProcessError as e:
            print(f"Error installing Inno Setup: {e}")
            return False

def check_dependencies():
    """Check if build dependencies are installed"""
    try:
        import pyinstaller
        import PIL
        return True
    except ImportError:
        return False

def install_dependencies():
    """Install build dependencies"""
    print("Installing build dependencies...")
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements-build.txt"], 
                      check=True)
        print("Build dependencies installed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error installing build dependencies: {e}")
        return False

def create_resources():
    """Create resources directory and icon"""
    resources_dir = Path("resources")
    resources_dir.mkdir(exist_ok=True)
    
    if not (resources_dir / "icon.ico").exists():
        print("Creating icon...")
        try:
            from create_icon import create_icon
            create_icon()
            return True
        except Exception as e:
            print(f"Error creating icon: {e}")
            return False
    else:
        print("Icon already exists")
        return True

def setup_build_environment(components=None):
    """Set up the build environment
    
    Args:
        components (list): List of components to install. Options:
            - 'inno': Install Inno Setup
            - 'deps': Install build dependencies
            - 'icon': Create icon
            If None, checks and installs missing components only.
    """
    print("Checking build environment...")
    
    if not sys.platform.startswith('win'):
        print("This script is only for Windows!")
        return False
    
    success = True
    components = components or ['inno', 'deps', 'icon']
    
    # Check and install components as needed
    if 'inno' in components and not is_inno_setup_installed():
        success &= install_inno_setup()
    
    if 'deps' in components and not check_dependencies():
        success &= install_dependencies()
    
    if 'icon' in components:
        success &= create_resources()
    
    if success:
        print("\nBuild environment is ready!")
        print("You can now run 'python build_installer.py' to create the installer.")
    else:
        print("\nSome components failed to install. Please check the errors above.")
    
    return success

def main():
    parser = argparse.ArgumentParser(description='Setup build environment for DK2 Modding Tool')
    parser.add_argument('--inno', action='store_true', help='Install/check Inno Setup only')
    parser.add_argument('--deps', action='store_true', help='Install/check build dependencies only')
    parser.add_argument('--icon', action='store_true', help='Create/check icon only')
    parser.add_argument('--all', action='store_true', help='Install/check all components')
    
    args = parser.parse_args()
    
    # Determine which components to install
    if args.all:
        components = ['inno', 'deps', 'icon']
    else:
        components = []
        if args.inno:
            components.append('inno')
        if args.deps:
            components.append('deps')
        if args.icon:
            components.append('icon')
        # If no arguments provided, check all components but only install if missing
        if not components:
            components = ['inno', 'deps', 'icon']
    
    if setup_build_environment(components):
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main() 