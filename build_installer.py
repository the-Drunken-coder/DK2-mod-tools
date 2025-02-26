import os
import sys
import subprocess
import shutil
import time
import threading
from pathlib import Path
from datetime import datetime, timezone
from itertools import cycle
import re

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
    
    # Clean previous builds and create output directory
    output_dir = Path('output')
    output_dir.mkdir(exist_ok=True)
    
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
        '--add-data="modules;modules" '  # Include entire modules directory
        '--add-data="utils.py;." '  # Include utils.py
        '--add-data="LICENSE;." '  # Include license
        '--add-data="README.md;." '  # Include readme
        '--add-data="modding_tool_config.json;." '  # Include default config
        '--hidden-import=modules.config_editor_module '
        '--hidden-import=modules.entities_editor_module '
        '--hidden-import=modules.equipment_binding_editor_module '
        '--hidden-import=modules.gui_editor_module '
        '--hidden-import=modules.localization_editor_module '
        '--hidden-import=modules.mod_files '
        '--hidden-import=modules.mod_metadata_editor_module '
        '--hidden-import=modules.units_editor_module '
        '--collect-submodules=modules '  # Collect all submodules
        '--collect-data=modules '  # Collect all module data
        '--collect-all=modules '  # Ensure ALL module content is included
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
        '--distpath output '  # Set output directory to output/
        'modding_tool.py'
    )
    
    log("Running PyInstaller (this may take a few minutes)...")
    run_command(command)
    
    # Verify the build
    exe_path = os.path.join('output', 'DK2ModdingTool.exe')
    if os.path.exists(exe_path):
        size_mb = os.path.getsize(exe_path) / (1024 * 1024)
        log(f"Executable built successfully at {exe_path} (Size: {size_mb:.2f}MB)")
    else:
        log("Failed to find built executable!", "ERROR")
        sys.exit(1)

def create_installer():
    """Create the installer using Inno Setup"""
    log("Starting installer creation process...")
    
    # Create output directory if it doesn't exist
    output_dir = Path('output')
    output_dir.mkdir(exist_ok=True)
    
    # Inno Setup script
    log("Generating Inno Setup script...")
    iss_script = r'''
#define MyAppName "Door Kickers 2 Modding Tool"
#define MyAppVersion "0.1.0"
#define MyAppPublisher "DK2 Modding Community"
#define MyAppURL "https://github.com/yourusername/dk2-modding-tool"
#define MyAppExeName "DK2ModdingTool.exe"

[Setup]
AppId={{8BC9CEB8-8B4A-11D0-8D11-00A0C91BC942}}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={userdocs}\{#MyAppName}
DisableDirPage=no
DisableProgramGroupPage=yes
LicenseFile=LICENSE
OutputDir=output
OutputBaseFilename=DK2ModdingTool_Setup
SetupIconFile=resources/icon.ico
Compression=lzma
SolidCompression=yes
WizardStyle=modern
UninstallDisplayIcon={app}\{#MyAppExeName}
CreateUninstallRegKey=yes
UninstallDisplayName={#MyAppName}
PrivilegesRequired=lowest
DirExistsWarning=no
UsePreviousAppDir=no
PrivilegesRequiredOverridesAllowed=dialog

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
Source: "output\DK2ModdingTool.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "README.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "LICENSE"; DestDir: "{app}"; Flags: ignoreversion
Source: "utils.py"; DestDir: "{app}"; Flags: ignoreversion
Source: "modding_tool_config.json"; DestDir: "{app}"; Flags: ignoreversion
Source: "modules\*"; DestDir: "{app}\modules"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "modules\config_editor_module.py"; DestDir: "{app}\modules"; Flags: ignoreversion
Source: "modules\entities_editor_module.py"; DestDir: "{app}\modules"; Flags: ignoreversion
Source: "modules\equipment_binding_editor_module.py"; DestDir: "{app}\modules"; Flags: ignoreversion
Source: "modules\gui_editor_module.py"; DestDir: "{app}\modules"; Flags: ignoreversion
Source: "modules\localization_editor_module.py"; DestDir: "{app}\modules"; Flags: ignoreversion
Source: "modules\mod_files.py"; DestDir: "{app}\modules"; Flags: ignoreversion
Source: "modules\mod_metadata_editor_module.py"; DestDir: "{app}\modules"; Flags: ignoreversion
Source: "modules\units_editor_module.py"; DestDir: "{app}\modules"; Flags: ignoreversion

[Dirs]
Name: "{app}"; Permissions: users-full
Name: "{app}\modules"; Permissions: users-full

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{app}"
Type: dirifempty; Name: "{app}"

[Code]
procedure CurStepChanged(CurStep: TSetupStep);
var
  ResultCode: Integer;
begin
  if CurStep = ssPostInstall then
  begin
    // Set full permissions for the installation directory and all contents
    Exec('icacls.exe', 
         ExpandConstant('"{app}" /grant Users:(OI)(CI)F /T'), 
         '', 
         SW_HIDE, 
         ewWaitUntilTerminated, 
         ResultCode);
  end;
end;
'''
    
    # Write Inno Setup script
    log("Writing Inno Setup script to installer.iss...")
    with open('installer.iss', 'w') as f:
        f.write(iss_script)
    
    log("Verifying required files...")
    required_files = [
        'output/DK2ModdingTool.exe',
        'README.md',
        'LICENSE',
        'resources/icon.ico'
    ]
    for file in required_files:
        if not os.path.exists(file):
            log(f"Required file missing: {file}", "ERROR")
            sys.exit(1)
        else:
            log(f"Found required file: {file}")
    
    # Verify modules directory exists
    if not os.path.exists('modules'):
        log("Modules directory missing!", "ERROR")
        sys.exit(1)
    else:
        log("Found modules directory")
    
    # Run Inno Setup Compiler
    log("Running Inno Setup Compiler...")
    iscc_path = r'"C:\Program Files (x86)\Inno Setup 6\ISCC.exe"'
    run_command(f'{iscc_path} installer.iss')
    
    # Verify installer was created
    installer_path = os.path.join('output', 'DK2ModdingTool_Setup.exe')
    if os.path.exists(installer_path):
        size_mb = os.path.getsize(installer_path) / (1024 * 1024)
        log(f"Installer created successfully at {installer_path} (Size: {size_mb:.2f}MB)")
    else:
        log("Failed to find created installer!", "ERROR")
        sys.exit(1)

def zip_release_files(output_dir):
    """Create a zip archive of the release files"""
    log("Creating release archive...")
    try:
        # Create zip file with version number
        version = "0.1.0"  # TODO: Get this from a version file
        zip_name = f'DK2ModdingTool_v{version}_release.zip'
        zip_path = output_dir / zip_name
        
        # Create zip file
        import zipfile
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Add executable and installer
            for file in ['DK2ModdingTool.exe', 'DK2ModdingTool_Setup.exe']:
                file_path = output_dir / file
                if file_path.exists():
                    log(f"Adding {file} to release archive...")
                    zipf.write(file_path, file)
            
            # Add documentation files
            for file in ['README.md', 'LICENSE']:
                if os.path.exists(file):
                    log(f"Adding {file} to release archive...")
                    zipf.write(file, file)
        
        size_mb = os.path.getsize(zip_path) / (1024 * 1024)
        log(f"Release archive created successfully: {zip_path} (Size: {size_mb:.2f}MB)")
        return True
    except Exception as e:
        log(f"Failed to create release archive: {str(e)}", "ERROR")
        return False

def get_latest_version():
    """Get the latest version from git tags"""
    try:
        # Get the latest tag
        result = subprocess.run(['git', 'describe', '--tags', '--abbrev=0'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            # Remove 'v' prefix if present and return
            return result.stdout.strip().lstrip('v')
    except Exception:
        pass
    return "0.1.0"  # Default if no tags found

def get_changes_since_last_tag():
    """Get all commit messages since the last tag"""
    try:
        # Get the latest tag
        tag_result = subprocess.run(['git', 'describe', '--tags', '--abbrev=0'],
                                  capture_output=True, text=True)
        if tag_result.returncode != 0:
            # If no tags exist, get all commits
            commits = subprocess.run(['git', 'log', '--pretty=format:%s'],
                                  capture_output=True, text=True)
        else:
            # Get commits since last tag
            commits = subprocess.run(['git', 'log', f'{tag_result.stdout.strip()}..HEAD', '--pretty=format:%s'],
                                  capture_output=True, text=True)

        if commits.returncode == 0:
            changes = commits.stdout.strip().split('\n')
            
            # Categorize changes based on commit message prefixes
            categorized = {
                'Added': [],
                'Changed': [],
                'Fixed': [],
                'Other': []
            }
            
            for change in changes:
                if change.lower().startswith(('add', 'new', 'implement')):
                    categorized['Added'].append(change)
                elif change.lower().startswith(('change', 'update', 'improve', 'enhance')):
                    categorized['Changed'].append(change)
                elif change.lower().startswith(('fix', 'bug', 'resolve')):
                    categorized['Fixed'].append(change)
                else:
                    categorized['Other'].append(change)
            
            # Format the changes
            formatted = []
            for category, items in categorized.items():
                if items:
                    formatted.append(f"### {category}")
                    formatted.extend(f"- {item}" for item in items)
                    formatted.append("")  # Add blank line between categories
            
            return "\n".join(formatted)
    except Exception as e:
        log(f"Error getting changes: {str(e)}", "ERROR")
    
    return "No changes documented"

def create_github_release():
    """Create a GitHub release with the installer"""
    log("Creating GitHub release...")
    
    output_dir = Path('output')
    output_dir.mkdir(exist_ok=True)  # Create output directory if it doesn't exist
    
    installer_path = output_dir / 'DK2ModdingTool_Setup.exe'
    if not installer_path.exists():
        log("Installer not found! Please build it first.", "ERROR")
        return False
    
    # Get version and changes from git
    version = get_latest_version()
    changes = get_changes_since_last_tag()
    
    # Create release notes
    release_notes = f'''# Door Kickers 2 Modding Tool v{version}

## Installation
1. Download DK2ModdingTool_Setup.exe
2. Run the installer
3. Follow the installation wizard
4. Launch the tool from the Start Menu or Desktop shortcut

## Changes in this version
{changes}

## Known Issues
Please see the README.md for current known issues and limitations.

## Support
If you encounter any issues, please report them on the GitHub issues page.
'''
    
    release_notes_path = output_dir / 'RELEASE_NOTES.md'
    with open(release_notes_path, 'w', encoding='utf-8') as f:
        f.write(release_notes)
            
    log("Release files prepared successfully!")
    
    # Create zip archive of release files
    if not zip_release_files(output_dir):
        return False
            
    log("\nTo create the GitHub release:")
    log("1. Go to your GitHub repository")
    log("2. Click 'Releases' then 'Create new release'")
    log(f"3. Create a new tag (e.g. v{version})")
    log("4. Upload the files from the 'output' directory:")
    log(f"   - DK2ModdingTool_v{version}_release.zip (contains all release files)")
    log("5. Copy the contents of RELEASE_NOTES.md into the release description")
    log("6. Click 'Publish release'")
    
    return True

def main():
    log("Starting build process...")
    
    # Clean ALL previous build artifacts and cache
    cleanup_paths = [
        'build', 
        'dist', 
        'output',
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
        # Create output directory
        output_dir = Path('output')
        output_dir.mkdir(exist_ok=True)
        
        # Build executable
        build_executable()
        
        # Create installer
        create_installer()
        
        # Create GitHub release
        create_github_release()
        
        log("Build process completed successfully!")
        log("\nAll output files are in the 'output' directory:")
        log("- DK2ModdingTool.exe (Executable)")
        log("- DK2ModdingTool_Setup.exe (Installer)")
        log("- DK2ModdingTool_v0.1.0_release.zip (Release archive)")
        log("- RELEASE_NOTES.md")
        
    except Exception as e:
        log(f"Build process failed: {str(e)}", "ERROR")
        import traceback
        log("Traceback:", "ERROR")
        print(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    main() 