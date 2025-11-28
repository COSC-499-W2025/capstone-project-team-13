"""
Minimal Unit Tests for Deletion Manager
"""
import unittest
import os
import sys
from unittest.mock import Mock, patch, MagicMock

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.deletion_manager import DeletionManager


class TestDeletionManager(unittest.TestCase):
    """Test core deletion functionality"""

    def setUp(self):
        self.manager = DeletionManager()

    # Test: Get shared files
    @patch("src.deletion_manager.db_manager")
    def test_get_shared_files(self, mock_db):
        """Test identifying shared files"""
        # Setup mock session
        mock_session = MagicMock()
        mock_db.get_session.return_value = mock_session
        
        # Create mock files
        mock_file1 = Mock(file_path="/path/to/shared.py")
        mock_file2 = Mock(file_path="/path/to/unique.py")
        
        # Mock query chain
        mock_query = MagicMock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value.all.return_value = [mock_file1, mock_file2]
        
        # Mock counts: file1 is shared (count=2), file2 is not (count=1)
        mock_query.filter.return_value.count.side_effect = [2, 1]
        
        # Test
        shared = self.manager.get_shared_files(1)
        
        # Verify
        self.assertEqual(len(shared), 1)
        self.assertIn("/path/to/shared.py", shared)

    # Test: Delete AI insights
    @patch("src.deletion_manager.db_manager")
    def test_delete_ai_insights(self, mock_db):
        """Test deleting AI insights from a project"""
        mock_project = Mock()
        mock_db.get_project.return_value = mock_project
        mock_db.update_project.return_value = mock_project
        
        result = self.manager.delete_ai_insights_for_project(1)
        
        self.assertTrue(result["success"])
        mock_db.update_project.assert_called_once_with(1, {'ai_description': None})

    # Test: Delete AI insights - project not found
    @patch("src.deletion_manager.db_manager")
    def test_delete_ai_insights_not_found(self, mock_db):
        """Test deleting AI insights when project doesn't exist"""
        mock_db.get_project.return_value = None
        
        result = self.manager.delete_ai_insights_for_project(999)
        
        self.assertFalse(result["success"])
        self.assertIn("error", result)

    # Test: Safe project deletion
    @patch("src.deletion_manager.db_manager")
    @patch.object(DeletionManager, "get_shared_files")
    @patch.object(DeletionManager, "delete_ai_insights_for_project")
    def test_delete_project_safely(self, mock_insights, mock_shared, mock_db):
        """Test safe project deletion"""
        mock_project = Mock()
        mock_db.get_project.return_value = mock_project
        mock_db.delete_project.return_value = True
        mock_shared.return_value = ["/path/to/shared.py", "/path/to/shared2.py"]
        mock_insights.return_value = {"success": True, "cache_deleted": 0}
        
        result = self.manager.delete_project_safely(1, delete_shared_files=False)
        
        self.assertTrue(result["project_deleted"])
        self.assertEqual(result["files_protected"], 2)
        mock_db.delete_project.assert_called_once_with(1)

    # Test: Project deletion - not found
    @patch("src.deletion_manager.db_manager")
    def test_delete_project_not_found(self, mock_db):
        """Test deleting a project that doesn't exist"""
        mock_db.get_project.return_value = None
        
        result = self.manager.delete_project_safely(999)
        
        self.assertFalse(result["project_deleted"])
        self.assertIn("error", result)


if __name__ == "__main__":
    unittest.main()