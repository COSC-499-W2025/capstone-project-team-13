"""
Tests for the text document scanner
"""

import unittest
import os
import sys
import tempfile
import shutil
from pathlib import Path

# Setup path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.Analysis.textDocumentScanner import TextDocumentScanner, scan_text_document
from src.Databases.database import db_manager


class TestTextDocumentScanner(unittest.TestCase):
    """Test cases for TextDocumentScanner"""
    
    def setUp(self):
        """Create a temporary test document directory"""
        self.test_dir = tempfile.mkdtemp()
        self.document_dir = Path(self.test_dir) / "test_documents"
        self.document_dir.mkdir()
        
        # Create some test document files
        self._create_test_files()
        
        # Clean database before each test
        db_manager.clear_all_data()
    
    def tearDown(self):
        """Clean up test directory and database"""
        shutil.rmtree(self.test_dir)
        db_manager.clear_all_data()
    
    def _create_test_files(self):
        """Create sample document files for testing"""
        
        # Text file with content
        text_file = self.document_dir / "essay.txt"
        text_file.write_text("""
This is a sample essay about technology and innovation.
The world of technology continues to evolve at a rapid pace.
Innovation drives progress in many industries including healthcare,
education, and transportation. Writing skills are essential for
communicating complex ideas effectively to diverse audiences.
""")
        
        # Markdown file
        md_file = self.document_dir / "README.md"
        md_file.write_text("""
# Project Documentation

This is a markdown document with structured content.

## Features
- Writing samples
- Documentation examples
- Technical communication

## Analysis
The analysis section provides detailed insights into
the research methodology and findings.
""")
        
        # Another text file
        notes_file = self.document_dir / "notes.txt"
        notes_file.write_text("""
Research notes on effective communication strategies.
Key concepts include clarity, conciseness, and audience awareness.
Documentation should be well-organized and accessible.
""")
        
        # XML file
        xml_file = self.document_dir / "data.xml"
        xml_file.write_text("""
<?xml version="1.0"?>
<document>
    <title>Sample XML Document</title>
    <content>This is structured data with metadata and content.</content>
</document>
""")
        
        # Create a nested directory with documents
        reports_dir = self.document_dir / "reports"
        reports_dir.mkdir()
        
        nested_file = reports_dir / "report.md"
        nested_file.write_text("""
# Annual Report
This report summarizes the key findings and recommendations.
""")
        
        # Create a directory that should be skipped
        backup_dir = self.document_dir / "backup"
        backup_dir.mkdir()
        
        skip_file = backup_dir / "old.txt"
        skip_file.write_text("This should be skipped")
    
    def test_initialization_valid_path(self):
        """Test scanner initialization with valid path"""
        scanner = TextDocumentScanner(str(self.document_dir))
        
        self.assertEqual(scanner.document_name, "test_documents")
        self.assertTrue(scanner.document_path.exists())
    
    def test_initialization_invalid_path(self):
        """Test scanner initialization with invalid path"""
        with self.assertRaises(ValueError):
            TextDocumentScanner("/nonexistent/path")
    
    def test_initialization_file_not_directory(self):
        """Test scanner initialization with file instead of directory"""
        test_file = Path(self.test_dir) / "test.txt"
        test_file.write_text("test")
        
        with self.assertRaises(ValueError):
            TextDocumentScanner(str(test_file), single_file=False)
    
    def test_find_text_files(self):
        """Test that text files are found correctly"""
        scanner = TextDocumentScanner(str(self.document_dir))
        scanner._find_text_files()
        
        # Should find 5 text files (skip backup)
        self.assertEqual(len(scanner.text_files), 5)
        
        # Check that backup was skipped
        file_paths = [str(f) for f in scanner.text_files]
        self.assertFalse(any('backup' in path for path in file_paths))
    
    def test_detect_document_types(self):
        """Test document type detection"""
        scanner = TextDocumentScanner(str(self.document_dir))
        scanner._find_text_files()
        scanner._detect_document_types()
        
        # Should detect Text, Markdown, and XML
        self.assertIn("Text", scanner.document_types)
        self.assertIn("Markdown", scanner.document_types)
        self.assertIn("XML", scanner.document_types)
    
    def test_extract_keywords(self):
        """Test keyword extraction from documents"""
        scanner = TextDocumentScanner(str(self.document_dir))
        scanner._find_text_files()
        scanner._extract_keywords()
        
        # Should extract some keywords
        self.assertGreater(len(scanner.all_keywords), 0)
        
        # Keywords should be tuples of (keyword, score)
        for keyword, score in scanner.all_keywords:
            self.assertIsInstance(keyword, str)
            self.assertIsInstance(score, (int, float))
    
    def test_read_file_content_text(self):
        """Test reading plain text files"""
        scanner = TextDocumentScanner(str(self.document_dir))
        text_file = self.document_dir / "essay.txt"
        
        content = scanner._read_file_content(text_file)
        
        self.assertIsNotNone(content)
        self.assertIn("technology", content.lower())
    
    def test_read_file_content_markdown(self):
        """Test reading markdown files"""
        scanner = TextDocumentScanner(str(self.document_dir))
        md_file = self.document_dir / "README.md"
        
        content = scanner._read_file_content(md_file)
        
        self.assertIsNotNone(content)
        self.assertIn("documentation", content.lower())
    
    def test_read_file_content_xml(self):
        """Test reading XML files"""
        scanner = TextDocumentScanner(str(self.document_dir))
        xml_file = self.document_dir / "data.xml"
        
        content = scanner._read_file_content(xml_file)
        
        self.assertIsNotNone(content)
        self.assertIn("xml", content.lower())
    
    def test_calculate_metrics(self):
        """Test metrics calculation"""
        scanner = TextDocumentScanner(str(self.document_dir))
        scanner._find_text_files()
        metrics = scanner._calculate_metrics()
        
        # Check that metrics are calculated
        self.assertIn('word_count', metrics)
        self.assertIn('file_count', metrics)
        self.assertIn('total_size_bytes', metrics)
        
        # Word count should be > 0
        self.assertGreater(metrics['word_count'], 0)
        
        # File count should match
        self.assertEqual(metrics['file_count'], 5)
    
    def test_scan_and_store(self):
        """Test complete scan and store workflow"""
        scanner = TextDocumentScanner(str(self.document_dir))
        project_id = scanner.scan_and_store()
        
        # Should return a valid project ID
        self.assertIsNotNone(project_id)
        self.assertIsInstance(project_id, int)
        
        # Verify project is in database
        project = db_manager.get_project(project_id)
        self.assertIsNotNone(project)
        self.assertEqual(project.name, "test_documents")
        self.assertEqual(project.project_type, "text")
        self.assertIsNotNone(project.date_created)
        self.assertIsNotNone(project.date_modified)
        self.assertIsNotNone(project.description)
        self.assertGreater(project.total_size_bytes, 0)
        
        # Verify document types were stored as tags
        self.assertIn("Text", project.tags)
        self.assertIn("Markdown", project.tags)
        
        # Verify word count was stored
        self.assertGreater(project.word_count, 0)
        
        # Verify keywords were stored
        keywords = db_manager.get_keywords_for_project(project_id)
        self.assertGreater(len(keywords), 0)

        # Verify scores were stored
        self.assertIsNotNone(project.success_score)
    
    def test_scan_text_document_function(self):
        """Test convenience function"""
        project_id = scan_text_document(str(self.document_dir))
        
        # Should return valid project ID
        self.assertIsNotNone(project_id)
        
        # Verify in database
        project = db_manager.get_project(project_id)
        self.assertIsNotNone(project)
    
    def test_scan_empty_directory(self):
        """Test scanning directory with no text files"""
        empty_dir = Path(self.test_dir) / "empty_documents"
        empty_dir.mkdir()
        
        # Create only non-text files
        (empty_dir / "image.png").write_bytes(b'\x89PNG\r\n')
        (empty_dir / "data.json").write_text('{"key": "value"}')
        
        scanner = TextDocumentScanner(str(empty_dir))
        project_id = scanner.scan_and_store()
        
        # Should return None (no text files found)
        self.assertIsNone(project_id)
    
    def test_rescan_existing_document(self):
        """Test rescanning a document that already exists"""
        # First scan
        scanner1 = TextDocumentScanner(str(self.document_dir))
        project_id1 = scanner1.scan_and_store()
        
        # Verify it detects existing project
        existing = db_manager.get_project_by_path(str(scanner1.document_path))
        self.assertIsNotNone(existing)
        self.assertEqual(existing.id, project_id1)
    
    def test_word_count_accuracy(self):
        """Test word count calculation accuracy"""
        # Create a document with known word count
        test_dir = Path(self.test_dir) / "word_count_test"
        test_dir.mkdir()
        
        test_file = test_dir / "test.txt"
        test_content = "one two three four five six seven eight nine ten"
        test_file.write_text(test_content)
        
        scanner = TextDocumentScanner(str(test_dir))
        scanner._find_text_files()
        metrics = scanner._calculate_metrics()
        
        # Should count exactly 10 words
        self.assertEqual(metrics['word_count'], 10)


class TestTextDocumentScannerEdgeCases(unittest.TestCase):
    """Test edge cases and error handling"""
    
    def setUp(self):
        """Create test environment"""
        self.test_dir = tempfile.mkdtemp()
        db_manager.clear_all_data()
    
    def tearDown(self):
        """Clean up"""
        shutil.rmtree(self.test_dir)
        db_manager.clear_all_data()
    
    def test_files_with_unicode(self):
        """Test handling files with unicode characters"""
        document_dir = Path(self.test_dir) / "unicode_documents"
        document_dir.mkdir()
        
        # Create file with unicode
        unicode_file = document_dir / "unicode.txt"
        unicode_file.write_text("""
Test document with unicode: café, naïve, 你好
This is a multilingual document with 世界 characters.
Writing samples include résumé and other professional documents. feedback
""", encoding='utf-8')
        
        scanner = TextDocumentScanner(str(document_dir))
        project_id = scanner.scan_and_store()
        
        self.assertIsNotNone(project_id)
        
        # Verify unicode content was processed
        project = db_manager.get_project(project_id)
        self.assertGreater(project.word_count, 0)
    
    def test_very_large_document(self):
        """Test handling very large documents"""
        document_dir = Path(self.test_dir) / "large_documents"
        document_dir.mkdir()
        
        # Create a large file
        large_file = document_dir / "large.txt"
        with open(large_file, 'w') as f:
            for i in range(10000):
                f.write(f"This is sentence number {i} with several words in it. ")
        
        scanner = TextDocumentScanner(str(document_dir))
        project_id = scanner.scan_and_store()
        
        self.assertIsNotNone(project_id)
        
        # Verify high word count
        project = db_manager.get_project(project_id)
        self.assertGreater(project.word_count, 50000)
    
    def test_empty_files(self):
        """Test handling empty document files"""
        document_dir = Path(self.test_dir) / "empty_files"
        document_dir.mkdir()
        
        # Create empty files
        (document_dir / "empty.txt").write_text("")
        (document_dir / "empty.md").write_text("")
        
        scanner = TextDocumentScanner(str(document_dir))
        project_id = scanner.scan_and_store()
        
        # Should still create project but with 0 word count
        self.assertIsNotNone(project_id)
        project = db_manager.get_project(project_id)
        self.assertEqual(project.word_count, 0)
    
    def test_mixed_line_endings(self):
        """Test handling files with different line endings"""
        document_dir = Path(self.test_dir) / "line_endings"
        document_dir.mkdir()
        
        # Create file with mixed line endings
        mixed_file = document_dir / "mixed.txt"
        with open(mixed_file, 'wb') as f:
            f.write(b"Line one\r\nLine two\nLine three\rLine four")
        
        scanner = TextDocumentScanner(str(document_dir))
        project_id = scanner.scan_and_store()
        
        self.assertIsNotNone(project_id)
    
    def test_special_characters(self):
        """Test handling documents with special characters"""
        from textwrap import dedent

        # Create test directory
        test_dir = Path(self.test_dir) / "special_chars"
        test_dir.mkdir()

        # Create test file
        test_file = test_dir / "special.txt"
        test_file.write_text(dedent("""\
    Document with special characters: @#$%^&*()
    Quotes: "double" and 'single'
    Punctuation: period. comma, semicolon; colon: exclamation! question?
    Symbols: © ® ™ § ¶
    """), encoding="utf-8")

        # Run the scanner
        scanner = TextDocumentScanner(str(test_dir))
        project_id = scanner.scan_and_store()

        # Validate results
        self.assertIsNotNone(project_id)
        project = db_manager.get_project(project_id)

        # Should count real words, not symbols
        print("DEBUG word_count:", project.word_count)
        self.assertGreater(project.word_count, 0)



class TestTextDocumentScannerPDFWord(unittest.TestCase):
    """Test PDF and Word document handling (requires libraries)"""
    
    def setUp(self):
        """Create test environment"""
        self.test_dir = tempfile.mkdtemp()
        db_manager.clear_all_data()
    
    def tearDown(self):
        """Clean up"""
        shutil.rmtree(self.test_dir)
        db_manager.clear_all_data()
    
    def test_missing_pdf_library(self):
        """Test graceful handling when PyPDF2 is not installed"""
        document_dir = Path(self.test_dir) / "pdf_documents"
        document_dir.mkdir()
        
        # Create a dummy PDF file (not actually valid PDF)
        pdf_file = document_dir / "document.pdf"
        pdf_file.write_bytes(b'%PDF-1.4\nDummy PDF content')
        
        scanner = TextDocumentScanner(str(document_dir))
        
        # Should handle gracefully even if PyPDF2 is missing
        # The scanner should continue without crashing
        try:
            scanner._find_text_files()
            metrics = scanner._calculate_metrics()
            # Word count might be 0 if PDF can't be read
            self.assertIsInstance(metrics['word_count'], int)
        except ImportError:
            # This is acceptable - library not installed
            pass
    
    def test_missing_docx_library(self):
        """Test graceful handling when python-docx is not installed"""
        document_dir = Path(self.test_dir) / "word_documents"
        document_dir.mkdir()
        
        # Create a dummy DOCX file (not actually valid)
        docx_file = document_dir / "document.docx"
        docx_file.write_bytes(b'PK\x03\x04Dummy DOCX content')
        
        scanner = TextDocumentScanner(str(document_dir))
        
        # Should handle gracefully even if python-docx is missing
        try:
            scanner._find_text_files()
            metrics = scanner._calculate_metrics()
            self.assertIsInstance(metrics['word_count'], int)
        except ImportError:
            # This is acceptable - library not installed
            pass


if __name__ == '__main__':
    unittest.main(verbosity=2)