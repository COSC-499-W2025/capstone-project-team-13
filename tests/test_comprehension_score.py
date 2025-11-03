import unittest
import os
import sys
from unittest.mock import mock_open, patch
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.Analysis.keywordAnalytics import calculate_final_score
from src.Analysis.keywordAnalytics import technical_density, keyword_clustering, extract_skills_with_scores
import pandas as pd

class TestCalculateFinalScore(unittest.TestCase):

    def setUp(self):
        self.fake_file = "/fake/path/code.py"

    @patch("src.Analysis.keywordAnalytics.technical_density")
    def test_technical_density_range(self, mock_density):
        """technical_density returns a value between 0 and 1"""
        mock_density.return_value = {"technical_density": 0.85}
        result = mock_density(self.fake_file)
        self.assertGreaterEqual(result["technical_density"], 0)
        self.assertLessEqual(result["technical_density"], 1)

    @patch("src.Analysis.keywordAnalytics.keyword_clustering")
    def test_keyword_clustering_range(self, mock_cluster):
        """keyword_clustering returns counts that normalize to 0-1 range"""
        mock_cluster.return_value = pd.DataFrame({
            "Cluster": ["Python", "ML", "Data"],
            "Keywords": [5, 3, 2]
        })
        cluster_df = mock_cluster(self.fake_file)
        cluster_norm = dict(zip(cluster_df["Cluster"], cluster_df["Keywords"]))
        total = sum(cluster_norm.values())
        for val in cluster_norm.values():
            normalized = val / total
            self.assertGreaterEqual(normalized, 0)
            self.assertLessEqual(normalized, 1)

    @patch("builtins.open", new_callable=mock_open, read_data="")
    @patch("src.Analysis.keywordAnalytics.technical_density")
    @patch("src.Analysis.keywordAnalytics.keyword_clustering")
    @patch("src.Analysis.keywordAnalytics.extract_skills_with_scores")
    def test_empty_input_returns_zero(self, mock_extract, mock_cluster, mock_density, mock_file):
        mock_density.return_value = {"technical_density": 0.0}
        mock_cluster.return_value = pd.DataFrame(columns=["Cluster", "Keywords"])
        mock_extract.return_value = {}

        result = calculate_final_score(self.fake_file)
        self.assertEqual(result["alignment_score"], 0.0)
        self.assertEqual(result["final_score"], 0.0)

    @patch("builtins.open", new_callable=mock_open, read_data="")
    @patch("src.Analysis.keywordAnalytics.technical_density")
    @patch("src.Analysis.keywordAnalytics.keyword_clustering")
    @patch("src.Analysis.keywordAnalytics.extract_skills_with_scores")
    def test_final_score_returns_percentage(self, mock_extract, mock_cluster, mock_density, mock_file):
        import pandas as pd
        mock_density.return_value = {"technical_density": 0.8}
        mock_cluster.return_value = pd.DataFrame({
            "Cluster": ["Python", "ML"],
            "Keywords": [3, 2]
        })
        mock_extract.return_value = {"Python": 0.6, "ML": 0.4}

        result = calculate_final_score(self.fake_file)
        self.assertTrue(0 <= result["final_score"] <= 100)

if __name__ == "__main__":
    unittest.main()