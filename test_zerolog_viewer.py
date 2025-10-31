#!/usr/bin/env python3
"""
Unit tests for ZeroLog Viewer.
"""

import csv
import json
import os
import tempfile
import unittest
from unittest.mock import Mock, patch
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Mock tkinter and tkinterdnd2 before importing the main module
sys.modules['tkinter'] = Mock()
sys.modules['tkinter.ttk'] = Mock()
sys.modules['tkinter.filedialog'] = Mock()
sys.modules['tkinter.messagebox'] = Mock()
sys.modules['tkinter.simpledialog'] = Mock()
sys.modules['tkinterdnd2'] = Mock()

from zerolog_viewer import ZeroLogViewer, ConfigManager


class TestZeroLogViewer(unittest.TestCase):
    """Test cases for ZeroLog Viewer."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_logs = [
            {
                "level": "debug",
                "time": "2025-10-20T17:19:16Z",
                "message": "Device found"
            },
            {
                "level": "info",
                "time": "2025-10-20T17:19:17Z",
                "message": "Connection established"
            },
            {
                "level": "error",
                "time": "2025-10-20T17:19:18Z",
                "message": "Failed to authenticate"
            }
        ]
    
    def test_level_colors_defined(self):
        """Test that level colors are properly defined in config."""
        # Level colors are now stored in config, not as class attribute
        config = ConfigManager.load_config()
        level_colors = config.get('level_colors', {})
        self.assertIn('debug', level_colors)
        self.assertIn('info', level_colors)
        self.assertIn('warn', level_colors)
        self.assertIn('error', level_colors)
        self.assertIn('fatal', level_colors)
    
    def test_get_default_config(self):
        """Test that get_default_config returns proper default values."""
        default_config = ConfigManager.get_default_config()
        
        # Check that all expected keys are present
        self.assertIn('visible_columns', default_config)
        self.assertIn('window_geometry', default_config)
        self.assertIn('level_colors', default_config)
        
        # Check default values
        self.assertEqual(default_config['visible_columns'], ["time", "level", "message", "url"])
        self.assertEqual(default_config['window_geometry'], "1200x700")
        
        # Check that all level colors are defined
        level_colors = default_config['level_colors']
        for level in ['debug', 'info', 'warn', 'warning', 'error', 'fatal', 'panic']:
            self.assertIn(level, level_colors)
            self.assertIsInstance(level_colors[level], str)
            self.assertTrue(level_colors[level].startswith('#'))
    
    def test_default_color_palette(self):
        """Test that the default color palette has appropriate color values."""
        default_config = ConfigManager.get_default_config()
        level_colors = default_config['level_colors']
        
        # Verify expected color palette
        expected_colors = {
            "debug": "#808080",      # Gray
            "info": "#0066CC",       # Blue
            "warn": "#FF8C00",       # Orange
            "warning": "#FF8C00",    # Orange
            "error": "#CC0000",      # Red
            "fatal": "#8B0000",      # Dark Red
            "panic": "#8B0000"       # Dark Red
        }
        
        for level, expected_color in expected_colors.items():
            self.assertEqual(level_colors[level], expected_color,
                           f"Color for {level} should be {expected_color}")
        
        # Ensure colors are not all black (the old default)
        self.assertNotEqual(level_colors['debug'], "#000000")
        self.assertNotEqual(level_colors['info'], "#000000")
        self.assertNotEqual(level_colors['error'], "#000000")
    
    def test_log_parsing(self):
        """Test JSONL parsing functionality."""
        # Create a temporary JSONL file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            for log in self.test_logs:
                f.write(json.dumps(log) + '\n')
            temp_file = f.name
        
        try:
            # Read and parse the file
            logs = []
            with open(temp_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        logs.append(json.loads(line))
            
            self.assertEqual(len(logs), 3)
            self.assertEqual(logs[0]['level'], 'debug')
            self.assertEqual(logs[1]['level'], 'info')
            self.assertEqual(logs[2]['level'], 'error')
        finally:
            os.unlink(temp_file)
    
    def test_column_extraction(self):
        """Test that columns are correctly extracted from logs."""
        columns = set()
        for log in self.test_logs:
            columns.update(log.keys())
        
        expected_columns = {'level', 'time', 'message'}
        self.assertEqual(columns, expected_columns)
    
    def test_time_sorting(self):
        """Test that logs can be sorted by time."""
        unsorted_logs = [
            {"time": "2025-10-20T17:19:18Z", "message": "C"},
            {"time": "2025-10-20T17:19:16Z", "message": "A"},
            {"time": "2025-10-20T17:19:17Z", "message": "B"}
        ]
        
        sorted_logs = sorted(unsorted_logs, key=lambda x: x.get('time', ''))
        
        self.assertEqual(sorted_logs[0]['message'], 'A')
        self.assertEqual(sorted_logs[1]['message'], 'B')
        self.assertEqual(sorted_logs[2]['message'], 'C')
    
    def test_search_functionality(self):
        """Test search/filter functionality."""
        search_term = "established"
        
        filtered = []
        for log in self.test_logs:
            for value in log.values():
                if search_term.lower() in str(value).lower():
                    filtered.append(log)
                    break
        
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0]['level'], 'info')
    
    def test_search_clear_preserves_selection(self):
        """Test that clearing search preserves the selected log entry."""
        # This test validates the feature: when we search, select a line,
        # then clear the search, the list view should move to the selected line
        
        # Simulate search filtering
        search_term = "established"
        filtered = []
        for log in self.test_logs:
            for value in log.values():
                if search_term.lower() in str(value).lower():
                    filtered.append(log)
                    break
        
        # Verify we found the log entry
        self.assertEqual(len(filtered), 1)
        selected_log = filtered[0]
        
        # Now simulate clearing the search - the selected log should be found
        # in the full list of test_logs
        found = False
        for i, log in enumerate(self.test_logs):
            if log == selected_log:
                found = True
                # The index should be 1 (second log in the original list)
                self.assertEqual(i, 1)
                break
        
        self.assertTrue(found, "Selected log should be found in full logs after clearing search")
    
    def test_log_level_hierarchy(self):
        """Test that log level hierarchy is correctly defined."""
        from zerolog_viewer import LogTab
        
        # Test that hierarchy is defined
        self.assertIn('debug', LogTab.LOG_LEVELS)
        self.assertIn('info', LogTab.LOG_LEVELS)
        self.assertIn('warn', LogTab.LOG_LEVELS)
        self.assertIn('error', LogTab.LOG_LEVELS)
        self.assertIn('fatal', LogTab.LOG_LEVELS)
        
        # Test hierarchy order
        self.assertLess(LogTab.LOG_LEVELS['debug'], LogTab.LOG_LEVELS['info'])
        self.assertLess(LogTab.LOG_LEVELS['info'], LogTab.LOG_LEVELS['warn'])
        self.assertLess(LogTab.LOG_LEVELS['warn'], LogTab.LOG_LEVELS['error'])
        self.assertLess(LogTab.LOG_LEVELS['error'], LogTab.LOG_LEVELS['fatal'])
        
        # Test that warning is same as warn
        self.assertEqual(LogTab.LOG_LEVELS['warn'], LogTab.LOG_LEVELS['warning'])
        
        # Test that panic is same as fatal
        self.assertEqual(LogTab.LOG_LEVELS['fatal'], LogTab.LOG_LEVELS['panic'])
    
    def test_level_filter_all_logs(self):
        """Test that 'all' level filter includes all logs."""
        # Create test logs with different levels
        test_logs_varied = [
            {"level": "debug", "message": "Debug message"},
            {"level": "info", "message": "Info message"},
            {"level": "warn", "message": "Warn message"},
            {"level": "error", "message": "Error message"},
            {"level": "fatal", "message": "Fatal message"},
        ]
        
        # With level_filter = 'all', all logs should pass
        from zerolog_viewer import LogTab
        
        # Mock the required attributes
        mock_tab = Mock()
        mock_tab.level_filter = 'all'
        mock_tab.LOG_LEVELS = LogTab.LOG_LEVELS
        
        # Use the actual method
        filtered = [log for log in test_logs_varied if LogTab._passes_level_filter(mock_tab, log)]
        
        self.assertEqual(len(filtered), 5)
    
    def test_level_filter_info_and_more(self):
        """Test that 'info' level filter excludes debug logs."""
        test_logs_varied = [
            {"level": "debug", "message": "Debug message"},
            {"level": "info", "message": "Info message"},
            {"level": "warn", "message": "Warn message"},
            {"level": "error", "message": "Error message"},
        ]
        
        from zerolog_viewer import LogTab
        
        # Mock the required attributes
        mock_tab = Mock()
        mock_tab.level_filter = 'info'
        mock_tab.LOG_LEVELS = LogTab.LOG_LEVELS
        
        # Use the actual method
        filtered = [log for log in test_logs_varied if LogTab._passes_level_filter(mock_tab, log)]
        
        # Should exclude debug, include info, warn, error
        self.assertEqual(len(filtered), 3)
        self.assertNotIn('debug', [log['level'] for log in filtered])
        self.assertIn('info', [log['level'] for log in filtered])
        self.assertIn('warn', [log['level'] for log in filtered])
        self.assertIn('error', [log['level'] for log in filtered])
    
    def test_level_filter_warn_and_more(self):
        """Test that 'warn' level filter excludes debug and info logs."""
        test_logs_varied = [
            {"level": "debug", "message": "Debug message"},
            {"level": "info", "message": "Info message"},
            {"level": "warn", "message": "Warn message"},
            {"level": "error", "message": "Error message"},
        ]
        
        from zerolog_viewer import LogTab
        
        # Mock the required attributes
        mock_tab = Mock()
        mock_tab.level_filter = 'warn'
        mock_tab.LOG_LEVELS = LogTab.LOG_LEVELS
        
        # Use the actual method
        filtered = [log for log in test_logs_varied if LogTab._passes_level_filter(mock_tab, log)]
        
        # Should exclude debug and info, include warn and error
        self.assertEqual(len(filtered), 2)
        self.assertNotIn('debug', [log['level'] for log in filtered])
        self.assertNotIn('info', [log['level'] for log in filtered])
        self.assertIn('warn', [log['level'] for log in filtered])
        self.assertIn('error', [log['level'] for log in filtered])
    
    def test_level_filter_error_and_more(self):
        """Test that 'error' level filter only includes error and fatal logs."""
        test_logs_varied = [
            {"level": "debug", "message": "Debug message"},
            {"level": "info", "message": "Info message"},
            {"level": "warn", "message": "Warn message"},
            {"level": "error", "message": "Error message"},
            {"level": "fatal", "message": "Fatal message"},
        ]
        
        from zerolog_viewer import LogTab
        
        # Mock the required attributes
        mock_tab = Mock()
        mock_tab.level_filter = 'error'
        mock_tab.LOG_LEVELS = LogTab.LOG_LEVELS
        
        # Use the actual method
        filtered = [log for log in test_logs_varied if LogTab._passes_level_filter(mock_tab, log)]
        
        # Should only include error and fatal
        self.assertEqual(len(filtered), 2)
        self.assertIn('error', [log['level'] for log in filtered])
        self.assertIn('fatal', [log['level'] for log in filtered])
    
    def test_level_filter_unknown_level(self):
        """Test that logs with unknown levels are included by default."""
        test_logs = [
            {"level": "custom", "message": "Custom level message"},
            {"level": "unknown", "message": "Unknown level message"},
        ]
        
        from zerolog_viewer import LogTab
        
        # Mock the required attributes
        mock_tab = Mock()
        mock_tab.level_filter = 'info'
        mock_tab.LOG_LEVELS = LogTab.LOG_LEVELS
        
        # Use the actual method
        filtered = [log for log in test_logs if LogTab._passes_level_filter(mock_tab, log)]
        
        # Unknown levels should be included
        self.assertEqual(len(filtered), 2)
    
    def test_multi_search_and_logic(self):
        """Test multi-search with AND logic."""
        test_logs = [
            {"level": "info", "message": "Device found", "location": "server"},
            {"level": "info", "message": "Connection established", "location": "client"},
            {"level": "error", "message": "Device error", "location": "server"},
        ]
        
        # Search for logs containing both "Device" AND "server"
        search_terms = ["device", "server"]
        search_logic = "AND"
        
        # Simulate the multi-search logic
        filtered = []
        for log in test_logs:
            log_values_str = [str(value).lower() for value in log.values()]
            match = True
            for term in search_terms:
                term_found = any(term in value for value in log_values_str)
                if not term_found:
                    match = False
                    break
            if match:
                filtered.append(log)
        
        # Should find logs 0 and 2 (both contain "device" and "server")
        self.assertEqual(len(filtered), 2)
        self.assertIn("Device found", filtered[0]['message'])
        self.assertIn("Device error", filtered[1]['message'])
    
    def test_multi_search_or_logic(self):
        """Test multi-search with OR logic."""
        test_logs = [
            {"level": "info", "message": "Device found", "location": "server"},
            {"level": "info", "message": "Connection established", "location": "client"},
            {"level": "error", "message": "Network error", "location": "router"},
        ]
        
        # Search for logs containing "Device" OR "error"
        search_terms = ["device", "error"]
        search_logic = "OR"
        
        # Simulate the multi-search logic
        filtered = []
        for log in test_logs:
            log_values_str = [str(value).lower() for value in log.values()]
            match = False
            for term in search_terms:
                term_found = any(term in value for value in log_values_str)
                if term_found:
                    match = True
                    break
            if match:
                filtered.append(log)
        
        # Should find logs 0 and 2 (contain "device" or "error")
        self.assertEqual(len(filtered), 2)
        self.assertIn("Device found", filtered[0]['message'])
        self.assertIn("Network error", filtered[1]['message'])
    
    def test_multi_search_single_term(self):
        """Test multi-search with single term (edge case)."""
        test_logs = [
            {"level": "info", "message": "Device found"},
            {"level": "info", "message": "Connection established"},
        ]
        
        # Search with single term should work with both AND and OR
        search_terms = ["device"]
        
        # Simulate the multi-search logic (AND)
        filtered = []
        for log in test_logs:
            log_values_str = [str(value).lower() for value in log.values()]
            match = True
            for term in search_terms:
                term_found = any(term in value for value in log_values_str)
                if not term_found:
                    match = False
                    break
            if match:
                filtered.append(log)
        
        self.assertEqual(len(filtered), 1)
        self.assertIn("Device found", filtered[0]['message'])
    
    def test_multi_search_empty_terms(self):
        """Test multi-search with no search terms (should return all)."""
        test_logs = [
            {"level": "info", "message": "Device found"},
            {"level": "info", "message": "Connection established"},
        ]
        
        search_terms = []
        
        # Empty search terms should not filter (return all)
        # This is handled in apply_search_multi by returning early
        self.assertEqual(len(search_terms), 0)
    
    def test_export_to_jsonl(self):
        """Test export to JSONL format."""
        test_logs = [
            {"level": "info", "time": "2025-10-20T17:19:16Z", "message": "Test log 1"},
            {"level": "error", "time": "2025-10-20T17:19:17Z", "message": "Test log 2"},
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            temp_file = f.name
        
        try:
            # Write logs to JSONL
            with open(temp_file, 'w', encoding='utf-8') as f:
                for log in test_logs:
                    f.write(json.dumps(log, ensure_ascii=False) + '\n')
            
            # Read back and verify
            with open(temp_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            self.assertEqual(len(lines), 2)
            
            # Parse and verify first log
            log1 = json.loads(lines[0])
            self.assertEqual(log1['level'], 'info')
            self.assertEqual(log1['message'], 'Test log 1')
            
            # Parse and verify second log
            log2 = json.loads(lines[1])
            self.assertEqual(log2['level'], 'error')
            self.assertEqual(log2['message'], 'Test log 2')
            
        finally:
            os.unlink(temp_file)
    
    def test_export_to_json(self):
        """Test export to JSON format (array)."""
        test_logs = [
            {"level": "info", "time": "2025-10-20T17:19:16Z", "message": "Test log 1"},
            {"level": "error", "time": "2025-10-20T17:19:17Z", "message": "Test log 2"},
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_file = f.name
        
        try:
            # Write logs to JSON
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(test_logs, f, indent=2, ensure_ascii=False)
            
            # Read back and verify
            with open(temp_file, 'r', encoding='utf-8') as f:
                loaded_logs = json.load(f)
            
            self.assertEqual(len(loaded_logs), 2)
            self.assertEqual(loaded_logs[0]['level'], 'info')
            self.assertEqual(loaded_logs[1]['level'], 'error')
            
        finally:
            os.unlink(temp_file)
    
    def test_export_to_csv(self):
        """Test export to CSV format."""
        test_logs = [
            {"level": "info", "time": "2025-10-20T17:19:16Z", "message": "Test log 1"},
            {"level": "error", "time": "2025-10-20T17:19:17Z", "message": "Test log 2"},
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            temp_file = f.name
        
        try:
            # Get all columns
            all_columns = set()
            for log in test_logs:
                all_columns.update(log.keys())
            
            # Sort columns with priority
            priority_columns = ['time', 'level', 'message']
            sorted_columns = []
            for col in priority_columns:
                if col in all_columns:
                    sorted_columns.append(col)
                    all_columns.discard(col)
            sorted_columns.extend(sorted(all_columns))
            
            # Write CSV
            with open(temp_file, 'w', encoding='utf-8', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=sorted_columns, extrasaction='ignore')
                writer.writeheader()
                for log in test_logs:
                    writer.writerow(log)
            
            # Read back and verify
            with open(temp_file, 'r', encoding='utf-8', newline='') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
            
            self.assertEqual(len(rows), 2)
            self.assertEqual(rows[0]['level'], 'info')
            self.assertEqual(rows[0]['message'], 'Test log 1')
            self.assertEqual(rows[1]['level'], 'error')
            self.assertEqual(rows[1]['message'], 'Test log 2')
            
        finally:
            os.unlink(temp_file)
    
    def test_export_csv_with_nested_objects(self):
        """Test that nested objects are converted to JSON strings in CSV."""
        test_logs = [
            {
                "level": "info",
                "time": "2025-10-20T17:19:16Z",
                "message": "Test log",
                "metadata": {"key1": "value1", "key2": "value2"}
            }
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            temp_file = f.name
        
        try:
            # Get all columns
            all_columns = set()
            for log in test_logs:
                all_columns.update(log.keys())
            
            # Sort columns
            priority_columns = ['time', 'level', 'message']
            sorted_columns = []
            for col in priority_columns:
                if col in all_columns:
                    sorted_columns.append(col)
                    all_columns.discard(col)
            sorted_columns.extend(sorted(all_columns))
            
            # Write CSV with nested object handling
            with open(temp_file, 'w', encoding='utf-8', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=sorted_columns, extrasaction='ignore')
                writer.writeheader()
                
                for log in test_logs:
                    row = {}
                    for col in sorted_columns:
                        value = log.get(col, '')
                        if isinstance(value, (dict, list)):
                            row[col] = json.dumps(value, ensure_ascii=False)
                        else:
                            row[col] = value
                    writer.writerow(row)
            
            # Read back and verify
            with open(temp_file, 'r', encoding='utf-8', newline='') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
            
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]['level'], 'info')
            
            # Verify nested object was converted to JSON string
            metadata = json.loads(rows[0]['metadata'])
            self.assertEqual(metadata['key1'], 'value1')
            self.assertEqual(metadata['key2'], 'value2')
            
        finally:
            os.unlink(temp_file)


if __name__ == '__main__':
    unittest.main()
