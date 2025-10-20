import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))) # Allow tests to import from src folder

import unittest
from src.indivcontributions import extrapolate_individual_contributions

class TestExtrapolateContributions(unittest.TestCase):
    def setUp(self):
        # Re-use your sample data
        self.sample_project = {
            "files": [
                {"owner": "Tolu", "editors": ["Maya"], "lines": 120},
                {"owner": "Maya", "editors": ["Tolu", "Jackson"], "lines": 80},
                {"owner": "Jackson", "editors": [], "lines": 40}
            ]
        }

    def test_percentages_sum_to_100(self):
        result = extrapolate_individual_contributions(self.sample_project)
        total = sum(c["contribution_percent"] for c in result["contributors"].values())
        self.assertAlmostEqual(total, 100.0, places=1)

    def test_expected_order(self):
        result = extrapolate_individual_contributions(self.sample_project)
        self.assertGreater(result["contributors"]["Tolu"]["contribution_percent"],
                           result["contributors"]["Maya"]["contribution_percent"])
        self.assertGreater(result["contributors"]["Maya"]["contribution_percent"],
                           result["contributors"]["Jackson"]["contribution_percent"])

if __name__ == "__main__":
    unittest.main()

#To test run python tests/test_indivcontributions.py
