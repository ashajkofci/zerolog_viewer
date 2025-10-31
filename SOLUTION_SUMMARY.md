# Fix for "Version Unknown" and Missing License in PyInstaller Build

## Problem

When building the ZeroLog Viewer with PyInstaller, the application showed:
- "Version Unknown" in the window title and About dialog
- No license information displayed (empty or fallback message)

This was because PyInstaller creates a standalone executable that runs from a temporary directory, and the `VERSION` and `LICENSE` files were not being bundled with the executable.

## Root Cause

1. The original code used `Path(__file__).parent / 'VERSION'` to read version info
2. In PyInstaller executables, `__file__` points to a temporary extraction directory
3. The `VERSION` and `LICENSE` files were not included in the PyInstaller bundle
4. The build command (`pyinstaller --onefile --windowed ...`) didn't specify data files to include

## Solution

### 1. Created PyInstaller Spec File (`zerolog_viewer.spec`)

The spec file explicitly bundles resource files:

```python
datas = [
    (os.path.join(script_dir, 'VERSION'), '.'),
    (os.path.join(script_dir, 'LICENSE'), '.'),
]
```

### 2. Updated Resource Path Resolution

Added `get_resource_path()` function that works in both environments:

```python
def get_resource_path(relative_path: str) -> Path:
    try:
        # PyInstaller: use temporary extraction directory
        base_path = Path(sys._MEIPASS)
    except AttributeError:
        # Development: use source directory
        base_path = Path(__file__).parent
    return base_path / relative_path
```

### 3. Updated Version Info Function

Modified `get_version_info()` to:
- Use `get_resource_path()` to find the VERSION file
- Skip git version lookup in PyInstaller (not available in bundle)
- Provide better error messages

### 4. Added License Reading Function

Created `get_license_text()` to:
- Read license from bundled resource
- Provide fallback message if missing

### 5. Enhanced About Dialog

Updated `show_about()` to:
- Display actual version from VERSION file
- Add "View License" button
- Created `show_license()` dialog with full license text

### 6. Updated NSIS Installer

Modified `installer.nsi` to:
- Include VERSION and LICENSE files in installation directory (optional, for reference)
- Clean up these files during uninstall

### 7. Updated GitHub Actions Workflow

Changed all build jobs to use the spec file:
```yaml
- name: Build executable with PyInstaller
  run: |
    pyinstaller zerolog_viewer.spec
```

### 8. Updated .gitignore

Modified to allow `zerolog_viewer.spec` while still ignoring auto-generated spec files.

## Testing

Created comprehensive tests in `test_version_and_license.py`:
- Verifies version info is read correctly
- Ensures version is not "Unknown"
- Validates license text content
- All 30 tests pass

## Benefits

1. **Correct Version Display**: Users see the actual version (e.g., "Version 0.3.0")
2. **License Visibility**: Full BSD 3-Clause license is accessible via About dialog
3. **Cross-Platform**: Works on Windows, macOS, and Linux
4. **Maintainable**: Single spec file manages all resource bundling
5. **Testable**: Automated tests verify functionality

## Files Changed

- `zerolog_viewer.py`: Added resource path handling and license display
- `zerolog_viewer.spec`: New file for PyInstaller configuration
- `installer.nsi`: Include VERSION and LICENSE in Windows installer
- `.github/workflows/release.yml`: Use spec file for all builds
- `.gitignore`: Allow spec file
- `test_version_and_license.py`: New tests for version/license reading
- `PYINSTALLER.md`: Documentation for PyInstaller configuration

## Verification

To verify the fix works:

1. Build the executable: `pyinstaller zerolog_viewer.spec`
2. Run the executable: `./dist/zerolog_viewer`
3. Check window title shows version (e.g., "ZeroLog Viewer v0.3.0")
4. Open Help → About and verify version is displayed
5. Click "View License" button and verify full license text is shown

## Future Considerations

- Consider adding an icon file to the bundle
- Could bundle README or other documentation
- Version info could be auto-generated from git tags during CI/CD
