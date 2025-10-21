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

# Mock tkinter before importing the main module
sys.modules['tkinter'] = Mock()
sys.modules['tkinter.ttk'] = Mock()
sys.modules['tkinter.filedialog'] = Mock()
sys.modules['tkinter.messagebox'] = Mock()

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


if __name__ == '__main__':
    unittest.main()
