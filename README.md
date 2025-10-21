# ZeroLog Viewer

A cross-platform GUI application for viewing and analyzing JSONL (JSON Lines) log files, specifically designed for zerolog format but compatible with any JSONL format.

## Features

- 📂 **Cross-platform**: Works on Windows, macOS, and Linux
- 📑 **Multi-tab interface**: Open multiple log files in separate tabs
- 🖱️ **Drag & Drop**: Drag and drop files directly into the application
- 📊 **Automatic column sizing**: Columns automatically adjust to content
- 🕐 **Time-based indexing**: Logs are automatically sorted by timestamp
- 🔄 **Sortable columns**: Click any column header to sort
- 🔍 **Debounced search**: Real-time search with 300ms debounce for smooth performance
- 📅 **Date range filtering**: Filter logs by date range (optional)
- 🎨 **Color-coded levels**: Different colors for debug, info, warn, error, etc.
- 🚀 **High performance**: Efficiently handles large files (100MB+) with lazy loading
- 💾 **Standalone executables**: Pre-built binaries available for all platforms

## Performance

The viewer is optimized for large log files:
- **Lazy loading**: Displays 1,000 entries at a time, loads more as you scroll
- **Background loading**: Files load in a background thread for responsive UI
- **Efficient parsing**: Can parse 300,000+ entries per second
- **Memory efficient**: Only displays visible rows in the UI
- **100MB+ files**: Tested with files containing 50,000+ entries

## Installation

### Using Pre-built Packages (Recommended)

Download the latest release for your platform from the [Releases](https://github.com/ashajkofci/zerolog_viewer/releases) page:

- **Linux DEB**: `zerolog-viewer-X.X.X-amd64.deb`
  - Install with: `sudo dpkg -i zerolog-viewer-X.X.X-amd64.deb`
  - Includes desktop integration
- **macOS DMG**: `zerolog-viewer-X.X.X.dmg`
  - Mount the DMG and drag to Applications folder
  - Includes proper app bundle
- **Windows Installer**: `zerolog-viewer-X.X.X-installer.exe`
  - Run the installer to install to Program Files
  - Creates Start Menu shortcuts and optionally Desktop shortcut
  - Optional .jsonl file association for double-click opening
- **Windows Standalone EXE**: `zerolog_viewer-windows-amd64.exe`
  - Download and run directly
  - No installation required
  - Portable - can be run from any location

### Running from Source

If you prefer to run from source:

```bash
# Clone the repository
git clone https://github.com/ashajkofci/zerolog_viewer.git
cd zerolog_viewer

# Install dependencies
pip install -r requirements.txt

# Run the application
python zerolog_viewer.py
```

## Usage

1. **Launch the application** by double-clicking the executable or running `python zerolog_viewer.py`
2. **Open files** via:
   - Click the "Open File" button
   - Use File → Open JSONL File menu
   - **Drag and drop** one or more files into the window
3. **View your logs** with automatic column sizing and color-coding
4. **Switch between files** using the tab interface
5. **Sort** by clicking column headers
6. **Search** by typing in the search box (with 300ms debounce)
7. **Filter by date** using the date range fields (optional)
8. **Adjust columns** by dragging column borders

### New in This Version

#### Multi-Tab Interface
- Open multiple log files simultaneously
- Each file opens in its own tab
- Switch between files easily
- Close tabs when done

#### Drag & Drop Support
- Drag files from your file explorer
- Drop them into the application window
- Multiple files open in separate tabs automatically

#### Date Range Filtering
- Enter "From" and/or "To" dates in ISO 8601 format
- Example: `2025-10-20T17:19:16Z`
- Click "Apply Date Filter" to filter logs
- Click "Clear Date Filter" to show all logs

#### Debounced Search
- Search input now has a 300ms debounce
- Prevents lag when typing quickly
- Smoother user experience

#### Performance Improvements
- Lazy loading: Only 1,000 items loaded initially
- Scroll down to load more items automatically
- Background file loading for large files
- Progress indicators during loading
- Can handle 100MB+ files efficiently

### Sample JSONL Format

The viewer works with any JSONL file, such as:

```json
{"level":"debug","git_revision":"v0.9.0-3f5b689","serialNumber":"910335","organizationID":"67e59f3d11d57bb940742d07","deviceID":"68cd61eaadba4ed22ccdc080","duration":2.750617,"time":"2025-10-20T17:19:16Z","message":"Device found"}
{"level":"info","time":"2025-10-20T17:19:17Z","message":"Connection established"}
{"level":"error","time":"2025-10-20T17:19:18Z","message":"Failed to process request"}
```

## Color Coding

Logs are automatically color-coded based on their level:

- 🔵 **Debug**: Gray
- 🔵 **Info**: Blue
- 🟠 **Warn/Warning**: Orange
- 🔴 **Error**: Red
- ⚫ **Fatal/Panic**: Dark Red

## Building from Source

To create your own executable:

```bash
# Install dependencies including build tools
pip install -r requirements.txt

# Build the executable
pyinstaller --onefile --windowed --name zerolog_viewer zerolog_viewer.py

# The executable will be in the dist/ folder
```

## Development

### Requirements

- Python 3.8 or higher
- tkinter (usually included with Python)
- tkinterdnd2 (for drag and drop support)

### Running Tests

```bash
# Test with the included sample files
python zerolog_viewer.py
# Then open sample_logs.jsonl or large_sample_logs.jsonl

# Run unit tests
python test_zerolog_viewer.py

# Run CLI tests
python test_cli.py
```

## Creating a Release

There are two ways to create a new release:

### Method 1: Manual Workflow Dispatch (Recommended)

1. Go to the Actions tab in GitHub
2. Select "Build and Release" workflow
3. Click "Run workflow"
4. Choose version bump type:
   - **patch**: Bug fixes (0.2.0 → 0.2.1)
   - **minor**: New features (0.2.0 → 0.3.0)
   - **major**: Breaking changes (0.2.0 → 1.0.0)
5. The workflow will:
   - Run all tests
   - Bump the version in the VERSION file
   - Create a git tag
   - Build packages for all platforms:
     - **Linux**: DEB package
     - **macOS**: DMG installer
     - **Windows**: Installer (with Start Menu shortcuts) and standalone executable
   - Create a GitHub release with all artifacts

### Method 2: Git Tag Push

1. Update the VERSION file manually
2. Create and push a tag:
   ```bash
   git tag v1.1.0
   git push origin v1.1.0
   ```
3. GitHub Actions will automatically build packages for all platforms

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT License - feel free to use this project for any purpose.

## Support

If you encounter any issues or have questions, please open an issue on GitHub.