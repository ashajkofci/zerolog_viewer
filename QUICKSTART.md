# Quick Start Guide

## 🚀 Get Started in 30 Seconds

### Option 1: Run from Source (Fastest for Testing)

```bash
# No installation needed! Just run it:
python zerolog_viewer.py

# Then click "Open File" and select sample_logs.jsonl
```

### Option 2: Build Executable

```bash
# Install PyInstaller
pip install -r requirements.txt

# Build executable
pyinstaller --onefile --windowed --name zerolog_viewer zerolog_viewer.py

# Run the executable
./dist/zerolog_viewer  # Linux/Mac
# or
dist\zerolog_viewer.exe  # Windows
```

### Option 3: Download Pre-built Release

Once you create a release, executables will be available at:
https://github.com/ashajkofci/zerolog_viewer/releases

---

## 📦 Creating Your First Release

```bash
# Make sure everything is committed
git add .
git commit -m "Ready for v1.0.0"

# Create and push a version tag
git tag v1.0.0
git push origin v1.0.0

# Wait ~5-10 minutes for GitHub Actions to build
# Executables will appear at: 
# https://github.com/ashajkofci/zerolog_viewer/releases/tag/v1.0.0
```

---

## 🎯 Try It Now

```bash
# Run the app
python zerolog_viewer.py

# It will open a window. Click "Open File"
# Navigate to and open: sample_logs.jsonl
# You should see 6 colored log entries!
```

### What to Try:

1. **Sort**: Click the "level" column header → logs sort by level
2. **Search**: Type "error" in search box → only error logs show
3. **Resize**: Drag column borders to adjust width
4. **Clear**: Click "Clear" to show all logs again

---

## 🎨 Understanding the Colors

When you open sample_logs.jsonl, you'll see:

- 🔷 Gray = debug logs
- 🔵 Blue = info logs  
- 🟠 Orange = warning logs
- 🔴 Red = error logs

---

## 📝 Using Your Own Logs

Your JSONL file should have one JSON object per line:

```json
{"level":"info","time":"2025-10-20T17:19:16Z","message":"Hello"}
{"level":"error","time":"2025-10-20T17:19:17Z","message":"Oops"}
```

The viewer will automatically:
- Create columns for all fields in your JSON
- Sort by time
- Color by level
- Size columns to fit content

---

## ❓ Troubleshooting

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

---

## 🎓 Learn More

- **Full Documentation**: See README.md
- **Features**: See FEATURES.md
- **Implementation Details**: See IMPLEMENTATION.md

---

## 🎉 That's It!

You now have a working JSONL log viewer. Enjoy! 🎊
