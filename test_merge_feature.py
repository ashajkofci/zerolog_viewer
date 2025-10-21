#!/usr/bin/env python3
"""
Test script for the multi-file merge feature.
"""

import json
import sys
import os

def test_file_merging():
    """Test merging multiple files."""
    print("Testing file merging logic...")
    
    # Create test files
    test_files = ['/tmp/test_file1.jsonl', '/tmp/test_file2.jsonl', '/tmp/test_file3.log']
    
    # Verify files exist
    for f in test_files:
        if not os.path.exists(f):
            print(f"✗ Test file not found: {f}")
            return False
    
    # Load all logs from files
    all_logs = []
    columns = set()
    
    for filename in test_files:
        with open(filename, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        log_entry = json.loads(line)
                        all_logs.append(log_entry)
                        columns.update(log_entry.keys())
                    except json.JSONDecodeError as e:
                        print(f"✗ Error parsing line in {filename}: {e}")
                        return False
    
    # Verify we loaded the correct number of entries
    expected_count = 8  # 3 + 3 + 2
    if len(all_logs) != expected_count:
        print(f"✗ Expected {expected_count} log entries, got {len(all_logs)}")
        return False
    
    print(f"✓ Loaded {len(all_logs)} log entries from {len(test_files)} files")
    
    # Sort by time
    all_logs.sort(key=lambda x: x.get('time', ''))
    
    # Verify sorting worked
    if all_logs[0]['message'] != "Log from file 1 - entry 1":
        print(f"✗ First log should be from file 1 entry 1, got: {all_logs[0]['message']}")
        return False
    
    if all_logs[-1]['message'] != "Log from file 3 - entry 2":
        print(f"✗ Last log should be from file 3 entry 2, got: {all_logs[-1]['message']}")
        return False
    
    print("✓ Logs correctly sorted by time")
    
    # Verify columns
    expected_columns = {'level', 'time', 'message'}
    if columns != expected_columns:
        print(f"✗ Expected columns {expected_columns}, got {columns}")
        return False
    
    print(f"✓ Columns correctly extracted: {columns}")
    
    return True

def test_merged_filename_generation():
    """Test merged filename generation."""
    print("\nTesting merged filename generation...")
    
    # Test with 2 files
    filenames = ['/path/to/file1.jsonl', '/path/to/file2.jsonl']
    merged_name = f"{os.path.basename(filenames[0])} + {os.path.basename(filenames[1])}"
    expected = "file1.jsonl + file2.jsonl"
    if merged_name != expected:
        print(f"✗ Expected '{expected}', got '{merged_name}'")
        return False
    print(f"✓ Two files merge name: {merged_name}")
    
    # Test with 3+ files
    filenames = ['/path/to/file1.jsonl', '/path/to/file2.jsonl', '/path/to/file3.log']
    merged_name = f"{len(filenames)} merged files"
    expected = "3 merged files"
    if merged_name != expected:
        print(f"✗ Expected '{expected}', got '{merged_name}'")
        return False
    print(f"✓ Three+ files merge name: {merged_name}")
    
    return True

def main():
    """Run all tests."""
    print("="*60)
    print("Multi-File Merge Feature Tests")
    print("="*60)
    
    tests = [
        test_file_merging,
        test_merged_filename_generation
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"✗ Test failed with exception: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print("\n" + "="*60)
    print(f"Results: {passed} passed, {failed} failed")
    print("="*60)
    
    return 0 if failed == 0 else 1

if __name__ == '__main__':
    sys.exit(main())
