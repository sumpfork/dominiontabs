import unittest
import pycodestyle
import glob


class TestCodeFormat(unittest.TestCase):

    def test_conformance(self):
        """Test that we conform to PEP-8."""
        style = pycodestyle.StyleGuide(max_line_length=120)
        result = style.check_files(glob.glob('*.py') + glob.glob('domdiv/*.py') + glob.glob('tests/*.py'))
        self.assertEqual(result.total_errors, 0,
                         "Found code style errors (and warnings).")
