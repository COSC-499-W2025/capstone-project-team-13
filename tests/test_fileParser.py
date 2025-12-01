import unittest
import os
import sys
import tempfile
import json
import csv

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from Helpers.fileParser import (
    parse_txt, parse_json, parse_csv, parse_code,
    parse_docx, parse_pdf, parse_media,
    parse_file, FileParseError
)

from docx import Document
import PyPDF2


class TestTextParser(unittest.TestCase):
    """Test cases for plain text parsing"""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.txt_file = os.path.join(self.test_dir, "test.txt")

    def tearDown(self):
        if os.path.exists(self.txt_file):
            os.remove(self.txt_file)
        os.rmdir(self.test_dir)

    def test_parse_simple_text(self):
        content = "Hello World\nThis is a test"
        with open(self.txt_file, 'w') as f:
            f.write(content)

        result = parse_txt(self.txt_file)

        self.assertEqual(result['type'], 'text')
        self.assertEqual(result['content'], content)
        self.assertEqual(result['lines'], 2)
        self.assertEqual(result['characters'], len(content))

    def test_parse_empty_text(self):
        with open(self.txt_file, 'w') as f:
            f.write("")

        result = parse_txt(self.txt_file)

        self.assertEqual(result['lines'], 0)
        self.assertEqual(result['characters'], 0)

    def test_parse_nonexistent_text(self):
        with self.assertRaises(FileParseError):
            parse_txt("nonexistent.txt")


class TestDocxParser(unittest.TestCase):
    """Test cases for DOCX parsing"""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.docx_file = os.path.join(self.test_dir, "test.docx")

    def tearDown(self):
        if os.path.exists(self.docx_file):
            os.remove(self.docx_file)
        os.rmdir(self.test_dir)

    def test_parse_docx(self):
        doc = Document()
        doc.add_paragraph("Hello")
        doc.add_paragraph("World")
        doc.save(self.docx_file)

        result = parse_docx(self.docx_file)

        self.assertEqual(result["type"], "text")
        self.assertIn("Hello", result["content"])
        self.assertEqual(result["line_count"], 2)
        self.assertEqual(result["word_count"], 2)


class TestPDFParser(unittest.TestCase):
    """Test cases for PDF parsing"""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.pdf_file = os.path.join(self.test_dir, "test.pdf")

    def tearDown(self):
        if os.path.exists(self.pdf_file):
            os.remove(self.pdf_file)
        os.rmdir(self.test_dir)

    def test_parse_pdf(self):
        # Create a minimal valid PDF
        writer = PyPDF2.PdfWriter()
        writer.add_blank_page(width=200, height=200)

        with open(self.pdf_file, "wb") as f:
            writer.write(f)

        # Patch extract_text to ensure content is found
        reader = PyPDF2.PdfReader(self.pdf_file)
        reader.pages[0].extract_text = lambda: "Hello PDF"

        result = parse_pdf(self.pdf_file)

        self.assertEqual(result["type"], "text")
        self.assertIn("Hello PDF", result["content"])
        self.assertGreater(result["word_count"], 0)


class TestJSONParser(unittest.TestCase):
    """Test cases for JSON parsing"""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.json_file = os.path.join(self.test_dir, "test.json")

    def tearDown(self):
        if os.path.exists(self.json_file):
            os.remove(self.json_file)
        os.rmdir(self.test_dir)

    def test_parse_valid_json(self):
        data = {"name": "Test", "value": 123}
        with open(self.json_file, 'w') as f:
            json.dump(data, f)

        result = parse_json(self.json_file)

        self.assertEqual(result['type'], 'json')
        self.assertEqual(result['content'], data)
        self.assertGreater(result['size'], 0)

    def test_parse_invalid_json(self):
        with open(self.json_file, 'w') as f:
            f.write("{invalid json}")

        with self.assertRaises(FileParseError):
            parse_json(self.json_file)


class TestCSVParser(unittest.TestCase):
    """Test cases for CSV parsing"""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.csv_file = os.path.join(self.test_dir, "test.csv")

    def tearDown(self):
        if os.path.exists(self.csv_file):
            os.remove(self.csv_file)
        os.rmdir(self.test_dir)

    def test_parse_valid_csv(self):
        with open(self.csv_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=["name", "age"])
            writer.writeheader()
            writer.writerow({"name": "Alice", "age": "30"})

        result = parse_csv(self.csv_file)

        self.assertEqual(result["type"], "csv")
        self.assertEqual(result["rows"], 1)
        self.assertEqual(result["columns"], ["name", "age"])

    def test_parse_empty_csv(self):
        with open(self.csv_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=["col"])
            writer.writeheader()

        result = parse_csv(self.csv_file)

        self.assertEqual(result["rows"], 0)
        self.assertEqual(result["columns"], [])


class TestPythonParser(unittest.TestCase):
    """Test cases for Python parsing"""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.py_file = os.path.join(self.test_dir, "test.py")

    def tearDown(self):
        if os.path.exists(self.py_file):
            os.remove(self.py_file)
        os.rmdir(self.test_dir)

    def test_parse_python_functions(self):
        code = """def a(): pass\ndef b(): return True"""
        with open(self.py_file, 'w') as f:
            f.write(code)

        result = parse_code(self.py_file)

        self.assertEqual(result["functions"], 2)
        self.assertEqual(result["classes"], 0)

    def test_parse_python_classes(self):
        code = """class A: pass\nclass B: pass"""
        with open(self.py_file, 'w') as f:
            f.write(code)

        result = parse_code(self.py_file)

        self.assertEqual(result["classes"], 2)
        self.assertEqual(result["functions"], 0)

    def test_parse_empty_python(self):
        with open(self.py_file, 'w') as f:
            f.write("")

        result = parse_code(self.py_file)

        self.assertEqual(result["lines"], 0)


class TestMediaParser(unittest.TestCase):
    """Test cases for media parsing"""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.media_file = os.path.join(self.test_dir, "test.png")
        with open(self.media_file, "wb") as f:
            f.write(b"\x00\x01\x02")

    def tearDown(self):
        if os.path.exists(self.media_file):
            os.remove(self.media_file)
        os.rmdir(self.test_dir)

    def test_parse_media(self):
        result = parse_media(self.media_file)
        self.assertEqual(result["type"], "media")
        self.assertEqual(result["size_bytes"], 3)


class TestMainParser(unittest.TestCase):
    """Test cases for main parse_file routing"""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        import shutil
        shutil.rmtree(self.test_dir)

    def test_parse_routing_txt(self):
        path = os.path.join(self.test_dir, "a.txt")
        with open(path, 'w') as f:
            f.write("hello")
        result = parse_file(path)
        self.assertEqual(result["type"], "text")

    def test_parse_routing_docx(self):
        path = os.path.join(self.test_dir, "a.docx")
        doc = Document()
        doc.add_paragraph("hi")
        doc.save(path)
        result = parse_file(path)
        self.assertEqual(result["type"], "text")

    def test_parse_routing_pdf(self):
        path = os.path.join(self.test_dir, "a.pdf")
        writer = PyPDF2.PdfWriter()
        writer.add_blank_page(width=200, height=200)
        with open(path, "wb") as f:
            writer.write(f)
        result = parse_file(path)
        self.assertEqual(result["type"], "text")

    def test_parse_routing_code(self):
        path = os.path.join(self.test_dir, "a.py")
        with open(path, "w") as f:
            f.write("print('x')")
        result = parse_file(path)
        self.assertEqual(result["type"], "python")

    def test_parse_routing_media(self):
        path = os.path.join(self.test_dir, "a.png")
        with open(path, "wb") as f:
            f.write(b"\x00")
        result = parse_file(path)
        self.assertEqual(result["type"], "media")

    def test_unsupported_extension(self):
        path = os.path.join(self.test_dir, "a.xyz")
        with open(path, 'w') as f:
            f.write("test")

        with self.assertRaises(FileParseError):
            parse_file(path)

    def test_case_insensitive_extension(self):
        path = os.path.join(self.test_dir, "a.TXT")
        with open(path, "w") as f:
            f.write("data")

        result = parse_file(path)
        self.assertEqual(result["type"], "text")


if __name__ == '__main__':
    unittest.main()
