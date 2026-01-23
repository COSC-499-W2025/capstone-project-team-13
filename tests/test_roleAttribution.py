import unittest
from unittest.mock import MagicMock, patch
from src.Analysis.roleAttribution import (
    get_contribution_level,
    get_role_from_contribution,
    calculate_user_contribution,
    assign_user_role,
    identify_user_role
)

class TestRoleAttribution(unittest.TestCase):

    def test_get_contribution_level(self):
        self.assertEqual(get_contribution_level(60, True), "Lead")
        self.assertEqual(get_contribution_level(30, True), "Senior")
        self.assertEqual(get_contribution_level(15, True), "Contributing")
        self.assertEqual(get_contribution_level(5, True), "Junior")
        self.assertEqual(get_contribution_level(0, True), "Supporting")
        self.assertEqual(get_contribution_level(50, False), "Owner")

    def test_get_role_from_contribution(self):
        self.assertEqual(get_role_from_contribution(60, True, "Backend Developer"), "Lead Backend Developer")
        self.assertEqual(get_role_from_contribution(0, False, "Project Manager"), "Owner / Project Manager")

    @patch("src.Analysis.roleAttribution.Session")
    def test_calculate_user_contribution(self, MockSession):
        mock_session = MockSession()
        mock_project = MagicMock()
        mock_project.id = 1

        mock_contributor = MagicMock()
        mock_contributor.name = "test_user"
        mock_contributor.contribution_percent = 45.0

        mock_session.query.return_value.filter.return_value.all.return_value = [mock_contributor]

        result = calculate_user_contribution(mock_session, mock_project, "test_user")
        self.assertEqual(result, 45.0)

    @patch("src.Analysis.roleAttribution.input", side_effect=["test_user", "Backend Developer"])
    @patch("src.Analysis.roleAttribution.Session")
    def test_assign_user_role(self, MockSession, mock_input):
        mock_session = MockSession()
        mock_project = MagicMock()
        mock_project.id = 1

        mock_contributor = MagicMock()
        mock_contributor.name = "test_user"
        mock_contributor.contribution_percent = 45.0

        mock_session.query.return_value.filter.return_value.all.return_value = [mock_contributor]

        assign_user_role(mock_session, mock_project)
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()

    @patch("src.Analysis.roleAttribution.input", side_effect=["1", "2", "y", "Custom Role"])
    @patch("src.Analysis.roleAttribution.Session")
    def test_identify_user_role(self, MockSession, mock_input):
        mock_session = MockSession()
        mock_project = MagicMock()
        mock_project.id = 1
        mock_project.name = "Test Project"

        mock_contributor = MagicMock()
        mock_contributor.name = "test_user"
        mock_contributor.contribution_percent = 45.0

        mock_session.query.return_value.filter.return_value.order_by.return_value.all.return_value = [mock_contributor]

        result = identify_user_role(mock_session, mock_project)
        self.assertEqual(result, "Custom Role")

if __name__ == "__main__":
    unittest.main()