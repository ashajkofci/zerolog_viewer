# Release Workflow Diagram

## Workflow Dispatch Flow

```
User triggers workflow
    ↓
Selects version bump type (patch/minor/major)
    ↓
┌─────────────────────────┐
│   Run Tests             │
│   - Unit tests          │
│   - CLI tests           │
└───────────┬─────────────┘
            ↓
┌─────────────────────────┐
│   Bump Version          │
│   - Read VERSION file   │
│   - Calculate new ver   │
│   - Update VERSION      │
│   - Commit & push       │
│   - Create & push tag   │
└───────────┬─────────────┘
            ↓
    ┌───────┴───────┐
    ↓               ↓               ↓
┌────────────┐  ┌────────────┐  ┌────────────┐
│Build Linux │  │Build macOS │  │Build Win   │
│- PyInstaller│ │- PyInstaller│ │- PyInstaller│
│- Create DEB│  │- Create DMG│  │- EXE only  │
└─────┬──────┘  └─────┬──────┘  └─────┬──────┘
      ↓               ↓               ↓
      └───────────────┼───────────────┘
                      ↓
          ┌───────────────────┐
          │  Create Release   │
          │  - Collect all    │
          │    artifacts      │
          │  - Create release │
          │  - Upload files   │
          └───────────────────┘
```

## Tag Push Flow

```
Developer creates tag (e.g., v0.3.0)
    ↓
Pushes tag to GitHub
    ↓
┌─────────────────────────┐
│   Run Tests             │
│   - Unit tests          │
│   - CLI tests           │
└───────────┬─────────────┘
            ↓
    ┌───────┴───────┐
    ↓               ↓               ↓
┌────────────┐  ┌────────────┐  ┌────────────┐
│Build Linux │  │Build macOS │  │Build Win   │
│- PyInstaller│ │- PyInstaller│ │- PyInstaller│
│- Create DEB│  │- Create DMG│  │- EXE only  │
└─────┬──────┘  └─────┬──────┘  └─────┬──────┘
      ↓               ↓               ↓
      └───────────────┼───────────────┘
                      ↓
          ┌───────────────────┐
          │  Create Release   │
          │  - Collect all    │
          │    artifacts      │
          │  - Create release │
          │  - Upload files   │
          └───────────────────┘
```

## Version Bumping Logic

```
Current Version: X.Y.Z

Patch:  X.Y.Z → X.Y.(Z+1)
        0.2.0 → 0.2.1
        - Bug fixes
        - Minor updates

Minor:  X.Y.Z → X.(Y+1).0
        0.2.0 → 0.3.0
        - New features
        - Backwards compatible

Major:  X.Y.Z → (X+1).0.0
        0.2.0 → 1.0.0
        - Breaking changes
        - Major features
```

## Package Outputs

### Linux DEB Package
```
zerolog-viewer-X.X.X-amd64.deb
├── /usr/local/bin/
│   └── zerolog_viewer (executable)
├── /usr/share/applications/
│   └── zerolog-viewer.desktop
└── DEBIAN/
    └── control (package metadata)
```

### macOS DMG
```
zerolog-viewer-X.X.X.dmg
└── ZeroLog Viewer.app/
    └── Contents/
        ├── MacOS/
        │   └── ZeroLog Viewer (executable)
        ├── Resources/
        └── Info.plist (bundle metadata)
```

### Windows EXE
```
zerolog_viewer-windows-amd64.exe
└── Standalone executable
```

## Artifact Flow

```
Build Jobs Complete
    ↓
Upload to GitHub Actions Artifacts
    ↓
artifacts/
├── zerolog_viewer-windows-amd64.exe/
│   └── zerolog_viewer-windows-amd64.exe
├── zerolog-viewer-X.X.X-amd64.deb/
│   └── zerolog-viewer-X.X.X-amd64.deb
└── zerolog-viewer-X.X.X.dmg/
    └── zerolog-viewer-X.X.X.dmg
    ↓
Release Job Downloads All Artifacts
    ↓
Creates GitHub Release with all files
    ↓
Users can download from GitHub Releases page
```

## Key Benefits

1. **Automated Versioning**: No manual version management needed
2. **Consistent Releases**: All platforms built from same commit
3. **Easy Distribution**: Native package formats for each platform
4. **Professional Packaging**: Desktop integration, metadata, installers
5. **Semantic Versioning**: Clear version progression
6. **Single Command**: One click to create a release
