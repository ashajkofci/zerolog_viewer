#!/usr/bin/env python3
"""Test that version and license info can be read"""
import unittest
from zerolog_viewer import get_version_info, get_license_text


class TestVersionAndLicense(unittest.TestCase):
    """Test version and license reading functionality"""
    
    def test_get_version_info_returns_dict(self):
        """Test that get_version_info returns a dict with expected keys"""
        version_info = get_version_info()
        self.assertIsInstance(version_info, dict)
        self.assertIn('version', version_info)
        self.assertIn('git_version', version_info)
    
    def test_version_not_unknown(self):
        """Test that version is not 'Unknown' when VERSION file exists"""
        version_info = get_version_info()
        # In development environment, VERSION file exists
        self.assertNotEqual(version_info['version'], 'Unknown')
        # Version should be in format X.Y.Z
        parts = version_info['version'].split('.')
        self.assertEqual(len(parts), 3 if '.' in version_info['version'] else 1)
    
    def test_get_license_text_returns_string(self):
        """Test that get_license_text returns a non-empty string"""
        license_text = get_license_text()
        self.assertIsInstance(license_text, str)
        self.assertGreater(len(license_text), 0)
    
    def test_license_contains_bsd(self):
        """Test that license text contains BSD 3-Clause License"""
        license_text = get_license_text()
        self.assertIn('BSD 3-Clause License', license_text)
    
    def test_license_contains_copyright(self):
        """Test that license text contains copyright notice"""
        license_text = get_license_text()
        self.assertIn('Copyright', license_text)
        self.assertIn('Adrian Shajkofci', license_text)


if __name__ == '__main__':
    unittest.main()
