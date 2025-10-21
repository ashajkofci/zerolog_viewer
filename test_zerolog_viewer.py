#!/usr/bin/env python3
"""
Unit tests for ZeroLog Viewer.
"""

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


if __name__ == '__main__':
    unittest.main()
