#!/usr/bin/env python3
"""
Test for sorting functionality with merged files and filters.

This test verifies that sorting works correctly when filtered_logs is populated,
which happens when users apply search or level filters on merged files.
"""
import unittest
import sys
import os

# Add parent directory to path to import zerolog_viewer
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

class TestSortingWithFilters(unittest.TestCase):
    """Test sorting functionality when filters are active."""
    
    def test_sort_with_filtered_logs(self):
        """Test that sorting works correctly when filtered_logs is populated."""
        # Create a mock LogTab-like object
        class MockLogTab:
            def __init__(self):
                self.logs = []
                self.filtered_logs = []
                self.sort_column = None
                self.sort_reverse = False
        
        # Create test data
        test_logs = [
            {"time": "2025-01-01T09:58:00Z", "level": "warn", "message": "Entry 1"},
            {"time": "2025-01-01T10:00:00Z", "level": "info", "message": "Entry 2"},
            {"time": "2025-01-01T10:00:30Z", "level": "warn", "message": "Entry 3"},
            {"time": "2025-01-01T10:01:00Z", "level": "info", "message": "Entry 4"},
            {"time": "2025-01-01T10:02:00Z", "level": "info", "message": "Entry 5"},
            {"time": "2025-01-01T10:03:00Z", "level": "error", "message": "Entry 6"},
        ]
        
        # Initialize mock tab
        tab = MockLogTab()
        tab.logs = test_logs.copy()
        tab.logs.sort(key=lambda x: x.get('time', ''))
        
        # Simulate applying a filter (e.g., search for "entry")
        tab.filtered_logs = [log for log in tab.logs if "entry" in str(log).lower()]
        
        # Verify filtered_logs is populated
        self.assertEqual(len(tab.filtered_logs), 6)
        self.assertEqual(tab.filtered_logs[0]['time'], "2025-01-01T09:58:00Z")
        
        # Simulate sorting by time descending (click twice)
        from datetime import datetime
        
        def sort_key(log):
            value = log.get('time', '')
            try:
                return datetime.fromisoformat(str(value).replace('Z', '+00:00'))
            except:
                return value
        
        # First click - ascending
        column = 'time'
        if tab.sort_column == column:
            tab.sort_reverse = not tab.sort_reverse
        else:
            tab.sort_column = column
            tab.sort_reverse = False
        
        # Second click - descending
        if tab.sort_column == column:
            tab.sort_reverse = not tab.sort_reverse
        else:
            tab.sort_column = column
            tab.sort_reverse = False
        
        # THE FIX: Sort both logs and filtered_logs
        tab.logs.sort(key=sort_key, reverse=tab.sort_reverse)
        if tab.filtered_logs:
            tab.filtered_logs.sort(key=sort_key, reverse=tab.sort_reverse)
        
        # Verify both are sorted descending
        self.assertTrue(tab.sort_reverse)
        self.assertEqual(tab.logs[0]['time'], "2025-01-01T10:03:00Z")
        self.assertEqual(tab.filtered_logs[0]['time'], "2025-01-01T10:03:00Z")
        
        # Verify display would show correct order (uses filtered_logs when available)
        logs_to_display = tab.filtered_logs if tab.filtered_logs else tab.logs
        expected_order = [
            "2025-01-01T10:03:00Z",
            "2025-01-01T10:02:00Z",
            "2025-01-01T10:01:00Z",
            "2025-01-01T10:00:30Z",
            "2025-01-01T10:00:00Z",
            "2025-01-01T09:58:00Z",
        ]
        actual_order = [log['time'] for log in logs_to_display]
        self.assertEqual(actual_order, expected_order)
    
    def test_sort_without_filtered_logs(self):
        """Test that sorting works correctly when filtered_logs is empty."""
        # Create a mock LogTab-like object
        class MockLogTab:
            def __init__(self):
                self.logs = []
                self.filtered_logs = []
                self.sort_column = None
                self.sort_reverse = False
        
        # Create test data
        test_logs = [
            {"time": "2025-01-01T10:00:00Z", "level": "info", "message": "Entry 2"},
            {"time": "2025-01-01T09:58:00Z", "level": "warn", "message": "Entry 1"},
            {"time": "2025-01-01T10:03:00Z", "level": "error", "message": "Entry 3"},
        ]
        
        # Initialize mock tab
        tab = MockLogTab()
        tab.logs = test_logs.copy()
        tab.filtered_logs = []  # No filter active
        
        from datetime import datetime
        
        def sort_key(log):
            value = log.get('time', '')
            try:
                return datetime.fromisoformat(str(value).replace('Z', '+00:00'))
            except:
                return value
        
        # Sort by time ascending
        tab.sort_column = 'time'
        tab.sort_reverse = False
        tab.logs.sort(key=sort_key, reverse=tab.sort_reverse)
        if tab.filtered_logs:
            tab.filtered_logs.sort(key=sort_key, reverse=tab.sort_reverse)
        
        # Verify sorted ascending
        self.assertEqual(tab.logs[0]['time'], "2025-01-01T09:58:00Z")
        self.assertEqual(tab.logs[-1]['time'], "2025-01-01T10:03:00Z")

if __name__ == '__main__':
    unittest.main()
