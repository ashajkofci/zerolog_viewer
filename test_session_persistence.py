#!/usr/bin/env python3
"""
Unit tests for session persistence functionality in ZeroLog Viewer.
"""

import json
import os
import tempfile
import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Mock tkinter and tkinterdnd2 before importing the main module
sys.modules['tkinter'] = Mock()
sys.modules['tkinter.ttk'] = Mock()
sys.modules['tkinter.filedialog'] = Mock()
sys.modules['tkinter.messagebox'] = Mock()
sys.modules['tkinter.simpledialog'] = Mock()
sys.modules['tkinterdnd2'] = Mock()

from zerolog_viewer import ConfigManager


class TestSessionPersistence(unittest.TestCase):
    """Test cases for session persistence functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create temporary directory for config
        self.temp_dir = tempfile.mkdtemp()
        self.config_dir_patch = patch.object(
            ConfigManager, 
            'get_config_dir',
            return_value=Path(self.temp_dir)
        )
        self.config_dir_patch.start()
    
    def tearDown(self):
        """Clean up test fixtures."""
        self.config_dir_patch.stop()
        # Clean up temp directory
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_get_session_file(self):
        """Test that get_session_file returns correct path."""
        session_file = ConfigManager.get_session_file()
        self.assertTrue(str(session_file).endswith('session.json'))
        self.assertEqual(session_file.parent, Path(self.temp_dir))
    
    def test_save_and_load_empty_session(self):
        """Test saving and loading an empty session."""
        session = {"tabs": []}
        ConfigManager.save_session(session)
        
        loaded_session = ConfigManager.load_session()
        self.assertEqual(loaded_session, session)
    
    def test_save_and_load_single_file_session(self):
        """Test saving and loading a session with a single file tab."""
        session = {
            "tabs": [
                {
                    "type": "single",
                    "file": "/path/to/file.jsonl"
                }
            ]
        }
        ConfigManager.save_session(session)
        
        loaded_session = ConfigManager.load_session()
        self.assertEqual(loaded_session, session)
        self.assertEqual(len(loaded_session["tabs"]), 1)
        self.assertEqual(loaded_session["tabs"][0]["type"], "single")
        self.assertEqual(loaded_session["tabs"][0]["file"], "/path/to/file.jsonl")
    
    def test_save_and_load_merged_file_session(self):
        """Test saving and loading a session with merged file tabs."""
        session = {
            "tabs": [
                {
                    "type": "merged",
                    "files": ["/path/to/file1.jsonl", "/path/to/file2.jsonl"]
                }
            ]
        }
        ConfigManager.save_session(session)
        
        loaded_session = ConfigManager.load_session()
        self.assertEqual(loaded_session, session)
        self.assertEqual(len(loaded_session["tabs"]), 1)
        self.assertEqual(loaded_session["tabs"][0]["type"], "merged")
        self.assertEqual(len(loaded_session["tabs"][0]["files"]), 2)
    
    def test_save_and_load_multiple_tabs_session(self):
        """Test saving and loading a session with multiple tabs."""
        session = {
            "tabs": [
                {
                    "type": "single",
                    "file": "/path/to/file1.jsonl"
                },
                {
                    "type": "merged",
                    "files": ["/path/to/file2.jsonl", "/path/to/file3.jsonl"]
                },
                {
                    "type": "single",
                    "file": "/path/to/file4.jsonl"
                }
            ]
        }
        ConfigManager.save_session(session)
        
        loaded_session = ConfigManager.load_session()
        self.assertEqual(loaded_session, session)
        self.assertEqual(len(loaded_session["tabs"]), 3)
        self.assertEqual(loaded_session["tabs"][0]["type"], "single")
        self.assertEqual(loaded_session["tabs"][1]["type"], "merged")
        self.assertEqual(loaded_session["tabs"][2]["type"], "single")
    
    def test_load_nonexistent_session(self):
        """Test loading a session when no session file exists."""
        # Don't save anything first
        loaded_session = ConfigManager.load_session()
        self.assertEqual(loaded_session, {"tabs": []})
    
    def test_session_file_created_on_save(self):
        """Test that session file is created when saving."""
        session = {"tabs": [{"type": "single", "file": "/test.jsonl"}]}
        ConfigManager.save_session(session)
        
        session_file = ConfigManager.get_session_file()
        self.assertTrue(session_file.exists())
    
    def test_session_persists_across_saves(self):
        """Test that session persists across multiple save operations."""
        # First save
        session1 = {
            "tabs": [
                {"type": "single", "file": "/file1.jsonl"}
            ]
        }
        ConfigManager.save_session(session1)
        
        # Second save with different data
        session2 = {
            "tabs": [
                {"type": "single", "file": "/file1.jsonl"},
                {"type": "single", "file": "/file2.jsonl"}
            ]
        }
        ConfigManager.save_session(session2)
        
        # Load should get the latest
        loaded_session = ConfigManager.load_session()
        self.assertEqual(loaded_session, session2)
        self.assertEqual(len(loaded_session["tabs"]), 2)


if __name__ == '__main__':
    unittest.main()
