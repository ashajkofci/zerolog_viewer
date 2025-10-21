# Quick Start: Creating a Release

## For Maintainers

This guide shows you how to create a new release using the automated workflow.

## Option 1: Workflow Dispatch (Recommended) ⭐

### Step-by-Step Instructions

1. **Navigate to GitHub Actions**
   - Go to your repository on GitHub
   - Click the **Actions** tab at the top

2. **Select the Workflow**
   - From the left sidebar, click **Build and Release**

3. **Run the Workflow**
   - Click the **Run workflow** button (top right)
   - A dropdown will appear

4. **Choose Version Bump Type**
   - Select from the dropdown:
     - **patch** → Bug fixes (0.2.0 → 0.2.1)
     - **minor** → New features (0.2.0 → 0.3.0)
     - **major** → Breaking changes (0.2.0 → 1.0.0)

5. **Click "Run workflow"**
   - The workflow will start automatically

### What Happens Next?

The workflow will:
1. ✅ Run all tests
2. ✅ Bump version number
3. ✅ Commit and push VERSION file
4. ✅ Create and push git tag
5. ✅ Build Linux DEB package
6. ✅ Build macOS DMG
7. ✅ Build Windows EXE
8. ✅ Create GitHub release with all files

**Total time:** ~10-15 minutes

### Check Progress

- Watch the workflow run in the Actions tab
- Green checkmarks ✓ = success
- Red X = failure (check logs)

### After Completion

Your release will be available at:
`https://github.com/YOUR_USERNAME/zerolog_viewer/releases`

Users can download:
- `zerolog-viewer-X.X.X-amd64.deb` (Linux)
- `zerolog-viewer-X.X.X.dmg` (macOS)
- `zerolog_viewer-windows-amd64.exe` (Windows)

## Option 2: Manual Tag Push

If you prefer manual control:

```bash
# 1. Update VERSION file
echo "0.3.0" > VERSION

# 2. Commit the change
git add VERSION
git commit -m "Bump version to 0.3.0"

# 3. Create and push tag
git tag v0.3.0
git push origin main
git push origin v0.3.0
```

The workflow will automatically build and release.

## Common Scenarios

### Scenario: Bug Fix Release
- Current version: 0.2.0
- Action: Select **patch**
- New version: 0.2.1
- Use case: Security patches, bug fixes

### Scenario: New Feature Release
- Current version: 0.2.0
- Action: Select **minor**
- New version: 0.3.0
- Use case: New features, improvements

### Scenario: Major Update
- Current version: 0.2.0
- Action: Select **major**
- New version: 1.0.0
- Use case: Breaking changes, complete rewrite

## Troubleshooting

### Workflow Failed?
1. Check the Actions tab for error logs
2. Look at the specific job that failed
3. Common issues:
   - Tests failed → Fix tests first
   - Build failed → Check dependencies
   - Permission denied → Check repository settings

### Need to Cancel?
- Go to Actions tab
- Click on the running workflow
- Click "Cancel workflow"

### Made a Mistake?
Delete the release and tag:
```bash
# Delete tag locally and remotely
git tag -d vX.Y.Z
git push origin :refs/tags/vX.Y.Z

# Delete release on GitHub
# Go to Releases → Click on the release → Delete
```

## Best Practices

1. **Test First**: Ensure all tests pass locally
2. **Review Changes**: Review all commits since last release
3. **Update Docs**: Update README if needed
4. **Choose Wisely**: Select appropriate version bump
5. **Monitor Build**: Watch the workflow complete
6. **Test Release**: Download and test at least one package

## Version History

You can always check the current version:
```bash
cat VERSION
```

Or check all releases:
```bash
git tag
```

## Questions?

See `RELEASE_WORKFLOW.md` for detailed documentation.
