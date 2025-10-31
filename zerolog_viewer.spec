# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for ZeroLog Viewer
This ensures VERSION and LICENSE files are bundled with the executable.
"""

import sys
import os

block_cipher = None

# Get the script directory - use SPECPATH which is available in spec files
script_dir = os.path.abspath(SPECPATH)

# Define data files to bundle
datas = [
    (os.path.join(script_dir, 'VERSION'), '.'),
    (os.path.join(script_dir, 'LICENSE'), '.'),
]

a = Analysis(
    ['zerolog_viewer.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='zerolog_viewer',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

# For macOS, create an app bundle
if sys.platform == 'darwin':
    app = BUNDLE(
        exe,
        name='ZeroLog Viewer.app',
        icon=None,
        bundle_identifier='com.zerolog.viewer',
    )
