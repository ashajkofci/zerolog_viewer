# Release Workflow Documentation

## Overview

The release workflow has been updated to provide:

1. **Automatic version bumping** based on semantic versioning (patch/minor/major)
2. **DMG packaging for macOS** with proper app bundle structure
3. **DEB packaging for Linux** with desktop integration
4. **Windows executable** (existing functionality preserved)

## Version Management

The version is now stored in a `VERSION` file at the root of the repository. The current version is `0.2.0`.

### Semantic Versioning

- **Patch** (0.2.0 → 0.2.1): Bug fixes and minor updates
- **Minor** (0.2.0 → 0.3.0): New features, backwards compatible
- **Major** (0.2.0 → 1.0.0): Breaking changes

## How to Create a Release

### Method 1: Workflow Dispatch (Recommended)

1. Navigate to **Actions** tab in GitHub
2. Select **Build and Release** workflow
3. Click **Run workflow**
4. Select version bump type from dropdown:
   - `patch` - for bug fixes
   - `minor` - for new features
   - `major` - for breaking changes
5. Click **Run workflow**

The workflow will:
- Run all tests
- Bump the version number in VERSION file
- Commit and push the version change
- Create a new git tag (e.g., v0.3.0)
- Build packages for all platforms
- Create a GitHub release with all artifacts

### Method 2: Manual Tag Push

1. Manually update the `VERSION` file with the new version number
2. Commit the change:
   ```bash
   git add VERSION
   git commit -m "Bump version to X.Y.Z"
   ```
3. Create and push the tag:
   ```bash
   git tag vX.Y.Z
   git push origin main
   git push origin vX.Y.Z
   ```
4. The workflow will automatically build and release

## Build Artifacts

### Linux DEB Package

- **File**: `zerolog-viewer-X.X.X-amd64.deb`
- **Installation**: 
  ```bash
  sudo dpkg -i zerolog-viewer-X.X.X-amd64.deb
  ```
- **Features**:
  - Installs to `/usr/local/bin/zerolog_viewer`
  - Includes desktop entry for application menu
  - Proper package metadata

### macOS DMG

- **File**: `zerolog-viewer-X.X.X.dmg`
- **Installation**: 
  1. Double-click to mount the DMG
  2. Drag "ZeroLog Viewer.app" to Applications folder
- **Features**:
  - Proper macOS app bundle structure
  - Info.plist with version information
  - Easy drag-and-drop installation

### Windows Executable

- **File**: `zerolog_viewer-windows-amd64.exe`
- **Usage**: Download and run directly
- **Features**:
  - Self-contained executable
  - No installation required

## Workflow Structure

The workflow consists of the following jobs:

1. **test**: Runs unit tests and CLI tests
2. **version**: (Only for workflow_dispatch) Bumps version and creates tag
3. **build-windows**: Builds Windows executable
4. **build-linux**: Builds Linux executable and creates DEB package
5. **build-macos**: Builds macOS executable and creates DMG
6. **release**: Collects all artifacts and creates GitHub release

## Workflow Triggers

- **Push to tag** (v*): Automatically builds and releases for existing tags
- **Workflow dispatch**: Manual trigger with version bump selection
- **Pull request to main**: Runs tests only (no builds or releases)

## Dependencies

### Linux DEB Building
- `dpkg-deb`: Pre-installed on Ubuntu runners

### macOS DMG Building
- `create-dmg`: Installed via Homebrew in the workflow

### All Platforms
- Python 3.11
- PyInstaller
- Project dependencies (tkinterdnd2, pytest)

## Testing Locally

### Test Version Bumping
```bash
# Current version
cat VERSION

# Test bump logic
CURRENT_VERSION=$(cat VERSION)
IFS='.' read -r MAJOR MINOR PATCH <<< "$CURRENT_VERSION"
PATCH=$((PATCH + 1))
echo "${MAJOR}.${MINOR}.${PATCH}"
```

### Test DEB Creation
```bash
# Build executable
pyinstaller --onefile --windowed --name zerolog_viewer zerolog_viewer.py

# Create DEB structure
VERSION="0.2.0"
mkdir -p zerolog-viewer_${VERSION}_amd64/usr/local/bin
mkdir -p zerolog-viewer_${VERSION}_amd64/DEBIAN
cp dist/zerolog_viewer zerolog-viewer_${VERSION}_amd64/usr/local/bin/

# Create control file and build
# (See workflow for full commands)
dpkg-deb --build zerolog-viewer_${VERSION}_amd64
```

### Test DMG Creation (macOS only)
```bash
# Build executable
pyinstaller --onefile --windowed --name "ZeroLog Viewer" zerolog_viewer.py

# Create app bundle
# (See workflow for full commands)

# Create DMG
brew install create-dmg
create-dmg --volname "ZeroLog Viewer" "zerolog-viewer.dmg" "ZeroLog Viewer.app"
```

## Security

All changes have been validated with CodeQL security scanning. No security vulnerabilities were found.

## Rollback

If a release needs to be rolled back:

1. Delete the GitHub release
2. Delete the git tag:
   ```bash
   git tag -d vX.Y.Z
   git push origin :refs/tags/vX.Y.Z
   ```
3. Revert the VERSION file change if needed
