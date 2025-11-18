#!/usr/bin/env python3
"""
Demonstration of Session Persistence Feature

This script demonstrates the session persistence functionality by:
1. Creating sample log files
2. Simulating opening files in the app
3. Saving the session
4. Simulating closing and reopening the app
5. Restoring the session
"""

import json
import os
import tempfile
from pathlib import Path

def demo_session_persistence():
    """Demonstrate session persistence functionality."""
    
    # Create temporary directory
    temp_dir = tempfile.mkdtemp()
    config_dir = Path(temp_dir) / "config"
    config_dir.mkdir(parents=True, exist_ok=True)
    
    print("=" * 60)
    print("Session Persistence Demonstration")
    print("=" * 60)
    
    # Step 1: Create sample files
    print("\n1. Creating sample log files...")
    file1 = config_dir / "logs1.jsonl"
    file2 = config_dir / "logs2.jsonl"
    file3 = config_dir / "logs3.jsonl"
    
    with open(file1, 'w') as f:
        f.write('{"level":"info","time":"2025-10-20T17:19:16Z","message":"Log from file 1"}\n')
    
    with open(file2, 'w') as f:
        f.write('{"level":"warn","time":"2025-10-20T17:19:17Z","message":"Log from file 2"}\n')
    
    with open(file3, 'w') as f:
        f.write('{"level":"error","time":"2025-10-20T17:19:18Z","message":"Log from file 3"}\n')
    
    print(f"   ✓ Created {file1.name}")
    print(f"   ✓ Created {file2.name}")
    print(f"   ✓ Created {file3.name}")
    
    # Step 2: Simulate opening files in the app
    print("\n2. Simulating user opening files in the app...")
    session = {
        "tabs": [
            {
                "type": "single",
                "file": str(file1)
            },
            {
                "type": "merged",
                "files": [str(file2), str(file3)]
            }
        ]
    }
    
    print(f"   ✓ Opened single file: {file1.name}")
    print(f"   ✓ Merged files: {file2.name} + {file3.name}")
    
    # Step 3: Save session
    print("\n3. Saving session to disk...")
    session_file = config_dir / "session.json"
    with open(session_file, 'w') as f:
        json.dump(session, f, indent=2)
    print(f"   ✓ Session saved to: {session_file}")
    
    # Display session contents
    print("\n   Session contents:")
    print("   " + "-" * 50)
    with open(session_file, 'r') as f:
        content = f.read()
        for line in content.split('\n'):
            print(f"   {line}")
    print("   " + "-" * 50)
    
    # Step 4: Simulate closing the app
    print("\n4. Simulating app close...")
    print("   ✓ Session automatically saved")
    
    # Step 5: Simulate reopening the app
    print("\n5. Simulating app reopen and session restore...")
    with open(session_file, 'r') as f:
        restored_session = json.load(f)
    
    print("   ✓ Session loaded from disk")
    print("\n   Restored tabs:")
    for i, tab in enumerate(restored_session["tabs"], 1):
        if tab["type"] == "single":
            print(f"   Tab {i}: Single file - {Path(tab['file']).name}")
        elif tab["type"] == "merged":
            files = [Path(f).name for f in tab["files"]]
            print(f"   Tab {i}: Merged files - {' + '.join(files)}")
    
    # Step 6: Test missing file handling
    print("\n6. Testing graceful handling of missing files...")
    os.remove(file3)
    print(f"   ✗ Deleted {file3.name}")
    
    print("\n   Restoring session with missing file...")
    existing_files = []
    for tab in restored_session["tabs"]:
        if tab["type"] == "single":
            if os.path.isfile(tab["file"]):
                existing_files.append(Path(tab["file"]).name)
                print(f"   ✓ Restored: {Path(tab['file']).name}")
        elif tab["type"] == "merged":
            existing = [f for f in tab["files"] if os.path.isfile(f)]
            if existing:
                names = [Path(f).name for f in existing]
                print(f"   ✓ Restored merged tab (partial): {' + '.join(names)}")
                print(f"     (Silently skipped missing: {file3.name})")
    
    # Step 7: Summary
    print("\n" + "=" * 60)
    print("Summary:")
    print("=" * 60)
    print("✓ Session is automatically saved when:")
    print("  - Files are opened")
    print("  - Files are merged")
    print("  - Tabs are closed")
    print("  - Application is closed")
    print()
    print("✓ Session is automatically restored when:")
    print("  - Application starts (100ms after UI loads)")
    print()
    print("✓ Missing files are handled gracefully:")
    print("  - No error messages shown")
    print("  - Files that exist are loaded")
    print("  - Files that don't exist are silently skipped")
    print("=" * 60)
    
    # Cleanup
    import shutil
    shutil.rmtree(temp_dir)
    print("\n✓ Cleanup complete")

if __name__ == "__main__":
    demo_session_persistence()
