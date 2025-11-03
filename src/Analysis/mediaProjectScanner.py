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


class MediaProjectScanner:
    """Scans and analyzes VISUAL media projects (photography, design, video, 3D)"""
    
    # Supported VISUAL media file extensions only
    MEDIA_EXTENSIONS = {
        # Raster images
        '.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.tif', '.webp', '.ico',
        # RAW image formats (photography)
        '.raw', '.cr2', '.nef', '.arw', '.dng', '.orf', '.rw2',
        # Design files (Photoshop, Affinity, etc.)
        '.psd', '.psb', '.xcf', '.afphoto',
        # Vector graphics
        '.ai', '.svg', '.eps', '.cdr',
        # UI/UX design
        '.fig', '.sketch', '.xd',
        # 3D modeling
        '.blend', '.obj', '.fbx', '.max', '.ma', '.mb', '.c4d', '.3ds', '.stl',
        # Video files
        '.mp4', '.mov', '.avi', '.mkv', '.webm', '.flv', '.wmv', '.m4v', '.mpg', '.mpeg',
        # Video project files
        '.aep', '.prproj', '.veg', '.drp',
        # Audio files (for video/motion design projects)
        '.mp3', '.wav', '.flac', '.aac', '.ogg', '.m4a',
    }
    
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
            'Backup', 'Cache', 'Thumbnails'
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
        """Find all media and text files in the project directory"""
        for root, dirs, files in os.walk(self.project_path):
            # Remove skip directories from dirs list
            dirs[:] = [d for d in dirs if d not in self.skip_dirs and not d.startswith('.')]
            
            for filename in files:
                # Skip hidden files
                if filename.startswith('.'):
                    continue
                
                file_path = Path(root) / filename
                file_ext = file_path.suffix.lower()
                
                # Check if it's a media file
                if file_ext in self.MEDIA_EXTENSIONS:
                    self.media_files.append(file_path)
                
                # Check if it's a text file for keyword extraction
                elif file_ext in self.TEXT_EXTENSIONS or filename.upper() in ['README', 'README.TXT']:
                    self.text_files.append(file_path)
    
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