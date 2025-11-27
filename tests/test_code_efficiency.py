import unittest
from unittest.mock import patch
from src.Analysis import codeEfficiency as ce

class TestCodeEfficiency(unittest.TestCase):

    @patch("src.Analysis.codeEfficiency.identify_language_and_framework")
    def test_interpreted_language(self, mock_ident):
        mock_ident.return_value = ("Python", None)  # force it to recognize as Python
        code = "def sum_list(lst): return sum(lst)"
        result = ce.grade_efficiency(code, "fake_path.py")
        self.assertIsNotNone(result["time_score"])
        self.assertGreater(result["time_score"], 0)

    @patch("src.Analysis.codeEfficiency.identify_language_and_framework")
    def test_compiled_language(self, mock_ident):
        mock_ident.return_value = ("C", None)
        code = "int main() { return 0; }"
        result = ce.grade_efficiency(code, "fake_path.c")
        self.assertIsNotNone(result["time_score"])
        self.assertGreater(result["time_score"], 0)

    @patch("src.Analysis.codeEfficiency.identify_language_and_framework")
    def test_static_language(self, mock_ident):
        mock_ident.return_value = ("HTML", None)
        code = "<html></html>"
        result = ce.grade_efficiency(code, "fake.html")
        self.assertIsNotNone(result["time_score"])
        self.assertGreater(result["time_score"], 0)

    @patch("src.Analysis.codeEfficiency.identify_language_and_framework")
    def test_poor_code(self, mock_ident):
        # Force Python recognition
        mock_ident.return_value = ("Python", None)
        
        # Use the actual file
        file_path = "tests/intentionally_bad_code.py"
        
        with open(file_path, "r", encoding="utf-8") as f:
            code = f.read()
        
        result = ce.grade_efficiency(code, file_path)
        
        self.assertIsNotNone(result["efficiency_score"])
        self.assertLess(result["efficiency_score"], 35)


    @patch("src.Analysis.codeEfficiency.identify_language_and_framework")
    def test_good_code(self, mock_ident):
        mock_ident.return_value = ("Python", None)
        code = "def add(a,b): return a+b"
        result = ce.grade_efficiency(code, "good.py")
        self.assertIsNotNone(result["efficiency_score"])
        self.assertGreater(result["efficiency_score"], 80)

if __name__ == "__main__":
    unittest.main()
