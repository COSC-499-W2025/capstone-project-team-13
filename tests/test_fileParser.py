import unittest
import os
import sys
import tempfile
import json
import csv

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from Helpers.fileParser import (
    parse_txt, parse_json, parse_csv, parse_py, 
    parse_file, FileParseError
)


class TestTextParser(unittest.TestCase):
    """Test cases for text file parsing"""
    
    def setUp(self):
        """Create temporary test files"""
        self.test_dir = tempfile.mkdtemp()
        self.txt_file = os.path.join(self.test_dir, "test.txt")
        
    def tearDown(self):
        """Clean up test files"""
        if os.path.exists(self.txt_file):
            os.remove(self.txt_file)
        os.rmdir(self.test_dir)
    
    def test_parse_simple_text(self):
        """Test parsing a simple text file"""
        content = "Hello World\nThis is a test"
        with open(self.txt_file, 'w') as f:
            f.write(content)
        
        result = parse_txt(self.txt_file)
        
        self.assertEqual(result['type'], 'text')
        self.assertEqual(result['content'], content)
        self.assertEqual(result['lines'], 2)
        self.assertEqual(result['characters'], len(content))
    
    def test_parse_empty_text(self):
        """Test parsing an empty text file"""
        with open(self.txt_file, 'w') as f:
            f.write("")
        
        result = parse_txt(self.txt_file)
        
        self.assertEqual(result['lines'], 0)  # Empty file has 0 lines
        self.assertEqual(result['characters'], 0)
    
    def test_parse_nonexistent_text(self):
        """Test parsing a file that doesn't exist"""
        with self.assertRaises(FileParseError):
            parse_txt("nonexistent.txt")


class TestJSONParser(unittest.TestCase):
    """Test cases for JSON file parsing"""
    
    def setUp(self):
        """Create temporary test files"""
        self.test_dir = tempfile.mkdtemp()
        self.json_file = os.path.join(self.test_dir, "test.json")
        
    def tearDown(self):
        """Clean up test files"""
        if os.path.exists(self.json_file):
            os.remove(self.json_file)
        os.rmdir(self.test_dir)
    
    def test_parse_valid_json(self):
        """Test parsing valid JSON"""
        data = {"name": "Test", "value": 123, "active": True}
        with open(self.json_file, 'w') as f:
            json.dump(data, f)
        
        result = parse_json(self.json_file)
        
        self.assertEqual(result['type'], 'json')
        self.assertEqual(result['content'], data)
        self.assertGreater(result['size'], 0)
    
    def test_parse_json_array(self):
        """Test parsing JSON array"""
        data = [1, 2, 3, 4, 5]
        with open(self.json_file, 'w') as f:
            json.dump(data, f)
        
        result = parse_json(self.json_file)
        
        self.assertEqual(result['content'], data)
    
    def test_parse_invalid_json(self):
        """Test parsing invalid JSON"""
        with open(self.json_file, 'w') as f:
            f.write("{invalid json content")
        
        with self.assertRaises(FileParseError) as context:
            parse_json(self.json_file)
        
        self.assertIn("Invalid JSON format", str(context.exception))
    
    def test_parse_empty_json(self):
        """Test parsing empty JSON object"""
        with open(self.json_file, 'w') as f:
            json.dump({}, f)
        
        result = parse_json(self.json_file)
        
        self.assertEqual(result['content'], {})


class TestCSVParser(unittest.TestCase):
    """Test cases for CSV file parsing"""
    
    def setUp(self):
        """Create temporary test files"""
        self.test_dir = tempfile.mkdtemp()
        self.csv_file = os.path.join(self.test_dir, "test.csv")
        
    def tearDown(self):
        """Clean up test files"""
        if os.path.exists(self.csv_file):
            os.remove(self.csv_file)
        os.rmdir(self.test_dir)
    
    def test_parse_valid_csv(self):
        """Test parsing valid CSV with headers"""
        with open(self.csv_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['name', 'age', 'city'])
            writer.writeheader()
            writer.writerow({'name': 'Alice', 'age': '30', 'city': 'NYC'})
            writer.writerow({'name': 'Bob', 'age': '25', 'city': 'LA'})
        
        result = parse_csv(self.csv_file)
        
        self.assertEqual(result['type'], 'csv')
        self.assertEqual(result['rows'], 2)
        self.assertEqual(result['columns'], ['name', 'age', 'city'])
        self.assertEqual(result['content'][0]['name'], 'Alice')
    
    def test_parse_empty_csv(self):
        """Test parsing CSV with only headers"""
        with open(self.csv_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['col1', 'col2'])
            writer.writeheader()
        
        result = parse_csv(self.csv_file)
        
        self.assertEqual(result['rows'], 0)
        self.assertEqual(result['columns'], [])
    
    def test_parse_csv_with_special_chars(self):
        """Test parsing CSV with special characters"""
        with open(self.csv_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['text'])
            writer.writeheader()
            writer.writerow({'text': 'Hello, "World"!'})
        
        result = parse_csv(self.csv_file)
        
        self.assertEqual(result['content'][0]['text'], 'Hello, "World"!')


class TestPythonParser(unittest.TestCase):
    """Test cases for Python file parsing"""
    
    def setUp(self):
        """Create temporary test files"""
        self.test_dir = tempfile.mkdtemp()
        self.py_file = os.path.join(self.test_dir, "test.py")
        
    def tearDown(self):
        """Clean up test files"""
        if os.path.exists(self.py_file):
            os.remove(self.py_file)
        os.rmdir(self.test_dir)
    
    def test_parse_python_with_functions(self):
        """Test parsing Python file with functions"""
        code = """def func1():
    pass

def func2():
    return True
"""
        with open(self.py_file, 'w') as f:
            f.write(code)
        
        result = parse_py(self.py_file)
        
        self.assertEqual(result['type'], 'python')
        self.assertEqual(result['functions'], 2)
        self.assertEqual(result['classes'], 0)
    
    def test_parse_python_with_classes(self):
        """Test parsing Python file with classes"""
        code = """class MyClass:
    def method1(self):
        pass

class AnotherClass:
    pass
"""
        with open(self.py_file, 'w') as f:
            f.write(code)
        
        result = parse_py(self.py_file)
        
        self.assertEqual(result['classes'], 2)
        self.assertEqual(result['functions'], 1)  # method1 counts as function
    
    def test_parse_empty_python(self):
        """Test parsing empty Python file"""
        with open(self.py_file, 'w') as f:
            f.write("")
        
        result = parse_py(self.py_file)
        
        self.assertEqual(result['lines'], 0)  # Empty file has 0 lines
        self.assertEqual(result['functions'], 0)
        self.assertEqual(result['classes'], 0)


class TestMainParser(unittest.TestCase):
    """Test cases for main parse_file function"""
    
    def setUp(self):
        """Create temporary test files"""
        self.test_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        """Clean up test files"""
        import shutil
        shutil.rmtree(self.test_dir)
    
    def test_parse_file_routing(self):
        """Test that parse_file routes to correct parser"""
        # Test .txt routing
        txt_file = os.path.join(self.test_dir, "test.txt")
        with open(txt_file, 'w') as f:
            f.write("test")
        result = parse_file(txt_file)
        self.assertEqual(result['type'], 'text')
        
        # Test .json routing
        json_file = os.path.join(self.test_dir, "test.json")
        with open(json_file, 'w') as f:
            json.dump({}, f)
        result = parse_file(json_file)
        self.assertEqual(result['type'], 'json')
    
    def test_parse_unsupported_format(self):
        """Test parsing unsupported file format"""
        unsupported = os.path.join(self.test_dir, "test.xml")
        with open(unsupported, 'w') as f:
            f.write("<xml></xml>")
        
        with self.assertRaises(FileParseError) as context:
            parse_file(unsupported)
        
        self.assertIn("No parser available", str(context.exception))
    
    def test_parse_case_insensitive_extension(self):
        """Test that file extension matching is case-insensitive"""
        txt_file = os.path.join(self.test_dir, "test.TXT")
        with open(txt_file, 'w') as f:
            f.write("test")
        
        result = parse_file(txt_file)
        self.assertEqual(result['type'], 'text')


if __name__ == '__main__':
    unittest.main()