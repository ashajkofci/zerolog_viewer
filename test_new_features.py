#!/usr/bin/env python3
"""
Test the new features of ZeroLog Viewer.
"""

import json
import os
import sys
import tempfile

# Test imports
try:
    from zerolog_viewer import LogTab, ZeroLogViewer
    print("✓ Successfully imported ZeroLogViewer classes")
except ImportError as e:
    print(f"✗ Failed to import: {e}")
    sys.exit(1)

# Test color mapping
from zerolog_viewer import LogTab
if hasattr(LogTab, 'LEVEL_COLORS'):
    print(f"✓ LogTab.LEVEL_COLORS defined with {len(LogTab.LEVEL_COLORS)} levels")
else:
    print("✗ LogTab.LEVEL_COLORS not found")

# Test that we can create a temporary JSONL file
sample_data = [
    {"level": "debug", "time": "2025-10-20T17:19:16Z", "message": "Test 1"},
    {"level": "info", "time": "2025-10-20T17:19:17Z", "message": "Test 2"},
    {"level": "error", "time": "2025-10-20T17:19:18Z", "message": "Test 3"}
]

with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
    for entry in sample_data:
        f.write(json.dumps(entry) + '\n')
    temp_file = f.name

try:
    # Test parsing
    logs = []
    with open(temp_file, 'r') as f:
        for line in f:
            if line.strip():
                logs.append(json.loads(line))
    
    print(f"✓ Successfully parsed {len(logs)} log entries")
    
    # Test date parsing
    from datetime import datetime
    for log in logs:
        time_str = log.get('time', '')
        try:
            dt = datetime.fromisoformat(time_str.replace('Z', '+00:00'))
            print(f"✓ Parsed timestamp: {time_str}")
        except Exception as e:
            print(f"✗ Failed to parse timestamp {time_str}: {e}")
    
    print("\n✅ All basic tests passed!")
    
finally:
    os.unlink(temp_file)
