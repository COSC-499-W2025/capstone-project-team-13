"""
Integration test for incremental skill extraction.

This test uses:
- a real database project
It verifies that newly introduced libraries are added to project skills
without requiring a full rescan.
"""

import sys
import unittest
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))


from src.Analysis.incrementalSkillUpdater import update_skills_incremental
from src.Databases.database import db_manager


class TestIncrementalSkillUpdater(unittest.TestCase):
    def test_incremental_skill_update_real_db(self):
        tmp_path = Path("/tmp/test_incremental_skill_updater")
        tmp_path.mkdir(parents=True, exist_ok=True)

        # 1. Create a real project in the database
        project = db_manager.create_project({
            "name": "Incremental Skill Integration Test",
            "file_path": str(tmp_path),
            "project_type": "code",
            "skills": ["Python"]
        })

        # 2. Create a real code file that introduces a new skill
        code_file = tmp_path / "use_numpy.py"
        code_file.write_text(
            "import numpy as np\n\n"
            "def foo():\n"
            "    return np.array([1, 2, 3])\n"
        )

        # 3. Run incremental skill update
        update_skills_incremental(project.id, [code_file])

        # 4. Reload project from DB
        updated_project = db_manager.get_project(project.id)

        # 5. Assert skills were merged correctly
        self.assertIn("Python", updated_project.skills)
        self.assertIn("NumPy", updated_project.skills)

        # 6. Cleanup
        db_manager.delete_project(project.id)

if __name__ == "__main__":
    unittest.main()
