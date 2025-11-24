import os
import shutil
import tempfile
import unittest
from git import Repo, Actor
from src.Analysis.projectcollabtype import identify_project_type


class TestProjectCollabTypeGit(unittest.TestCase):

    def setUp(self):
        # Create a temporary directory that will act as a git repo
        self.temp_dir = tempfile.mkdtemp()
        self.repo = Repo.init(self.temp_dir)

        # Create a file inside the repo
        file_path = os.path.join(self.temp_dir, "test.py")
        with open(file_path, "w") as f:
            f.write("print('hello')")

        # Define authors through GitPython's Actor class
        tolu = Actor("Tolu", "tolu@example.com")
        maya = Actor("Maya", "maya@example.com")

        # Commit #1 - Author: Tolu
        self.repo.index.add(["test.py"])
        self.repo.index.commit("Initial commit", author=tolu, committer=tolu)

        # Commit #2 - Author: Maya
        with open(file_path, "a") as f:
            f.write("\nprint('edit')")
        self.repo.index.add(["test.py"])
        self.repo.index.commit("Edit commit", author=maya, committer=maya)

        self.project_data = {"files": []}

    def tearDown(self): # IMPORTANT: Close before cleanup (Windows fix)
        self.repo.close()
        shutil.rmtree(self.temp_dir)

    def test_git_collaborative(self):
        result = identify_project_type(self.temp_dir, self.project_data)
        self.assertEqual(result, "Collaborative Project")

    def test_git_individual(self):
        # Create new temp repo with ONE author
        single_dir = tempfile.mkdtemp()
        repo2 = Repo.init(single_dir)

        file2 = os.path.join(single_dir, "solo.py")
        with open(file2, "w") as f:
            f.write("print('solo')")

        sana = Actor("Sana", "sana@example.com")

        repo2.index.add(["solo.py"])
        repo2.index.commit("Solo commit test", author=sana, committer=sana)

        data2 = {"files": []}

        result = identify_project_type(single_dir, data2)

        # Windows fix: close before deleting
        repo2.close()
        shutil.rmtree(single_dir)

        self.assertEqual(result, "Individual Project")


if __name__ == "__main__":
    unittest.main()


#To run the tests, type: python -m unittest tests/test_projectcollabtype.py
