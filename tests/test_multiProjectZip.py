import unittest
import os
import tempfile
import zipfile
import shutil
from src.Analysis.multiProjectZip import splitZipFile, processZipFile, identifyProjectType

class TestMultiProjectZip(unittest.TestCase):

    def setUp(self):
        """Set up a temporary directory and sample ZIP files for testing."""
        self.test_dir = tempfile.mkdtemp()
        self.zip_file = os.path.join(self.test_dir, "test.zip")

    def tearDown(self):
        """Clean up the temporary directory."""
        shutil.rmtree(self.test_dir)

    def test_splitZipFile(self):
        """Test the splitZipFile function."""
        with zipfile.ZipFile(self.zip_file, 'w') as zf:
            zf.writestr(os.path.join("project1", "file1.txt"), "content1")
            zf.writestr(os.path.join("project2", "file2.txt"), "content2")

        projects = splitZipFile(self.zip_file)
        self.assertIn("project1", projects)
        self.assertIn("project2", projects)
        self.assertEqual(len(projects), 2)

    def test_identifyProjectType(self):
        """Test the identifyProjectType function."""
        os.makedirs(os.path.join(self.test_dir, "code_project"))
        with open(os.path.join(self.test_dir, "code_project", "file.py"), 'w') as f:
            f.write("print('Hello')")

        result = identifyProjectType(os.path.join(self.test_dir, "code_project"))
        self.assertEqual(result['type'], 'code')
        self.assertIn('Primarily code', result['details'])

    # Additional tests for processZipFile and other project types can be added later. Ignoring for now so we can implement the basic structure first.

if __name__ == '__main__':
    unittest.main()