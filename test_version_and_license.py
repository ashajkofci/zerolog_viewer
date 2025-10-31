#!/usr/bin/env python3
"""Test that version and license info can be read"""
import unittest
from zerolog_viewer import get_version_info, get_license_text


class TestVersionAndLicense(unittest.TestCase):
    """Test version and license reading functionality"""
    
    # Expected patterns
    VERSION_PATTERN = r'^\d+\.\d+\.\d+$'  # X.Y.Z format
    
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
    
    def test_version_format(self):
        """Test that version follows X.Y.Z semantic versioning format"""
        version_info = get_version_info()
        if version_info['version'] != 'Unknown':
            # Should match semantic version format (e.g., "0.3.0")
            import re
            self.assertRegex(version_info['version'], self.VERSION_PATTERN,
                           f"Version '{version_info['version']}' does not match X.Y.Z format")
    
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
        """Test that license text contains copyright notice with year"""
        license_text = get_license_text()
        self.assertIn('Copyright', license_text)
        # Check for a year pattern (e.g., "2025")
        import re
        self.assertRegex(license_text, r'Copyright.*\d{4}',
                        "License should contain copyright with year")


if __name__ == '__main__':
    unittest.main()
