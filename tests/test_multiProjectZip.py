import sys
import os
import unittest
import zipfile

# Ensure the `src` directory is in the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from src.Analysis.multiProjectZip import splitZipFile, identifyProjectType, processZipFile

class TestMultiProjectZip(unittest.TestCase):

    def setUp(self):
        # Create a temporary zip file for testing
        self.test_zip_path = 'testZip.zip'
        with zipfile.ZipFile(self.test_zip_path, 'w') as test_zip:
            test_zip.writestr('Project1/file1.py', 'print("Hello, World!")')
            test_zip.writestr('Project1/file2.txt', 'Sample text file')
            test_zip.writestr('Project2/file3.mp4', '')
            test_zip.writestr('Project2/file4.jpg', '')
            test_zip.writestr('__MACOSX/._file', 'MACOSX metadata')

    def tearDown(self):
        # Remove the temporary zip file after tests
        if os.path.exists(self.test_zip_path):
            os.remove(self.test_zip_path)

    def test_splitZipFile(self):
        # Test the splitZipFile function
        projects = splitZipFile(self.test_zip_path)
        self.assertIn('Project1', projects)
        self.assertIn('Project2', projects)
        self.assertNotIn('__MACOSX', projects)

    def test_identifyProjectType(self):
        # Test the identifyProjectType function with a folder structure
        os.makedirs('test_folder/code', exist_ok=True)
        os.makedirs('test_folder/media', exist_ok=True)
        os.makedirs('test_folder/text', exist_ok=True)

        with open('test_folder/code/example.py', 'w') as f:
            f.write('print("Hello, World!")')
        with open('test_folder/media/example.mp4', 'w') as f:
            f.write('')
        with open('test_folder/text/example.txt', 'w') as f:
            f.write('Sample text file')

        result = identifyProjectType('test_folder')
        self.assertEqual(result['type'], 'mixed')
        self.assertIn('Mixed project', result['details'])

        # Cleanup
        import shutil
        shutil.rmtree('test_folder')

    def test_processZipFile(self):
        # Test the processZipFile function
        project_details = processZipFile(self.test_zip_path)
        self.assertEqual(len(project_details), 2)

        project1 = next((p for p in project_details if p['project_name'] == 'Project1'), None)
        project2 = next((p for p in project_details if p['project_name'] == 'Project2'), None)

        self.assertIsNotNone(project1)
        self.assertIsNotNone(project2)

        self.assertEqual(project1['type'], 'code')
        self.assertIn('code', project1['details'])

        self.assertEqual(project2['type'], 'media')
        self.assertIn('media', project2['details'])

if __name__ == '__main__':
    unittest.main()