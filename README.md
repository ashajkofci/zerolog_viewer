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

## Quick Start

### Try It Now

```bash
# Run the app directly from source
python zerolog_viewer.py

# Click "Open File" and select sample_logs.jsonl
# You should see 6 colored log entries!
```

### What to Try

1. **Sort**: Click the "level" column header → logs sort by level
2. **Search**: Type "error" in search box → only error logs show
3. **Resize**: Drag column borders to adjust width
4. **Clear**: Click "Clear" to show all logs again

## Installation

### Option 1: Pre-built Packages (Recommended)

Download the latest release for your platform from the [Releases](https://github.com/ashajkofci/zerolog_viewer/releases) page:

- **Linux DEB**: `zerolog-viewer-X.X.X-amd64.deb`
  - Install with: `sudo dpkg -i zerolog-viewer-X.X.X-amd64.deb`
  - Includes desktop integration
- **macOS DMG**: `zerolog-viewer-X.X.X.dmg`
  - Mount the DMG and drag to Applications folder
  - Includes proper app bundle
- **Windows EXE**: `zerolog_viewer-windows-amd64.exe`
  - Download and run directly
  - No installation required

### Option 2: Run from Source

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

### Option 3: Build Your Own Executable

```bash
# Install PyInstaller and dependencies
pip install -r requirements.txt

# Build executable
pyinstaller --onefile --windowed --name zerolog_viewer zerolog_viewer.py

# Run the executable
./dist/zerolog_viewer  # Linux/Mac
# or
dist\zerolog_viewer.exe  # Windows
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



## Creating a Release

There are two ways to create a new release:

### Method 1: Workflow Dispatch (Recommended) ⭐

1. Go to the **Actions** tab in GitHub
2. Select **"Build and Release"** workflow
3. Click **"Run workflow"** button
4. Choose version bump type from dropdown:
   - **patch**: Bug fixes (0.2.0 → 0.2.1)
   - **minor**: New features (0.2.0 → 0.3.0)
   - **major**: Breaking changes (0.2.0 → 1.0.0)
5. Click **"Run workflow"**

The workflow will automatically:
- ✅ Run all tests
- ✅ Bump the version in the VERSION file
- ✅ Commit and push version change
- ✅ Create and push git tag
- ✅ Build packages for all platforms:
  - **Linux**: DEB package with desktop integration
  - **macOS**: DMG installer with app bundle
  - **Windows**: Standalone executable
- ✅ Create a GitHub release with all artifacts

**Total time:** ~10-15 minutes

### Method 2: Manual Tag Push

1. Update the VERSION file manually:
   ```bash
   echo "0.3.0" > VERSION
   ```
2. Commit the change:
   ```bash
   git add VERSION
   git commit -m "Bump version to 0.3.0"
   ```
3. Create and push tag:
   ```bash
   git tag v0.3.0
   git push origin main
   git push origin v0.3.0
   ```

GitHub Actions will automatically build and release.

### Version Management

Versions follow semantic versioning and are stored in the `VERSION` file:

- **Patch** (0.2.0 → 0.2.1): Bug fixes and minor updates
- **Minor** (0.2.0 → 0.3.0): New features, backwards compatible
- **Major** (0.2.0 → 1.0.0): Breaking changes

### Troubleshooting Releases

**Workflow Failed?**
1. Check the Actions tab for error logs
2. Look at the specific job that failed
3. Common issues:
   - Tests failed → Fix tests first
   - Build failed → Check dependencies
   - Permission denied → Check repository settings

**Need to Cancel?**
- Go to Actions tab
- Click on the running workflow
- Click "Cancel workflow"

**Delete a Release:**
```bash
# Delete tag locally and remotely
git tag -d vX.Y.Z
git push origin :refs/tags/vX.Y.Z

# Delete release on GitHub
# Go to Releases → Click on the release → Delete
```

## Troubleshooting

### Common Issues

**"python: command not found"**
- Try `python3` instead of `python`

**"No module named 'tkinter'"**
- Ubuntu/Debian: `sudo apt-get install python3-tk`
- macOS: tkinter included with Python
- Windows: tkinter included with Python

**"pyinstaller: command not found"**
```bash
pip install pyinstaller
```

## Development

### Requirements

- Python 3.8 or higher
- tkinter (usually included with Python)
- tkinterdnd2 (for drag and drop support)

### Technical Details

- **Language:** Python 3.8+
- **GUI Framework:** tkinter (built-in, cross-platform)
- **Build Tool:** PyInstaller
- **CI/CD:** GitHub Actions
- **Testing:** unittest + custom CLI tests

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

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT License - feel free to use this project for any purpose.

## Support

If you encounter any issues or have questions, please open an issue on GitHub.