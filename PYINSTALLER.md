# PyInstaller Configuration

This document explains how the ZeroLog Viewer is packaged using PyInstaller and how version and license information is bundled with the executable.

## Overview

When building standalone executables with PyInstaller, resource files (like `VERSION` and `LICENSE`) need to be explicitly bundled with the executable. This is configured in the `zerolog_viewer.spec` file.

## Spec File Configuration

The `zerolog_viewer.spec` file is a PyInstaller configuration file that:

1. **Bundles Data Files**: Includes `VERSION` and `LICENSE` files in the executable
2. **Sets Build Options**: Configures one-file mode, windowed mode (no console), and other settings
3. **Platform-Specific Handling**: Creates an app bundle for macOS

### Data Files

```python
datas = [
    (os.path.join(script_dir, 'VERSION'), '.'),
    (os.path.join(script_dir, 'LICENSE'), '.'),
]
```

These files are extracted to a temporary directory at runtime and accessed via `sys._MEIPASS`.

## Resource Path Resolution

The `get_resource_path()` function in `zerolog_viewer.py` handles both development and PyInstaller environments:

```python
def get_resource_path(relative_path: str) -> Path:
    """Get absolute path to resource, works for dev and for PyInstaller."""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = Path(sys._MEIPASS)
    except AttributeError:
        # Running in normal Python environment
        base_path = Path(__file__).parent
    
    return base_path / relative_path
```

### How It Works

- **Development**: Reads files from the source directory
- **PyInstaller**: Reads files from the temporary extraction directory (`sys._MEIPASS`)

## Version Information

The `get_version_info()` function:

1. Reads version from the bundled `VERSION` file
2. Attempts to get git version info (only in development)
3. Returns both values or 'Unknown' if files are missing

## License Display

The `get_license_text()` function:

1. Reads the full license text from the bundled `LICENSE` file
2. Returns the text for display in the About dialog
3. Falls back to a generic message if the file is missing

## Building

### Using the Spec File

```bash
# Build with the spec file (recommended)
pyinstaller zerolog_viewer.spec

# Output will be in dist/zerolog_viewer (or dist/ZeroLog Viewer.app on macOS)
```

### Manual Build (Not Recommended)

```bash
# This won't include VERSION and LICENSE files
pyinstaller --onefile --windowed --name zerolog_viewer zerolog_viewer.py
```

## Testing

To verify that resources are bundled correctly:

```bash
# Run the tests
python3 -m pytest test_version_and_license.py -v
```

These tests verify:
- Version info is read correctly
- Version is not 'Unknown'
- License text is available
- License contains expected content

## Continuous Integration

The GitHub Actions workflow (`release.yml`) uses the spec file for all platform builds:

- **Windows**: Builds with `pyinstaller zerolog_viewer.spec`, then creates NSIS installer
- **Linux**: Builds with `pyinstaller zerolog_viewer.spec`, then creates DEB package
- **macOS**: Builds with `pyinstaller zerolog_viewer.spec`, creates app bundle, then DMG

## Troubleshooting

### Version Shows "Unknown"

1. Ensure `VERSION` file exists in the repository root
2. Check that `zerolog_viewer.spec` includes the file in `datas`
3. Verify `get_resource_path()` is used to read the file

### License Not Displayed

1. Ensure `LICENSE` file exists in the repository root
2. Check that `zerolog_viewer.spec` includes the file in `datas`
3. Verify `get_license_text()` is called in the About dialog

### Build Fails

1. Ensure PyInstaller is installed: `pip install pyinstaller`
2. Check that all dependencies are installed: `pip install -r requirements.txt`
3. Verify spec file syntax is correct

## Platform-Specific Notes

### Windows

- NSIS installer also includes `VERSION` and `LICENSE` files in the installation directory
- These are separate from the PyInstaller bundle (for user reference)

### macOS

- The spec file creates a `.app` bundle automatically
- Version info is also set in `Info.plist` during CI/CD

### Linux

- DEB package includes only the executable (with bundled resources)
- No separate resource files needed
