# ZeroLog Viewer

A cross-platform GUI application for viewing and analyzing JSONL (JSON Lines) log files, specifically designed for zerolog format but compatible with any JSONL format.

## Features

- 📂 **Cross-platform**: Works on Windows, macOS, and Linux
- 📊 **Automatic column sizing**: Columns automatically adjust to content
- 🕐 **Time-based indexing**: Logs are automatically sorted by timestamp
- 🔄 **Sortable columns**: Click any column header to sort
- 🔍 **Search functionality**: Real-time search across all fields
- 🎨 **Color-coded levels**: Different colors for debug, info, warn, error, etc.
- 🚀 **Fast**: Efficiently handles large log files
- 💾 **Standalone executables**: Pre-built binaries available for all platforms

## Installation

### Using Pre-built Executables (Recommended)

Download the latest release for your platform from the [Releases](https://github.com/ashajkofci/zerolog_viewer/releases) page:

- **Windows**: `zerolog_viewer-windows-amd64.exe`
- **Linux**: `zerolog_viewer-linux-amd64`
- **macOS**: `zerolog_viewer-macos-amd64`

No installation required - just download and run!

### Running from Source

If you prefer to run from source:

```bash
# Clone the repository
git clone https://github.com/ashajkofci/zerolog_viewer.git
cd zerolog_viewer

# Install dependencies (optional, only needed for building)
pip install -r requirements.txt

# Run the application
python zerolog_viewer.py
```

## Usage

1. **Launch the application** by double-clicking the executable or running `python zerolog_viewer.py`
2. **Open a JSONL file** via the "Open File" button or File → Open JSONL File menu
3. **View your logs** with automatic column sizing and color-coding
4. **Sort** by clicking column headers
5. **Search** by typing in the search box - results update in real-time
6. **Adjust columns** by dragging column borders

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
# Install PyInstaller
pip install pyinstaller

# Build the executable
pyinstaller --onefile --windowed --name zerolog_viewer zerolog_viewer.py

# The executable will be in the dist/ folder
```

## Development

### Requirements

- Python 3.8 or higher
- tkinter (usually included with Python)

### Running Tests

```bash
# Test with the included sample file
python zerolog_viewer.py
# Then open sample_logs.jsonl
```

## Creating a Release

To create a new release with automated builds:

1. Update version in code if needed
2. Create and push a tag:
   ```bash
   git tag v1.0.0
   git push origin v1.0.0
   ```
3. GitHub Actions will automatically build executables for all platforms
4. Executables will be attached to the release

Alternatively, trigger a manual build via GitHub Actions workflow dispatch.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT License - feel free to use this project for any purpose.

## Support

If you encounter any issues or have questions, please open an issue on GitHub.