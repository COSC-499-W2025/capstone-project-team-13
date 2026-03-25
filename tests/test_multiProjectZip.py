import unittest
import os
import sys
import tempfile
import zipfile
import shutil

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.Analysis.multiProjectZip import (
    splitZipFile, identifyProjectType, _find_project_roots, _count_files_recursive
)


class TestSplitZipFile(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.zip_file = os.path.join(self.test_dir, "test.zip")

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_multi_project_zip(self):
        """Two top-level folders are both returned."""
        with zipfile.ZipFile(self.zip_file, 'w') as zf:
            zf.writestr("project1/file1.txt", "content1")
            zf.writestr("project2/file2.txt", "content2")
        projects = splitZipFile(self.zip_file)
        self.assertIn("project1", projects)
        self.assertIn("project2", projects)
        self.assertEqual(len(projects), 2)

    def test_macosx_artefacts_ignored(self):
        """__MACOSX entries are excluded."""
        with zipfile.ZipFile(self.zip_file, 'w') as zf:
            zf.writestr("project1/main.py", "code")
            zf.writestr("__MACOSX/project1/._main.py", "junk")
        projects = splitZipFile(self.zip_file)
        self.assertEqual(projects, ["project1"])

    def test_windows_backslash_paths(self):
        """ZIP entries using backslash separators are handled correctly."""
        with zipfile.ZipFile(self.zip_file, 'w') as zf:
            zf.writestr("projectA\\main.py", "code")
        projects = splitZipFile(self.zip_file)
        self.assertIn("projectA", projects)

    def test_flat_zip_no_folders(self):
        """A ZIP with files at the root (no sub-folders) returns an empty list."""
        with zipfile.ZipFile(self.zip_file, 'w') as zf:
            zf.writestr("readme.txt", "hello")
            zf.writestr("main.py", "code")
        projects = splitZipFile(self.zip_file)
        # flat ZIP has no sub-folder, so no project names to split
        self.assertEqual(projects, [])


class TestCountFilesRecursive(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_flat_directory(self):
        for name in ["a.py", "b.py", "c.txt"]:
            open(os.path.join(self.test_dir, name), 'w').close()
        self.assertEqual(_count_files_recursive(self.test_dir), 3)

    def test_nested_directories(self):
        sub = os.path.join(self.test_dir, "src", "utils")
        os.makedirs(sub)
        open(os.path.join(self.test_dir, "main.py"), 'w').close()
        open(os.path.join(self.test_dir, "src", "app.py"), 'w').close()
        open(os.path.join(sub, "helper.py"), 'w').close()
        self.assertEqual(_count_files_recursive(self.test_dir), 3)

    def test_empty_directory(self):
        self.assertEqual(_count_files_recursive(self.test_dir), 0)


class TestFindProjectRoots(unittest.TestCase):

    def setUp(self):
        self.extract_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.extract_dir)

    def _make(self, *rel_paths):
        """Create files at given relative paths inside extract_dir."""
        for rel in rel_paths:
            full = os.path.join(self.extract_dir, rel)
            os.makedirs(os.path.dirname(full), exist_ok=True)
            open(full, 'w').close()

    def test_single_wrapper_folder(self):
        """ZIP with one top-level wrapper → wrapper itself is the project root."""
        self._make("myproject/src/main.py", "myproject/README.md")
        roots = _find_project_roots(self.extract_dir)
        self.assertEqual(len(roots), 1)
        self.assertEqual(roots[0][0], "myproject")

    def test_wrapper_with_multiple_subprojects(self):
        """Wrapper folder containing only sub-folders → each sub-folder is a root."""
        self._make("bundle/projectA/main.py", "bundle/projectB/app.py")
        roots = _find_project_roots(self.extract_dir)
        names = [r[0] for r in roots]
        self.assertIn("projectA", names)
        self.assertIn("projectB", names)

    def test_multiple_top_level_folders(self):
        """Multiple top-level folders → each is its own project root."""
        self._make("alpha/main.py", "beta/app.py", "gamma/run.py")
        roots = _find_project_roots(self.extract_dir)
        names = [r[0] for r in roots]
        self.assertIn("alpha", names)
        self.assertIn("beta", names)
        self.assertIn("gamma", names)

    def test_flat_zip_files_at_root(self):
        """Files directly at root (flat ZIP) → entire dir is one project."""
        self._make("main.py", "utils.py", "README.md")
        roots = _find_project_roots(self.extract_dir)
        self.assertEqual(len(roots), 1)
        self.assertEqual(roots[0][1], self.extract_dir)

    def test_macosx_folder_skipped(self):
        """__MACOSX directories are ignored."""
        self._make("myproject/main.py", "__MACOSX/myproject/._main.py")
        roots = _find_project_roots(self.extract_dir)
        self.assertEqual(len(roots), 1)
        self.assertEqual(roots[0][0], "myproject")


class TestIdentifyProjectType(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def _make_file(self, name, content=""):
        path = os.path.join(self.test_dir, name)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w') as f:
            f.write(content)

    def test_code_project(self):
        for name in ["main.py", "utils.py", "app.py"]:
            self._make_file(name)
        result = identifyProjectType(self.test_dir)
        self.assertEqual(result['type'], 'code')

    def test_nested_code_project(self):
        """Code files in subdirectories are found via os.walk."""
        self._make_file("src/main.py")
        self._make_file("src/utils.py")
        self._make_file("tests/test_main.py")
        result = identifyProjectType(self.test_dir)
        self.assertEqual(result['type'], 'code')
        self.assertGreater(result['code_count'], 0)

    def test_empty_folder(self):
        result = identifyProjectType(self.test_dir)
        self.assertEqual(result['type'], 'unknown')

    def test_text_project(self):
        for name in ["essay.txt", "report.txt", "notes.txt"]:
            self._make_file(name, "Some text content")
        result = identifyProjectType(self.test_dir)
        self.assertEqual(result['type'], 'unknown')  # text falls through to unknown per current logic


if __name__ == '__main__':
    unittest.main()