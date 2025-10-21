# Windows Installer Documentation

This document describes the Windows installer implementation for ZeroLog Viewer.

## Overview

As of this release, ZeroLog Viewer provides **two Windows distribution options**:

1. **Standalone EXE** (`zerolog_viewer-windows-amd64.exe`) - Portable executable that can be run from any location
2. **Windows Installer** (`zerolog-viewer-X.X.X-installer.exe`) - Full installer package

## Installer Features

The Windows installer (created with NSIS) provides the following features:

### Installation Options

- **Required**: Main application installation to Program Files
- **Optional**: Start Menu shortcuts (recommended)
- **Optional**: Desktop shortcut
- **Optional**: .jsonl file association (allows double-clicking .jsonl files to open in ZeroLog Viewer)

### Installation Details

- **Install Location**: `C:\Program Files\ZeroLog Viewer\`
- **Start Menu**: Creates "ZeroLog Viewer" folder with application and uninstall shortcuts
- **Registry Keys**: Stores installation path and uninstaller information
- **File Association**: Optionally registers `.jsonl` file extension

### Uninstallation

The installer includes a proper uninstaller that:
- Removes all installed files
- Removes Start Menu shortcuts
- Removes Desktop shortcut (if created)
- Removes file associations (if created)
- Removes registry keys
- Cleans up installation directory

Access the uninstaller via:
- Start Menu → ZeroLog Viewer → Uninstall
- Windows Settings → Apps → ZeroLog Viewer → Uninstall
- Control Panel → Programs and Features → ZeroLog Viewer

## Build Process

The installer is built automatically by GitHub Actions when creating a release. The build process:

1. Builds the standalone executable using PyInstaller
2. Installs NSIS (Nullsoft Scriptable Install System)
3. Runs the `installer.nsi` script to create the installer
4. Uploads both the standalone exe and installer as separate artifacts
5. Includes both in the GitHub release

## Files

- `installer.nsi` - NSIS script that defines the installer behavior
- `.github/workflows/release.yml` - Updated to build both exe and installer

## For Users

### Which Version Should I Use?

**Use the Installer if:**
- You want Start Menu integration
- You want Desktop shortcuts
- You want to associate .jsonl files with ZeroLog Viewer
- You prefer traditional Windows installation experience
- You want easy uninstallation through Windows Settings

**Use the Standalone EXE if:**
- You want a portable version
- You don't have admin rights to install software
- You want to run from a USB drive or network location
- You prefer minimal system integration
- You want to test the application without installing

### Installation Instructions

#### For the Installer:
1. Download `zerolog-viewer-X.X.X-installer.exe` from the [Releases](https://github.com/ashajkofci/zerolog_viewer/releases) page
2. Double-click to run the installer
3. Follow the installation wizard
4. Choose optional components (shortcuts, file association)
5. Click Install

#### For the Standalone EXE:
1. Download `zerolog_viewer-windows-amd64.exe` from the [Releases](https://github.com/ashajkofci/zerolog_viewer/releases) page
2. Save it anywhere you like
3. Double-click to run (no installation needed)

## Technical Details

### NSIS Script Structure

The `installer.nsi` script is organized into sections:

- **Configuration**: Version, product name, publisher info
- **UI Pages**: Welcome, components selection, directory, installation progress, finish
- **Sections**:
  - SEC01: Core application (required)
  - SEC02: Start Menu shortcuts (optional)
  - SEC03: Desktop shortcut (optional)
  - SEC04: File association (optional)
- **Uninstaller**: Complete removal of all components

### Version Handling

The installer version is dynamically set during the build process:
- The NSIS script defines a default version
- During GitHub Actions build, the version is overridden via `/DVERSION=X.X.X` command-line parameter
- The version appears in the installer filename and Windows Programs list

### Requirements

- Windows 7 or later (64-bit)
- Administrator privileges (for installation to Program Files)
- Approximately 50 MB disk space

## For Developers

### Testing the Installer Locally

To build the installer locally (on Windows):

1. Install NSIS from https://nsis.sourceforge.io/
2. Build the executable: `pyinstaller --onefile --windowed --name zerolog_viewer zerolog_viewer.py`
3. Build the installer: `makensis /DVERSION=0.2.0 installer.nsi`
4. Test the resulting installer

### Modifying the Installer

To modify the installer behavior, edit `installer.nsi`:
- Add new files in the main section
- Add/remove optional components by adding/removing sections
- Modify UI pages by changing the `!insertmacro` directives
- Update registry keys as needed

After modifying, test thoroughly on a clean Windows system.
