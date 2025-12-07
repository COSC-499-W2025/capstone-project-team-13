"""
Visual Media Project Scanner
Scans VISUAL media projects (images, videos, 3D, design files) and stores in database
Note: This scanner is for visual/creative projects only, not text-based projects
"""

import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional
from collections import defaultdict

# Setup path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.Databases.database import db_manager
from src.Analysis.visualMediaAnalyzer import analyze_visual_project
from src.Extraction.keywordExtractorText import extract_keywords_with_scores
from src.Helpers.fileFormatCheck import check_file_format, InvalidFileFormatError
from src.Helpers.fileDataCheck import sniff_supertype
from src.Helpers.classifier import supertype_from_extension


class MediaProjectScanner:
    """Scans and analyzes VISUAL media projects (photography, design, video, 3D)"""
    
    # Text file extensions ONLY for keyword extraction (not counted as media)
    TEXT_EXTENSIONS = {'.txt', '.md'}
    
    def __init__(self, project_path: str):
        """
        Initialize scanner for a VISUAL media project folder
        
        Args:
            project_path: Path to visual media project root directory
            (photography, design, video, 3D modeling, etc.)
        
        Raises:
            ValueError: If path doesn't exist or isn't a directory
        """
        self.project_path = Path(project_path).resolve()
        if not self.project_path.exists():
            raise ValueError(f"Project path does not exist: {project_path}")
        
        #allow directory OR single file
        self.single_file = self.project_path.is_file()
        
        if self.single_file:
            # Use the file name without extension as project name
            self.project_name = self.project_path.stem
        else:
            if not self.project_path.is_dir():
                raise ValueError(f"Project path is not a directory: {project_path}")
        
        self.project_name = self.project_path.name
        
        # Data storage
        self.media_files = []
        self.text_files = []
        self.software_used = set()
        self.skills_detected = set()
        self.all_keywords = []
        
        # Directories to skip during scanning
        self.skip_dirs = {
            'node_modules', '__pycache__', '.git', '.venv', 'venv',
            'env', 'dist', 'build', '.next', '.cache', 'vendor',
            '.pytest_cache', 'coverage', '.mypy_cache', '__MACOSX',
            'Backup', 'Cache', 'Thumbnails', '.DS_Store', 'Thumbs.db',
            '.backup', 'backup', 'backups', '.archive', 'archive', 
            'archives', '.trash', 'trash', 'temp', 'tmp', '.tmp'
        }
    
    def scan_and_store(self) -> Optional[int]:
        """
        Complete workflow: scan, analyze, and store in database
        
        Returns:
            project_id: Database ID of created project, or None if no media found
        """
        print(f"\n{'='*60}")
        print(f"Scanning Visual Media Project: {self.project_name}")
        print(f"Path: {self.project_path}")
        print(f"{'='*60}\n")
        
        # Check if already in database
        existing = db_manager.get_project_by_path(str(self.project_path))
        if existing:
            print(f"⚠️  Project already exists in database with ID: {existing.id}")
            user_input = input("Do you want to re-scan and update? (yes/no): ").strip().lower()
            if user_input != 'yes':
                print("Scan cancelled.")
                return existing.id
            # Delete old project to re-scan
            db_manager.delete_project(existing.id)
            print("Deleted old project. Re-scanning...")
        
        # Step 1: Find all media and text files
        print("Step 1: Finding visual media files...")
        self._find_files()
        print(f"  ✓ Found {len(self.media_files)} visual media files")
        print(f"  ✓ Found {len(self.text_files)} text files (for keywords)")
        
        if len(self.media_files) == 0:
            print("\n⚠️  No visual media files found. This may not be a visual media project.")
            print("    (Looking for: images, videos, design files, 3D models)")
            return None
        
        # Step 2: Analyze using visualMediaAnalyzer
        print("\nStep 2: Analyzing visual media files...")
        self._analyze_media()
        print(f"  ✓ Software: {', '.join(sorted(self.software_used)) or 'None detected'}")
        print(f"  ✓ Skills: {', '.join(sorted(list(self.skills_detected)[:5])) or 'None detected'}")
        
        # Step 3: Extract keywords from text files
        print("\nStep 3: Extracting keywords from project descriptions...")
        self._extract_keywords()
        print(f"  ✓ Extracted {len(self.all_keywords)} unique keywords")
        
        # Step 4: Calculate metrics
        print("\nStep 4: Calculating project metrics...")
        metrics = self._calculate_metrics()
        print(f"  ✓ Total files: {metrics['file_count']}")
        print(f"  ✓ Total size: {metrics['total_size_mb']:.2f} MB")
        
        # Step 5: Store in database
        print("\nStep 5: Storing in database...")
        project_id = self._store_in_database(metrics)
        print(f"  ✓ Stored with project ID: {project_id}")
        
        print(f"\n{'='*60}")
        print(f"✓ Visual Media Project Scan Complete!")
        print(f"{'='*60}\n")
        
        return project_id
    
    def _find_files(self):
        """Find all media and text files in the project directory with validation"""
        
        def _maybe_add_media_file(path: Path):
            """Validate a path as a 'media' file and add to self.media_files if valid."""
            path_str = str(path)
            
            # 1) First: global format check (ALLOWED_FORMATS)
            try:
                check_file_format(path_str)
            except InvalidFileFormatError as e:
                # Unsupported extension → skip with message
                print(f"Skipping unsupported file: {path_str} — {e}")
                return
            
            # 2) Then: map extension → supertype ("text" / "code" / "media" / etc)
            ext_supertype = supertype_from_extension(path_str)
            if ext_supertype != "media":
                # Not configured as a media file
                print(f"Skipping file with unsupported media extension: {path_str}")
                return
            
            # 3) Finally: sniff content to confirm it's actually media
            try:
                sniffed_supertype = sniff_supertype(path_str)
                if sniffed_supertype != "media":
                    # e.g. text file with media extension
                    print(f"Skipping file due to content mismatch: {path_str} (sniffed as {sniffed_supertype})")
                    return
            except Exception as e:
                print(f"Skipping file due to sniffing error: {path_str} — {e}")
                return
            
            # All checks passed → track it
            self.media_files.append(path)
        
        def _maybe_add_text_file(path: Path):
            """Validate a path as a 'text' file for keyword extraction."""
            path_str = str(path)
            file_ext = path.suffix.lower()
            
            # Only process specific text extensions for keyword extraction
            if file_ext not in self.TEXT_EXTENSIONS and path.name.upper() not in ['README', 'README.TXT']:
                return
            
            # 1) Extension-level validation
            try:
                check_file_format(path_str)
            except InvalidFileFormatError:
                # Not in allowed formats, but still try for README files
                if path.name.upper() not in ['README', 'README.TXT']:
                    return
            
            # 2) Map extension → supertype
            ext_supertype = supertype_from_extension(path_str)
            
            # For text files, accept if extension says text OR if it's a README
            if ext_supertype != "text" and path.name.upper() not in ['README', 'README.TXT']:
                return
            
            # 3) Content sniffing for text files
            try:
                sniffed_supertype = sniff_supertype(path_str)
                if sniffed_supertype != "text":
                    return
            except Exception as e:
                # Skip files that fail sniffing
                return
            
            # All checks passed → track it
            self.text_files.append(path)

                    
        # Single-file mode
        if self.single_file:
            file_path = self.project_path
            if file_path.is_file():
                _maybe_add_media_file(file_path)
                _maybe_add_text_file(file_path)
            return
        
        # --- Directory mode ---
        for root, dirs, files in os.walk(self.project_path):
            # Remove skip directories from dirs list
            dirs[:] = [d for d in dirs if d not in self.skip_dirs and not d.startswith('.')]
            
            for filename in files:
                # Skip hidden files
                if filename.startswith('.'):
                    continue
                
                file_path = Path(root) / filename
                
                # Try to add as media file
                _maybe_add_media_file(file_path)
                
                # Try to add as text file (for keyword extraction)
                _maybe_add_text_file(file_path)
    
    def _analyze_media(self):
        """Analyze media files using existing visualMediaAnalyzer function"""
        try:
            # Use existing function
            analysis = analyze_visual_project(str(self.project_path))
            
            if 'software_used' in analysis:
                self.software_used.update(analysis['software_used'])
            
            if 'skills_detected' in analysis:
                self.skills_detected.update(analysis['skills_detected'])
                
        except Exception as e:
            print(f"  ⚠️  Error during media analysis: {e}")
            # Continue anyway with what we have
    
    def _extract_keywords(self):
        """Extract keywords from text files in the project"""
        keyword_scores = defaultdict(float)
        
        for file_path in self.text_files:
            try:
                # Read text file
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    text = f.read()
                
                # Use existing keyword extractor
                keywords = extract_keywords_with_scores(text)
                
                # Aggregate scores (take top 10 per file)
                for score, keyword in keywords[:10]:
                    keyword_scores[keyword.lower()] += score
                    
            except Exception as e:
                # Skip files that can't be processed
                continue
        
        # Sort by score and keep top 30 overall
        self.all_keywords = sorted(
            keyword_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )[:30]
    
    def _calculate_metrics(self) -> Dict[str, Any]:
        """Calculate basic project metrics"""
        total_size = 0
        file_dates = []
        
        for file_path in self.media_files:
            try:
                # Get size and dates
                stat = file_path.stat()
                total_size += stat.st_size
                file_dates.append(datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc))
                
            except Exception:
                continue
        
        # Determine date range
        date_created = min(file_dates) if file_dates else datetime.now(timezone.utc)
        date_modified = max(file_dates) if file_dates else datetime.now(timezone.utc)
        
        return {
            'file_count': len(self.media_files),
            'total_size_bytes': total_size,
            'total_size_mb': total_size / (1024 * 1024),
            'date_created': date_created,
            'date_modified': date_modified
        }
    
    def _store_in_database(self, metrics: Dict[str, Any]) -> int:
        """Store project data in database"""
        
        # Prepare project data
        project_data = {
            'name': self.project_name,
            'file_path': str(self.project_path),
            'date_created': metrics['date_created'],
            'date_modified': metrics['date_modified'],
            'lines_of_code': 0,  # Not applicable for media projects
            'file_count': metrics['file_count'],
            'total_size_bytes': metrics['total_size_bytes'],
            'project_type': 'visual_media',  # Specify as visual media project
            'languages': list(self.software_used),  # Store software in languages field
            'frameworks': [],  # Not applicable
            'skills': list(self.skills_detected)[:10] if self.skills_detected else []
        }
        
        # Create project record
        project = db_manager.create_project(project_data)
        
        # Store keywords (top 20)
        if self.all_keywords:
            print(f"  → Storing {min(len(self.all_keywords), 20)} keywords...")
            for keyword, score in self.all_keywords[:20]:
                db_manager.add_keyword({
                    'project_id': project.id,
                    'keyword': keyword,
                    'score': float(score),
                })
        
        return project.id


def scan_media_project(project_path: str) -> Optional[int]:
    """
    Convenience function to scan a visual media project
    
    Args:
        project_path: Path to visual media project directory
                     (photography, graphic design, video editing, 3D modeling, etc.)
        
    Returns:
        project_id: Database ID of scanned project, or None if no visual media found
    """
    try:
        scanner = MediaProjectScanner(project_path)
        return scanner.scan_and_store()
    except Exception as e:
        print(f"\n✗ Error scanning project: {e}")
        return None


if __name__ == "__main__":
    """Command-line interface"""
    if len(sys.argv) < 2:
        print("Usage: python mediaProjectScanner.py <project_path>")
        sys.exit(1)
    
    project_path = sys.argv[1]
    project_id = scan_media_project(project_path)
    
    if project_id:
        print(f"\n✓ Successfully scanned project. Database ID: {project_id}")
    else:
        print("\n✗ Failed to scan project.")
        sys.exit(1)