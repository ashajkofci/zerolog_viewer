#!/usr/bin/env python3
"""
Integration test for session restoration functionality.
This tests the restore_session logic without requiring a full GUI.
"""

import json
import os
import tempfile
import unittest
from unittest.mock import Mock, patch, MagicMock, call
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

from zerolog_viewer import ConfigManager, ZeroLogViewer


class TestSessionRestoration(unittest.TestCase):
    """Test cases for session restoration functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create temporary directory for config and test files
        self.temp_dir = tempfile.mkdtemp()
        self.config_dir_patch = patch.object(
            ConfigManager, 
            'get_config_dir',
            return_value=Path(self.temp_dir)
        )
        self.config_dir_patch.start()
        
        # Create sample log files
        self.file1 = os.path.join(self.temp_dir, "test1.jsonl")
        self.file2 = os.path.join(self.temp_dir, "test2.jsonl")
        self.file3 = os.path.join(self.temp_dir, "test3.jsonl")
        
        with open(self.file1, 'w') as f:
            f.write('{"level":"info","time":"2025-10-20T17:19:16Z","message":"Test 1"}\n')
        
        with open(self.file2, 'w') as f:
            f.write('{"level":"info","time":"2025-10-20T17:19:17Z","message":"Test 2"}\n')
        
        with open(self.file3, 'w') as f:
            f.write('{"level":"info","time":"2025-10-20T17:19:18Z","message":"Test 3"}\n')
    
    def tearDown(self):
        """Clean up test fixtures."""
        self.config_dir_patch.stop()
        # Clean up temp directory
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_restore_session_with_single_file(self):
        """Test restoring a session with a single file tab."""
        # Save session with single file
        session = {
            "tabs": [
                {
                    "type": "single",
                    "file": self.file1
                }
            ]
        }
        ConfigManager.save_session(session)
        
        # Create mock app
        mock_root = Mock()
        mock_root.geometry = Mock(return_value="1200x700")
        
        with patch.object(ZeroLogViewer, '_create_ui'):
            with patch.object(ZeroLogViewer, 'load_file') as mock_load_file:
                app = ZeroLogViewer(mock_root)
                app.restore_session()
                
                # Verify load_file was called with the correct file
                mock_load_file.assert_called_once_with(self.file1, silent=True)
    
    def test_restore_session_with_merged_files(self):
        """Test restoring a session with merged files."""
        # Save session with merged files
        session = {
            "tabs": [
                {
                    "type": "merged",
                    "files": [self.file1, self.file2]
                }
            ]
        }
        ConfigManager.save_session(session)
        
        # Create mock app
        mock_root = Mock()
        mock_root.geometry = Mock(return_value="1200x700")
        
        with patch.object(ZeroLogViewer, '_create_ui'):
            with patch.object(ZeroLogViewer, 'load_merged_files') as mock_load_merged:
                app = ZeroLogViewer(mock_root)
                app.restore_session()
                
                # Verify load_merged_files was called with the correct files
                mock_load_merged.assert_called_once_with([self.file1, self.file2], silent=True)
    
    def test_restore_session_skips_missing_single_file(self):
        """Test that restore gracefully skips missing single files."""
        # Save session with a file that doesn't exist
        nonexistent_file = os.path.join(self.temp_dir, "nonexistent.jsonl")
        session = {
            "tabs": [
                {
                    "type": "single",
                    "file": nonexistent_file
                }
            ]
        }
        ConfigManager.save_session(session)
        
        # Create mock app
        mock_root = Mock()
        mock_root.geometry = Mock(return_value="1200x700")
        
        with patch.object(ZeroLogViewer, '_create_ui'):
            with patch.object(ZeroLogViewer, 'load_file') as mock_load_file:
                app = ZeroLogViewer(mock_root)
                app.restore_session()
                
                # Verify load_file was NOT called (file doesn't exist)
                mock_load_file.assert_not_called()
    
    def test_restore_session_handles_partially_missing_merged_files(self):
        """Test that restore handles merged files where some files are missing."""
        # Create session with some existing and some missing files
        nonexistent_file = os.path.join(self.temp_dir, "nonexistent.jsonl")
        session = {
            "tabs": [
                {
                    "type": "merged",
                    "files": [self.file1, nonexistent_file, self.file2]
                }
            ]
        }
        ConfigManager.save_session(session)
        
        # Create mock app
        mock_root = Mock()
        mock_root.geometry = Mock(return_value="1200x700")
        
        with patch.object(ZeroLogViewer, '_create_ui'):
            with patch.object(ZeroLogViewer, 'load_merged_files') as mock_load_merged:
                app = ZeroLogViewer(mock_root)
                app.restore_session()
                
                # Verify load_merged_files was called with only existing files
                mock_load_merged.assert_called_once_with([self.file1, self.file2], silent=True)
    
    def test_restore_session_loads_single_file_when_only_one_merged_file_exists(self):
        """Test that when only one file exists in merged files, it loads as single file."""
        # Create session with merged files where only one exists
        nonexistent_file = os.path.join(self.temp_dir, "nonexistent.jsonl")
        session = {
            "tabs": [
                {
                    "type": "merged",
                    "files": [self.file1, nonexistent_file]
                }
            ]
        }
        ConfigManager.save_session(session)
        
        # Create mock app
        mock_root = Mock()
        mock_root.geometry = Mock(return_value="1200x700")
        
        with patch.object(ZeroLogViewer, '_create_ui'):
            with patch.object(ZeroLogViewer, 'load_file') as mock_load_file:
                with patch.object(ZeroLogViewer, 'load_merged_files') as mock_load_merged:
                    app = ZeroLogViewer(mock_root)
                    app.restore_session()
                    
                    # Verify load_file was called (not load_merged_files)
                    mock_load_file.assert_called_once_with(self.file1, silent=True)
                    mock_load_merged.assert_not_called()
    
    def test_restore_session_skips_when_all_merged_files_missing(self):
        """Test that restore gracefully skips when all merged files are missing."""
        # Create session with all missing files
        nonexistent1 = os.path.join(self.temp_dir, "nonexistent1.jsonl")
        nonexistent2 = os.path.join(self.temp_dir, "nonexistent2.jsonl")
        session = {
            "tabs": [
                {
                    "type": "merged",
                    "files": [nonexistent1, nonexistent2]
                }
            ]
        }
        ConfigManager.save_session(session)
        
        # Create mock app
        mock_root = Mock()
        mock_root.geometry = Mock(return_value="1200x700")
        
        with patch.object(ZeroLogViewer, '_create_ui'):
            with patch.object(ZeroLogViewer, 'load_file') as mock_load_file:
                with patch.object(ZeroLogViewer, 'load_merged_files') as mock_load_merged:
                    app = ZeroLogViewer(mock_root)
                    app.restore_session()
                    
                    # Verify nothing was loaded
                    mock_load_file.assert_not_called()
                    mock_load_merged.assert_not_called()
    
    def test_restore_session_with_multiple_tabs(self):
        """Test restoring a session with multiple tabs."""
        # Save session with multiple tabs
        session = {
            "tabs": [
                {
                    "type": "single",
                    "file": self.file1
                },
                {
                    "type": "merged",
                    "files": [self.file2, self.file3]
                },
                {
                    "type": "single",
                    "file": self.file3
                }
            ]
        }
        ConfigManager.save_session(session)
        
        # Create mock app
        mock_root = Mock()
        mock_root.geometry = Mock(return_value="1200x700")
        
        with patch.object(ZeroLogViewer, '_create_ui'):
            with patch.object(ZeroLogViewer, 'load_file') as mock_load_file:
                with patch.object(ZeroLogViewer, 'load_merged_files') as mock_load_merged:
                    app = ZeroLogViewer(mock_root)
                    app.restore_session()
                    
                    # Verify correct calls were made
                    assert mock_load_file.call_count == 2
                    mock_load_file.assert_any_call(self.file1, silent=True)
                    mock_load_file.assert_any_call(self.file3, silent=True)
                    mock_load_merged.assert_called_once_with([self.file2, self.file3], silent=True)


if __name__ == '__main__':
    unittest.main()
