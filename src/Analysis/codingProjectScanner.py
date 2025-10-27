# src/Analysis/codingProjectScanner.py
"""
Coding Project Scanner
Scans code projects, analyzes them using existing functions, and stores in database
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
from src.Analysis.codeIdentifier import identify_language_and_framework, LANGUAGE_BY_EXTENSION
from src.Extraction.keywordExtractorCode import extract_code_keywords_with_scores
from src.Analysis.skillsExtractCoding import extract_skills_with_scores


class CodingProjectScanner:
    """Scans and analyzes coding projects"""
    
    def __init__(self, project_path: str):
        """
        Initialize scanner for a coding project folder
        
        Args:
            project_path: Path to coding project root directory
        
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
        self.code_files = []  # List of code file paths
        self.languages = set()
        self.frameworks = set()
        self.all_skills = {}
        self.all_keywords = []
        
        # Directories to skip during scanning
        self.skip_dirs = {
            'node_modules', '__pycache__', '.git', '.venv', 'venv',
            'env', 'dist', 'build', '.next', '.cache', 'vendor',
            '.pytest_cache', 'coverage', '.mypy_cache', '__MACOSX'
        }
    
    def scan_and_store(self) -> int:
        """
        Complete workflow: scan, analyze, and store in database
        
        Returns:
            project_id: Database ID of created project
        """
        print(f"\n{'='*60}")
        print(f"Scanning Coding Project: {self.project_name}")
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
        
        # Step 1: Find all code files
        print("Step 1: Finding code files...")
        self._find_code_files()
        print(f"  ✓ Found {len(self.code_files)} code files")
        
        if len(self.code_files) == 0:
            print("\n⚠️  No code files found. This may not be a coding project.")
            return None
        
        # Step 2: Detect languages and frameworks
        print("\nStep 2: Detecting languages and frameworks...")
        self._detect_languages_and_frameworks()
        print(f"  ✓ Languages: {', '.join(sorted(self.languages)) or 'None detected'}")
        print(f"  ✓ Frameworks: {', '.join(sorted(self.frameworks)) or 'None detected'}")
        
        # Step 3: Extract keywords from code
        print("\nStep 3: Extracting keywords from code...")
        self._extract_keywords()
        print(f"  ✓ Extracted {len(self.all_keywords)} unique keywords")
        
        # Step 4: Analyze skills
        print("\nStep 4: Analyzing coding skills...")
        self._analyze_skills()
        if self.all_skills:
            top_skills = sorted(self.all_skills.items(), key=lambda x: x[1], reverse=True)[:5]
            print(f"  ✓ Top skills: {', '.join([s[0] for s in top_skills])}")
        else:
            print("  ✓ No specific skills detected")
        
        # Step 5: Calculate metrics
        print("\nStep 5: Calculating project metrics...")
        metrics = self._calculate_metrics()
        print(f"  ✓ Total lines of code: {metrics['lines_of_code']:,}")
        print(f"  ✓ Total files: {metrics['file_count']}")
        print(f"  ✓ Total size: {metrics['total_size_mb']:.2f} MB")
        
        # Step 6: Store in database
        print("\nStep 6: Storing in database...")
        project_id = self._store_in_database(metrics)
        print(f"  ✓ Stored with project ID: {project_id}")
        
        print(f"\n{'='*60}")
        print(f"✓ Coding Project Scan Complete!")
        print(f"{'='*60}\n")
        
        return project_id
    
    def _find_code_files(self):
        """Find all code files in the project directory using existing config"""
        for root, dirs, files in os.walk(self.project_path):
            # Remove skip directories from dirs list
            dirs[:] = [d for d in dirs if d not in self.skip_dirs and not d.startswith('.')]
            
            for filename in files:
                # Skip hidden files
                if filename.startswith('.'):
                    continue
                
                file_path = Path(root) / filename
                file_ext = file_path.suffix.lower()
                
                # Check if it's a code file using existing LANGUAGE_BY_EXTENSION
                if file_ext in LANGUAGE_BY_EXTENSION:
                    self.code_files.append(file_path)
    
    def _detect_languages_and_frameworks(self):
        """Detect languages and frameworks using existing codeIdentifier function"""
        for file_path in self.code_files:
            try:
                # Use existing function
                lang, frameworks = identify_language_and_framework(str(file_path))
                
                if lang:
                    self.languages.add(lang)
                if frameworks:
                    self.frameworks.update(frameworks)
                    
            except Exception as e:
                # If detection fails, just use extension mapping as fallback
                file_ext = file_path.suffix.lower()
                lang = LANGUAGE_BY_EXTENSION.get(file_ext)
                if lang:
                    self.languages.add(lang)
    
    def _extract_keywords(self):
        """Extract keywords from code files using existing keyword extractor"""
        keyword_scores = defaultdict(float)
        
        for file_path in self.code_files:
            try:
                # Use existing function
                keywords = extract_code_keywords_with_scores(str(file_path))
                
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
    
    def _analyze_skills(self):
        """Analyze technical skills using existing skills extractor"""
        # Read all code file contents
        all_code_text = []
        
        for file_path in self.code_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    all_code_text.append(f.read())
            except Exception:
                continue
        
        if all_code_text:
            # Combine all code and use existing function
            combined_text = '\n'.join(all_code_text)
            self.all_skills = extract_skills_with_scores(combined_text)
    
    def _calculate_metrics(self) -> Dict[str, Any]:
        """Calculate basic project metrics"""
        total_lines = 0
        total_size = 0
        file_dates = []
        
        for file_path in self.code_files:
            try:
                # Count lines
                with open(file_path, 'r', encoding='utf-8') as f:
                    total_lines += len(f.readlines())
                
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
            'lines_of_code': total_lines,
            'file_count': len(self.code_files),
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
            'lines_of_code': metrics['lines_of_code'],
            'file_count': metrics['file_count'],
            'total_size_bytes': metrics['total_size_bytes'],
            'project_type': 'code',
            'languages': list(self.languages),
            'frameworks': list(self.frameworks),
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
                })
        
        return project.id


def scan_coding_project(project_path: str) -> Optional[int]:
    """
    Convenience function to scan a coding project
    
    Args:
        project_path: Path to coding project directory
        
    Returns:
        project_id: Database ID of scanned project, or None if failed
    """
    try:
        scanner = CodingProjectScanner(project_path)
        return scanner.scan_and_store()
    except Exception as e:
        print(f"\n✗ Error scanning project: {e}")
        return None


if __name__ == "__main__":
    """Command-line interface"""
    if len(sys.argv) < 2:
        print("Usage: python codingProjectScanner.py <project_path>")
        sys.exit(1)
    
    project_path = sys.argv[1]
    project_id = scan_coding_project(project_path)
    
    if project_id:
        print(f"\n✓ Successfully scanned project. Database ID: {project_id}")
    else:
        print("\n✗ Failed to scan project.")
        sys.exit(1)