import os
import sys
import subprocess
import shutil
import time
import threading
from pathlib import Path
from datetime import datetime
from itertools import cycle

class Spinner:
    def __init__(self):
        self.spinner = cycle(['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏'])
        self.busy = False
        self.spinner_visible = False
        sys.stdout.write('\033[?25l')  # Hide cursor

    def write_next(self):
        with self._screen_lock:
            if not self.spinner_visible:
                sys.stdout.write(next(self.spinner))
                self.spinner_visible = True
                sys.stdout.flush()

    def remove_spinner(self, cleanup=False):
        with self._screen_lock:
            if self.spinner_visible:
                sys.stdout.write('\b')
                self.spinner_visible = False
                if cleanup:
                    sys.stdout.write(' ')
                    sys.stdout.write('\r')
                sys.stdout.flush()

    def spinner_task(self):
        while self.busy:
            self.write_next()
            time.sleep(0.1)
            self.remove_spinner()

    def __enter__(self):
        if sys.stdout.isatty():
            self._screen_lock = threading.Lock()
            self.busy = True
            self.thread = threading.Thread(target=self.spinner_task)
            self.thread.start()

    def __exit__(self, exc_type, exc_val, exc_tb):
        if sys.stdout.isatty():
            self.busy = False
            time.sleep(0.2)
            self.remove_spinner(cleanup=True)
            sys.stdout.write('\033[?25h')  # Show cursor

def log(message, level="INFO", spinner=False):
    """Log a message with timestamp"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    if spinner:
        print(f"\r[{timestamp}] {level}: {message}", end="", flush=True)
    else:
        print(f"[{timestamp}] {level}: {message}")

def run_command(command):
    """Run a command and return its output"""
    try:
        log(f"Executing command: {command}")
        start_time = time.time()
        
        # Run process with real-time output
        process = subprocess.Popen(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1
        )

        # Print output in real-time with spinner
        log("Command output:")
        with Spinner():
            while True:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
                if output:
                    print(f"\r{output.strip()}")
        
        return_code = process.poll()
        duration = time.time() - start_time
        
        if return_code == 0:
            log(f"Command completed successfully in {duration:.2f} seconds")
        else:
            log(f"Command failed with exit code {return_code}", "ERROR")
            sys.exit(1)
            
    except Exception as e:
        log(f"Failed to execute command: {str(e)}", "ERROR")
        sys.exit(1)

def build_executable():
    """Build the executable using PyInstaller"""
    log("Starting executable build process...")
    
    # Clean previous builds
    for path in ['build', 'dist']:
        if os.path.exists(path):
            log(f"Cleaning {path} directory...")
            shutil.rmtree(path)
            log(f"Cleaned {path} directory")
    
    # PyInstaller command using Python module with verbose output
    log("Configuring PyInstaller command...")
    command = (
        f'{sys.executable} -m PyInstaller '
        '--name=DK2ModdingTool '
        '--windowed '
        '--onefile '
        '--icon=resources/icon.ico '
        '--add-data="modules;modules" '  # Only include our modules
        '--clean '  # Clean PyInstaller cache
        '--noupx '  # Don't use UPX compression (can cause issues)
        '--exclude-module=matplotlib '  # Exclude unnecessary large packages
        '--exclude-module=numpy '
        '--exclude-module=PIL '
        '--exclude-module=pandas '
        '--exclude-module=scipy '
        '--exclude-module=PyQt5 '
        '--exclude-module=PySide2 '
        '--exclude-module=wx '
        '--collect-all=tkinter '  # Ensure tkinter is fully included
        '--noconsole '
        '--log-level=INFO '
        'modding_tool.py'
    )
    
    log("Running PyInstaller (this may take a few minutes)...")
    run_command(command)
    
    # Verify the build
    exe_path = os.path.join('dist', 'DK2ModdingTool.exe')
    if os.path.exists(exe_path):
        size_mb = os.path.getsize(exe_path) / (1024 * 1024)
        log(f"Executable built successfully at {exe_path} (Size: {size_mb:.2f}MB)")
    else:
        log("Failed to find built executable!", "ERROR")
        sys.exit(1)

def create_installer():
    """Create the installer using Inno Setup"""
    log("Starting installer creation process...")
    
    # Inno Setup script
    log("Generating Inno Setup script...")
    iss_script = f'''
#define MyAppName "Door Kickers 2 Modding Tool"
#define MyAppVersion "0.1.0"
#define MyAppPublisher "DK2 Modding Community"
#define MyAppURL "https://github.com/yourusername/dk2-modding-tool"
#define MyAppExeName "DK2ModdingTool.exe"

[Setup]
AppId={{{{8BC9CEB8-8B4A-11D0-8D11-00A0C91BC942}}}}
AppName={{#MyAppName}}
AppVersion={{#MyAppVersion}}
AppPublisher={{#MyAppPublisher}}
AppPublisherURL={{#MyAppURL}}
AppSupportURL={{#MyAppURL}}
AppUpdatesURL={{#MyAppURL}}
DefaultDirName={{autopf}}\\{{#MyAppName}}
DisableProgramGroupPage=yes
LicenseFile=LICENSE
OutputDir=installer
OutputBaseFilename=DK2ModdingTool_Setup
SetupIconFile=resources/icon.ico
Compression=lzma
SolidCompression=yes
WizardStyle=modern

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{{cm:CreateDesktopIcon}}"; GroupDescription: "{{cm:AdditionalIcons}}"

[Files]
Source: "dist\\DK2ModdingTool.exe"; DestDir: "{{app}}"; Flags: ignoreversion
Source: "README.md"; DestDir: "{{app}}"; Flags: ignoreversion
Source: "LICENSE"; DestDir: "{{app}}"; Flags: ignoreversion

[Icons]
Name: "{{autoprograms}}\\{{#MyAppName}}"; Filename: "{{app}}\\{{#MyAppExeName}}"
Name: "{{autodesktop}}\\{{#MyAppName}}"; Filename: "{{app}}\\{{#MyAppExeName}}"; Tasks: desktopicon

[Run]
Filename: "{{app}}\\{{#MyAppExeName}}"; Description: "{{cm:LaunchProgram,{{#StringChange(MyAppName, '&', '&&')}}}}"; Flags: nowait postinstall skipifsilent
    '''
    
    # Create installer directory if it doesn't exist
    installer_dir = Path('installer')
    installer_dir.mkdir(exist_ok=True)
    
    # Write Inno Setup script
    log("Writing Inno Setup script to installer.iss...")
    with open('installer.iss', 'w') as f:
        f.write(iss_script)
    
    # Verify required files
    log("Verifying required files...")
    required_files = ['dist/DK2ModdingTool.exe', 'README.md', 'LICENSE', 'resources/icon.ico']
    for file in required_files:
        if not os.path.exists(file):
            log(f"Required file missing: {file}", "ERROR")
            sys.exit(1)
        else:
            log(f"Found required file: {file}")
    
    # Run Inno Setup Compiler
    log("Running Inno Setup Compiler...")
    iscc_path = r'"C:\Program Files (x86)\Inno Setup 6\ISCC.exe"'
    run_command(f'{iscc_path} installer.iss')
    
    # Verify installer was created
    installer_path = os.path.join('installer', 'DK2ModdingTool_Setup.exe')
    if os.path.exists(installer_path):
        size_mb = os.path.getsize(installer_path) / (1024 * 1024)
        log(f"Installer created successfully at {installer_path} (Size: {size_mb:.2f}MB)")
    else:
        log("Failed to find created installer!", "ERROR")
        sys.exit(1)

def create_github_release():
    """Create a GitHub release with the installer"""
    log("Creating GitHub release...")
    
    installer_path = os.path.join('installer', 'DK2ModdingTool_Setup.exe')
    if not os.path.exists(installer_path):
        log("Installer not found! Please build it first.", "ERROR")
        return False
        
    # Create release directory
    release_dir = Path('release')
    release_dir.mkdir(exist_ok=True)
    
    # Copy files to release directory
    log("Copying files to release directory...")
    try:
        # Copy installer
        shutil.copy2(installer_path, release_dir / 'DK2ModdingTool_Setup.exe')
        
        # Copy README and LICENSE
        shutil.copy2('README.md', release_dir / 'README.md')
        shutil.copy2('LICENSE', release_dir / 'LICENSE')
        
        # Create release notes
        release_notes = f'''# Door Kickers 2 Modding Tool Release

## Installation
1. Download DK2ModdingTool_Setup.exe
2. Run the installer
3. Follow the installation wizard
4. Launch the tool from the Start Menu or Desktop shortcut

## Changes in this version
- GUI Layout Editor improvements
- Equipment binding fixes
- Improved mod file handling
- Better error handling
- Various bug fixes and improvements

## Known Issues
Please see the README.md for current known issues and limitations.

## Support
If you encounter any issues, please report them on the GitHub issues page.
'''
        
        with open(release_dir / 'RELEASE_NOTES.md', 'w') as f:
            f.write(release_notes)
            
        log("Release files prepared successfully!")
        log("\nTo create the GitHub release:")
        log("1. Go to your GitHub repository")
        log("2. Click 'Releases' then 'Create new release'")
        log("3. Create a new tag (e.g. v0.1.0)")
        log("4. Upload the files from the 'release' directory:")
        log("   - DK2ModdingTool_Setup.exe")
        log("   - README.md")
        log("   - LICENSE")
        log("5. Copy the contents of RELEASE_NOTES.md into the release description")
        log("6. Click 'Publish release'")
        
        return True
        
    except Exception as e:
        log(f"Failed to prepare release: {str(e)}", "ERROR")
        return False

def main():
    log("Starting build process...")
    
    # Clean ALL previous build artifacts and cache
    cleanup_paths = [
        'build', 
        'dist', 
        'installer',
        'release',
        '__pycache__',
        'modules/__pycache__',
        'DK2ModdingTool.spec'
    ]
    
    for path in cleanup_paths:
        if os.path.exists(path):
            log(f"Cleaning {path}...")
            try:
                if os.path.isfile(path):
                    os.remove(path)
                else:
                    shutil.rmtree(path)
                log(f"Cleaned {path}")
            except Exception as e:
                log(f"Error cleaning {path}: {str(e)}", "WARNING")
    
    # Clean all .pyc files recursively
    log("Cleaning .pyc files...")
    for root, dirs, files in os.walk('.'):
        for file in files:
            if file.endswith('.pyc'):
                try:
                    os.remove(os.path.join(root, file))
                    log(f"Removed {os.path.join(root, file)}")
                except Exception as e:
                    log(f"Error removing {file}: {str(e)}", "WARNING")
    
    # Create resources directory if it doesn't exist
    if not os.path.exists('resources'):
        log("Creating resources directory...")
        os.makedirs('resources')
    
    # Check if icon exists
    if not os.path.exists('resources/icon.ico'):
        log("Icon file missing at resources/icon.ico", "ERROR")
        log("Please run setup_build_env.py first to create the icon", "ERROR")
        return
    else:
        log("Found icon file")
    
    try:
        # Build executable
        build_executable()
        
        # Create installer
        create_installer()
        
        # Create GitHub release
        create_github_release()
        
        log("Build process completed successfully!")
        
    except Exception as e:
        log(f"Build process failed: {str(e)}", "ERROR")
        import traceback
        log("Traceback:", "ERROR")
        print(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    main() 