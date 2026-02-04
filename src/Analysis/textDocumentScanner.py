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
import nltk
from nltk.tokenize import word_tokenize


# nltk.download('punkt', quiet=True)

# Setup path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from src.Settings.config import EXT_SUPERTYPES
from src.Databases.database import db_manager
from src.Extraction.keywordExtractorText import extract_keywords_with_scores
from src.Analysis.skillsExtractDocs import analyze_folder_for_skills, analyze_document_for_skills, extract_text
from src.Helpers.fileFormatCheck import check_file_format, InvalidFileFormatError
from src.Helpers.fileDataCheck import sniff_supertype
from src.Helpers.classifier import supertype_from_extension
from src.Analysis.file_hasher import compute_file_hash
from src.UserPrompts.config_integration import config_manager

class TextDocumentScanner:
    """Scans and analyzes text-based documents"""

    
    def __init__(self, document_path: str,single_file: Optional[bool] = None):
        """
        Initialize scanner for a text document or folder

        Args:
            document_path: Path to text document file or root directory
            single_file: If True, analyze only the single file; if False, analyze entire folder

        Raises:
            ValueError: If path doesn't exist
        """
        self.document_path = Path(document_path).resolve()
        if not self.document_path.exists():
            raise ValueError(f"Document path does not exist: {document_path}")
        
        
        if single_file is None:
            self.single_file = self.document_path.is_file()
        else:
            self.single_file = single_file

        if self.single_file:
            if not self.document_path.is_file():
                raise ValueError(f"Single file mode requires a file path: {document_path}")
            self.document_name = self.document_path.stem
        else:
            if not self.document_path.is_dir():
                raise ValueError(f"Folder mode requires a directory path: {document_path}")
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
        Supports incremental updates.
        
        Returns:
            project_id: Database ID of created/updated project
        """
        from datetime import datetime, timezone
        
        print(f"\n{'='*60}")
        print(f"Scanning Text Document: {self.document_name}")
        print(f"Path: {self.document_path}")
        print(f"{'='*60}\n")
        
        # Check if already in database
        existing = db_manager.get_project_by_path(str(self.document_path))
        is_incremental = False
        
        if existing:
            print(f"⚠️  Document already exists in database with ID: {existing.id}")
            user_input = input("Options:\n  1. Incremental update (add new files)\n  2. Full rescan (replace all)\n  3. Cancel\nChoice (1/2/3): ").strip()
            
            if user_input == '3':
                print("Scan cancelled.")
                return existing.id
            elif user_input == '1':
                is_incremental = True
                print("Performing incremental update...")
            else:
                db_manager.delete_project(existing.id)
                print("Deleted old project. Re-scanning...")
                existing = None
        
        # Step 1: Find text files
        print("Step 1: Finding text files...")
        self._find_text_files()
        print(f"  ✓ Found {len(self.text_files)} text files")

        if len(self.text_files) == 0:
            print("\n⚠️  No text files found.")
            return None
        
        if is_incremental:
            # Incremental update
            project_id = existing.id
            
            existing_files = db_manager.get_files_for_project(project_id)
            existing_hashes = {f.file_hash for f in existing_files if f.file_hash}
            
            new_files_count = 0
            for file_path in self.text_files:
                file_hash = compute_file_hash(str(file_path))
                
                if file_hash in existing_hashes:
                    continue
                
                file_data = {
                    'project_id': project_id,
                    'file_path': str(file_path),
                    'file_name': file_path.name,
                    'file_type': file_path.suffix,
                    'file_size': file_path.stat().st_size,
                    'file_created': datetime.fromtimestamp(file_path.stat().st_ctime, tz=timezone.utc),
                    'file_modified': datetime.fromtimestamp(file_path.stat().st_mtime, tz=timezone.utc),
                    'file_hash': file_hash
                }
                db_manager.add_file_to_project(file_data)
                new_files_count += 1
            
            updates = {
                'file_count': len(db_manager.get_files_for_project(project_id)),
                'updated_at': datetime.now(timezone.utc)
            }
            db_manager.update_project(project_id, updates)
            
            print(f"\n✓ Incremental update complete!")
            print(f"  Added {new_files_count} new files")
            print(f"  Total files: {updates['file_count']}")
            
        else:
            # Pre-calculate metadata and metrics for accurate scoring
            self._detect_document_types()
            self._analyze_skills()
            metrics = self._calculate_metrics()

            # Create new project
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
                'skills': list(self.all_skills.keys())[:10] if self.all_skills else [],
                'date_scanned': datetime.now(timezone.utc)
            }
            
            project = db_manager.create_project(project_data)
            project_id = project.id
            
            print(f"\n✓ Project stored with ID: {project_id}")
            
            print("\nStep 2: Storing file information...")
            for file_path in self.text_files:
                file_hash = compute_file_hash(str(file_path))
                file_data = {
                    'project_id': project_id,
                    'file_path': str(file_path),
                    'file_name': file_path.name,
                    'file_type': file_path.suffix,
                    'file_size': file_path.stat().st_size,
                    'file_created': datetime.fromtimestamp(file_path.stat().st_ctime, tz=timezone.utc),
                    'file_modified': datetime.fromtimestamp(file_path.stat().st_mtime, tz=timezone.utc),
                    'file_hash': file_hash
                }
                db_manager.add_file_to_project(file_data)
            
            print(f"  ✓ Stored {len(self.text_files)} files")
            
            # Extract keywords if enabled
            # Extract keywords if enabled
            if config_manager.get_or_create_config().enable_keyword_extraction:
                print("\nStep 3: Extracting keywords...")
                self._extract_keywords()
                if self.all_keywords:
                    for keyword, score in self.all_keywords[:30]:  
                        keyword_data = {
                            'project_id': project_id,
                            'keyword': keyword,  
                            'score': float(score)
                        }
                        db_manager.add_keyword(keyword_data)
                    print(f"  ✓ Extracted {len(self.all_keywords)} keywords")

            # Calculate and store importance score after metadata/keywords are saved
            from src.Analysis.importanceScores import calculate_importance_score
            importance_score = calculate_importance_score(project)
            db_manager.update_project(project_id, {'success_score': importance_score})
        
        return project_id
    
    def _find_text_files(self):
        """Find all text files - either single file or entire directory"""

        def _maybe_add_text_file(path: Path):
            """Validate a path as a 'text' file and add to self.text_files if valid."""
            path_str = str(path)
            file_ext = path.suffix.lower()

            # 1) First: global format check (ALLOWED_FORMATS)
            try:
                check_file_format(path_str)
            except InvalidFileFormatError as e:
                # This is where unsupported formats will show
                print(f"Skipping unsupported file: {path_str} — {e}")
                return

            # 2) Then: is this a text extension we care about?
            ext_supertype = supertype_from_extension(path_str)
            if ext_supertype != "text":
                # Not configured as a text file
                print(f"Skipping file with unsupported text extension: {path_str}")
                return

            # 3) Finally: sniff content to confirm it's actually text
            # If sniffing fails, allow the file if extension is text
            try:
                sniffed_supertype = sniff_supertype(path_str)
                if sniffed_supertype != "text":
                    # Allow common text extensions even if sniffing is inconclusive
                    if file_ext not in {'.txt', '.md', '.xml', '.pdf', '.doc', '.docx'}:
                        print(f"Skipping file due to content mismatch: {path_str} (sniffed as {sniffed_supertype})")
                        return
            except Exception:
                # Allow based on extension if sniffing fails
                pass

            # If all checks pass, store the file
            self.text_files.append(path)

        # --- Single file mode ---
        if self.single_file:
            _maybe_add_text_file(self.document_path)
            return

        # --- Directory mode ---
        for root, dirs, files in os.walk(self.document_path):
            # Remove skip directories from dirs list
            dirs[:] = [d for d in dirs if d not in self.skip_dirs and not d.startswith('.')]

            for filename in files:
                # Skip hidden files
                if filename.startswith('.'):
                    continue

                file_path = Path(root) / filename
                _maybe_add_text_file(file_path)

    
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
                text_content = extract_text(str(file_path))
                
                if not text_content or not text_content.strip():
                    continue
                
                keywords = extract_keywords_with_scores(text_content)

                # IMPORTANT: extract_keywords_with_scores returns (score, keyword) tuples!
                for score, keyword in keywords[:10]:  # ✅ CORRECT: score first, keyword second
                    keyword_scores[keyword.lower()] += score
                    
            except Exception as e:
                print(f"  ⚠️  Error extracting keywords from {file_path.name}: {e}")
                continue
        
        # Store sorted list in self.all_keywords as (keyword, score) tuples
        self.all_keywords = sorted(
            keyword_scores.items(),  # items() returns (keyword, score) tuples
            key=lambda x: x[1],
            reverse=True
        )
    
    def _analyze_skills(self): 
        """Analyze skills from text files"""
        
        try:
            if self.single_file:
                # For single file, use the single document analyzer
                skill_results = analyze_document_for_skills(str(self.document_path))
                self.all_skills = {skill: count for skill, count in skill_results}
            else:
                # For folders, use the folder analyzer
                skill_results = analyze_folder_for_skills(str(self.document_path))
                self.all_skills = {skill: count for skill, count in skill_results}
            
        except ImportError:
            pass
        except Exception as e:
            print(f"  ⚠️  Error analyzing skills: {e}")
            pass


    def _read_file_content(self, file_path: Path) -> Optional[str]:
        """Read content from various file types using extract_text"""
        try:
            content = extract_text(str(file_path))
            if content:
                return content
            # Fallback for plain text formats when extract_text returns empty
            if file_path.suffix.lower() in {'.txt', '.md', '.xml'}:
                return file_path.read_text(encoding='utf-8', errors='ignore')
            return content
        except Exception as e:
            print(f"    ⚠️  Error reading {file_path.name}: {str(e)}")
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
            'skills': list(self.all_skills.keys())[:10] if self.all_skills else [],
            'contributors': 1  # Set contributors to 1
        }
        
        # Create project record
        project = db_manager.create_project(project_data)
        
        # Calculate and store importance score
        from src.Analysis.importanceScores import calculate_importance_score
        importance_score = calculate_importance_score(project)
        db_manager.update_project(project.id, {'success_score': importance_score})
        
        # Store keywords (top 30)
        if self.all_keywords:
            print(f"  → Storing {min(len(self.all_keywords), 30)} keywords...")
            for keyword, score in self.all_keywords[:30]:
                db_manager.add_keyword({
                    'project_id': project.id,
                    'keyword': keyword,
                    'score': float(score),
                    #'category': 'text'
                })
        
        return project.id


def scan_text_document(document_path: str, single_file: Optional[bool] = None) -> Optional[int]:
    """
    Convenience function to scan a text document or folder
    
    Args:
        document_path: Path to text document file or directory
        single_file: If True, analyze only the file; if False, analyze entire folder
        
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