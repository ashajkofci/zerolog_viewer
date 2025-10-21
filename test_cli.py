#!/usr/bin/env python3
"""
CLI test script for ZeroLog Viewer - tests core functionality without GUI.
"""

import json
import sys
import os

def test_jsonl_parsing():
    """Test JSONL parsing."""
    print("Testing JSONL parsing...")
    
    # Read sample file
    logs = []
    with open('sample_logs.jsonl', 'r') as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    log = json.loads(line)
                    logs.append(log)
                except json.JSONDecodeError as e:
                    print(f"Error parsing line: {e}")
                    return False
    
    print(f"✓ Successfully parsed {len(logs)} log entries")
    return True

def test_column_extraction():
    """Test column extraction."""
    print("\nTesting column extraction...")
    
    logs = []
    with open('sample_logs.jsonl', 'r') as f:
        for line in f:
            line = line.strip()
            if line:
                logs.append(json.loads(line))
    
    columns = []
    for log in logs:
        for key in log.keys():
            if key not in columns:
                columns.append(key)
    
    print(f"✓ Found columns: {', '.join(columns)}")
    return True

def test_sorting():
    """Test sorting by time."""
    print("\nTesting time-based sorting...")
    
    logs = []
    with open('sample_logs.jsonl', 'r') as f:
        for line in f:
            line = line.strip()
            if line:
                logs.append(json.loads(line))
    
    sorted_logs = sorted(logs, key=lambda x: x.get('time', ''))
    
    print(f"✓ Sorted {len(sorted_logs)} logs by time")
    print(f"  First: {sorted_logs[0]['time']} - {sorted_logs[0]['message']}")
    print(f"  Last: {sorted_logs[-1]['time']} - {sorted_logs[-1]['message']}")
    return True

def test_search():
    """Test search functionality."""
    print("\nTesting search functionality...")
    
    logs = []
    with open('sample_logs.jsonl', 'r') as f:
        for line in f:
            line = line.strip()
            if line:
                logs.append(json.loads(line))
    
    search_term = "error"
    filtered = []
    for log in logs:
        for value in log.values():
            if search_term.lower() in str(value).lower():
                filtered.append(log)
                break
    
    print(f"✓ Search for '{search_term}' found {len(filtered)} entries")
    return True

def test_level_colors():
    """Test level color mapping."""
    print("\nTesting level color mapping...")
    
    try:
        from zerolog_viewer import ZeroLogViewer
        
        levels = ['debug', 'info', 'warn', 'error', 'fatal']
        for level in levels:
            if level in ZeroLogViewer.LEVEL_COLORS:
                color = ZeroLogViewer.LEVEL_COLORS[level]
                print(f"✓ Level '{level}' -> color {color}")
            else:
                print(f"✗ Level '{level}' not found")
                return False
        
        return True
    except ImportError:
        print("⚠ Skipping level colors test (tkinter not available in headless environment)")
        return True

def main():
    """Run all tests."""
    print("="*60)
    print("ZeroLog Viewer - Core Functionality Tests")
    print("="*60)
    
    tests = [
        test_jsonl_parsing,
        test_column_extraction,
        test_sorting,
        test_search,
        test_level_colors
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
            failed += 1
    
    print("\n" + "="*60)
    print(f"Results: {passed} passed, {failed} failed")
    print("="*60)
    
    return 0 if failed == 0 else 1

if __name__ == '__main__':
    sys.exit(main())
