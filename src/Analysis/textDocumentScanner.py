"""
Text Document Scanner
Scans text documents, analyzes them using existing functions, and stores in database
"""

import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional
from collections import defaultdict

# Setup path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from src.Settings.config import EXT_SUPERTYPES
from src.Databases.database import db_manager
from src.Extraction.keywordExtractorText import extract_keywords_with_scores
#from src.Analysis.skillsExtractText #TODO: when the function is created, add this import

class TextDocumentScanner:
    """Scans and analyzes text-based documents"""

    # Document file extensions to scan
    TEXT_EXTENSIONS = {
        '.txt', '.md', '.html', '.css',
        '.xml', '.pdf', '.doc', '.docx'
    }
    
    def __init__(self, document_path: str):
        """
        Initialize scanner for a text document folder

        Args:
            document_path: Path to text document root directory

        Raises:
            ValueError: If path doesn't exist or isn't a directory
        """
        self.document_path = Path(document_path).resolve()
        if not self.document_path.exists():
            raise ValueError(f"Document path does not exist: {document_path}")
        if not self.document_path.is_dir():
            raise ValueError(f"Document path is not a directory: {document_path}")

        self.document_name = self.document_path.name

        # Data storage
        self.text_files = []  # List of text file paths
        self.document_types = set()
        self.all_skills = {}
        self.all_keywords = []
        
        # Directories to skip during scanning
        self.skip_dirs = {
            '.git',  # Version control
            '__MACOSX',  # Mac metadata
            '.DS_Store',  # Mac folder settings
            'Thumbs.db',  # Windows thumbnails
            '.backup', 'backup', 'backups',  # Backup folders
            '.archive', 'archive', 'archives',  # Archive folders
            '.trash', 'trash',  # Trash folders
            'temp', 'tmp', '.tmp',  # Temporary folders
        }
    
    def scan_and_store(self) -> int:
        """
        Complete workflow: scan, analyze, and store in database
        
        Returns:
            project_id: Database ID of created project
        """
        print(f"\n{'='*60}")
        print(f"Scanning Text Document: {self.document_name}")
        print(f"Path: {self.document_path}")
        print(f"{'='*60}\n")
        
        # Check if already in database
        existing = db_manager.get_project_by_path(str(self.document_path))
        if existing:
            print(f"⚠️  Document already exists in database with ID: {existing.id}")
            user_input = input("Do you want to re-scan and update? (yes/no): ").strip().lower()
            if user_input != 'yes':
                print("Scan cancelled.")
                return existing.id
            # Delete old project to re-scan
            db_manager.delete_project(existing.id)
            print("Deleted old project. Re-scanning...")
        
        # Step 1: Find all text files
        print("Step 1: Finding text files...")
        self._find_text_files()
        print(f"  ✓ Found {len(self.text_files)} text files")

        if len(self.text_files) == 0:
            print("\n⚠️  No text files found. This may not be a text project.")
            return None
        
        # Step 2: Detect document types
        print("\nStep 2: Detecting document types...")
        self._detect_document_types()
        print(f"  ✓ Document types: {', '.join(sorted(self.document_types)) or 'None detected'}")

        # Step 3: Extract keywords from document
        print("\nStep 3: Extracting keywords from document...")
        self._extract_keywords()
        print(f"  ✓ Extracted {len(self.all_keywords)} unique keywords")
        
        # Step 4: Analyze skills #TODO: update when the function is created
        # print("\nStep 4: Analyzing skills from content...")
        # self._analyze_skills()
        # if self.all_skills:
        #     top_skills = sorted(self.all_skills.items(), key=lambda x: x[1], reverse=True)[:5]
        #     print(f"  ✓ Top skills: {', '.join([s[0] for s in top_skills])}")
        # else:
        #     print("  ✓ No specific skills detected")
        
        # Step 5: Calculate metrics
        print("\nStep 5: Calculating project metrics...")
        metrics = self._calculate_metrics()
        print(f"  ✓ Total word count: ~{metrics['word_count']:,}")
        print(f"  ✓ Total files: {metrics['file_count']}")
        print(f"  ✓ Total size: {metrics['total_size_mb']:.2f} MB")
       
        # Step 6: Store in database
        print("\nStep 6: Storing in database...")
        project_id = self._store_in_database(metrics)
        print(f"  ✓ Stored with project ID: {project_id}")
        
        print(f"\n{'='*60}")
        print(f"✓ Text Document Scan Complete!")
        print(f"{'='*60}\n")
        
        return project_id
    
    def _find_text_files(self):
        """Find all text files in the project directory using existing config"""
        for root, dirs, files in os.walk(self.document_path):
            # Remove skip directories from dirs list
            dirs[:] = [d for d in dirs if d not in self.skip_dirs and not d.startswith('.')]
            
            for filename in files:
                # Skip hidden files
                if filename.startswith('.'):
                    continue
                
                file_path = Path(root) / filename
                file_ext = file_path.suffix.lower()
                
                # Check if it's a text file using EXT_SUPERTYPES
                if EXT_SUPERTYPES.get(file_ext) == "text":
                    self.text_files.append(file_path)
    
    def _detect_document_types(self):
        """Detect document types based on file extensions"""
        type_counts = defaultdict(int)
        
        for file_path in self.text_files:
            file_ext = file_path.suffix.lower()
            
            # Map extensions to document types
            if file_ext == '.txt':
                doc_type = 'Text'
            elif file_ext == '.md':
                doc_type = 'Markdown'
            elif file_ext == '.xml':
                doc_type = 'XML'
            elif file_ext == '.pdf':
                doc_type = 'PDF'
            elif file_ext in {'.doc', '.docx'}:
                doc_type = 'Word'
            else:
                doc_type = 'Other'
            
            self.document_types.add(doc_type)
            type_counts[doc_type] += 1
        
        # Print breakdown
        if type_counts:
            for doc_type, count in sorted(type_counts.items(), key=lambda x: x[1], reverse=True):
                print(f"    - {doc_type}: {count} file(s)")
    
    def _extract_keywords(self):
        """Extract keywords from text files using existing keyword extractor"""
        keyword_scores = defaultdict(float)
        
        for file_path in self.text_files:
            try:
                # Use existing function
                keywords = extract_keywords_with_scores(str(file_path))

                # Aggregate scores (take top 10 per file)
                for score, keyword in keywords[:10]:
                    keyword_scores[keyword.lower()] += score
                    
            except Exception as e:
                # Skip files that can't be processed
                continue
        
        # Sort by score and keep top 50 overall
        self.all_keywords = sorted(
            keyword_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )[:50]
    
    # def _analyze_skills(self): #TODO: implement when the function is pulled to main
    #     """Analyze skills from text files using existing skills extractor"""
    #     try:
    #         # Import the skills analysis function
    #         from src.Analysis.skillsExtractText import analyze_folder_for_skills
            
    #         # Analyze the entire folder for skills
    #         # Returns list of tuples: [(skill, count), ...]
    #         skill_results = analyze_folder_for_skills(str(self.document_path))
            
    #         # Convert to dictionary {skill: score}
    #         self.all_skills = {skill: count for skill, count in skill_results}
            
    #     except ImportError:
    #         # If the module doesn't exist yet, skip skill analysis
    #         pass
    #     except Exception as e:
    #         # Log error but continue processing
    #         print(f"  ⚠️  Error analyzing skills: {e}")
    #         pass


    def _read_file_content(self, file_path: Path) -> Optional[str]:
        """Read content from various file types"""
        file_ext = file_path.suffix.lower()
        
        try:
            # Plain text files
            if file_ext in {'.txt', '.md', '.xml'}:
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()
            
            # PDF files (requires PyPDF2)
            elif file_ext == '.pdf':
                try:
                    import PyPDF2
                    with open(file_path, 'rb') as f:
                        reader = PyPDF2.PdfReader(f)
                        text = []
                        for page in reader.pages:
                            text.append(page.extract_text())
                        return '\n'.join(text)
                except ImportError:
                    print(f"  ⚠️  PyPDF2 not installed, skipping PDF: {file_path.name}")
                    return None
            
            # Word documents (requires python-docx)
            elif file_ext in {'.doc', '.docx'}:
                try:
                    import docx
                    doc = docx.Document(file_path)
                    return '\n'.join([para.text for para in doc.paragraphs])
                except ImportError:
                    print(f"  ⚠️  python-docx not installed, skipping Word doc: {file_path.name}")
                    return None
            
            # Other formats - try as plain text
            else:
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()
                    
        except Exception as e:
            return None
        

    def _calculate_metrics(self) -> Dict[str, Any]:
        """Calculate basic project metrics with robust word counting"""
        import re  # <-- IMPORTANT: ensure this import is present

        total_words = 0
        total_size = 0
        file_dates = []

        for file_path in self.text_files:
            try:
                content = self._read_file_content(file_path)

                if content:
                    # Word-like tokens incl. Unicode letters, digits, and intra-word ’ ' -
                    word_tokens = re.findall(
                        r"[A-Za-z0-9\u00C0-\u024F\u1E00-\u1EFF]+(?:[’'-][A-Za-z0-9\u00C0-\u024F\u1E00-\u1EFF]+)*",
                        content
                    )
                    # Fallback if regex finds nothing but there is content
                    if not word_tokens:
                        word_tokens = content.split()

                    total_words += len(word_tokens)

                # File metadata
                stat = file_path.stat()
                total_size += stat.st_size
                file_dates.append(datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc))

            except Exception as e:
                # Don’t hide errors completely—print once so tests aren’t silent
                print(f"  ⚠️  Skipping {file_path.name} due to error: {e}")
                continue

        # Determine date range
        date_created = min(file_dates) if file_dates else datetime.now(timezone.utc)
        date_modified = max(file_dates) if file_dates else datetime.now(timezone.utc)
        
        return {
            'word_count': total_words,
            'file_count': len(self.text_files),
            'total_size_bytes': total_size,
            'total_size_mb': total_size / (1024 * 1024),
            'date_created': date_created,
            'date_modified': date_modified
        }
    
    def _store_in_database(self, metrics: Dict[str, Any]) -> int:
        """Store project data in database"""
        
        # Prepare project data
        project_data = {
            'name': self.document_name,
            'file_path': str(self.document_path),
            'description': f"Text project with {metrics['file_count']} documents",
            'date_created': metrics['date_created'],
            'date_modified': metrics['date_modified'],
            'word_count': metrics['word_count'], 
            'file_count': metrics['file_count'],
            'total_size_bytes': metrics['total_size_bytes'],
            'project_type': 'text',
            'tags': list(self.document_types),
            'skills': list(self.all_skills.keys())[:10] if self.all_skills else []
        }
        
        # Create project record
        project = db_manager.create_project(project_data)
        
        # Store keywords (top 30)
        if self.all_keywords:
            print(f"  → Storing {min(len(self.all_keywords), 30)} keywords...")
            for keyword, score in self.all_keywords[:30]:
                db_manager.add_keyword({
                    'project_id': project.id,
                    'keyword': keyword,
                    'score': float(score),
                    'category': 'text'
                })
        
        return project.id


def scan_text_document(document_path: str) -> Optional[int]:
    """
    Convenience function to scan a text document
    
    Args:
        document_path: Path to coding project directory
        
    Returns:
        document_id: Database ID of scanned document, or None if failed
    """
    try:
        scanner = TextDocumentScanner(document_path)
        return scanner.scan_and_store()
    except Exception as e:
        print(f"\n✗ Error scanning project: {e}")
        return None


if __name__ == "__main__":
    """Command-line interface"""
    if len(sys.argv) < 2:
        print("Usage: python textDocumentScanner.py <document_path>")
        sys.exit(1)
    
    document_path = sys.argv[1]
    project_id = scan_text_document(document_path)
    
    if project_id:
        print(f"\n✓ Successfully scanned document. Database ID: {project_id}")
    else:
        print("\n✗ Failed to scan document.")
        sys.exit(1)