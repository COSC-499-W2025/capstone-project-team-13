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
from src.Analysis.file_hasher import compute_file_hash

# Setup path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.Databases.database import db_manager
from src.Analysis.codeIdentifier import identify_language_and_framework, LANGUAGE_BY_EXTENSION
from src.Extraction.keywordExtractorCode import extract_code_keywords_with_scores
from src.Analysis.importanceScores import calculate_importance_score
from src.Analysis.skillsExtractCodingImproved import analyze_coding_skills_refined, SUBSKILL_KEYWORDS, CORE_FOLDERS, PERIPHERAL_FOLDERS, ADVANCED_KEYWORDS, SKILL_KEYWORDS
from src.Helpers.fileFormatCheck import check_file_format, InvalidFileFormatError
from src.Helpers.fileDataCheck import sniff_supertype
from src.Helpers.classifier import supertype_from_extension
from src.Helpers.gitContributorExtraction import is_git_repository, populate_contributors_for_project

class CodingProjectScanner:
    """Scans and analyzes coding projects"""
    
    def __init__(self, project_path: str):
        """
        Initialize scanner for a coding project folder or single file
        
        Args:
            project_path: Path to coding project root directory or single code file
        
        Raises:
            ValueError: If path doesn't exist or isn't a directory/file as expected
        """
        self.project_path = Path(project_path).resolve()
        if not self.project_path.exists():
            raise ValueError(f"Project path does not exist: {project_path}")
        
        #allow either dir or single file
        self.single_file = self.project_path.is_file()
        if self.single_file:
            self.project_name = self.project_path.stem
        else:
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
        Supports incremental updates.
        
        Returns:
            project_id: Database ID of created/updated project
        """
        from datetime import datetime, timezone
        
        print(f"\n{'='*60}")
        print(f"Scanning Coding Project: {self.project_name}")
        print(f"Path: {self.project_path}")
        print(f"{'='*60}\n")
        
        # Check if already in database
        existing = db_manager.get_project_by_path(str(self.project_path))
        is_incremental = False
        
        if existing:
            print(f"⚠️  Project already exists in database with ID: {existing.id}")
            user_input = input("Options:\n  1. Incremental update (add new files)\n  2. Full rescan (replace all)\n  3. Cancel\nChoice (1/2/3): ").strip()
            
            if user_input == '3':
                print("Scan cancelled.")
                return existing.id
            elif user_input == '1':
                is_incremental = True
                print("Performing incremental update...")
            else:
                # Full rescan - delete and recreate
                db_manager.delete_project(existing.id)
                print("Deleted old project. Re-scanning...")
                existing = None
        
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
        print(f"  ✓ Languages: {', '.join(self.languages) if self.languages else 'None detected'}")
        print(f"  ✓ Frameworks: {', '.join(self.frameworks) if self.frameworks else 'None detected'}")

        # Step 3: Store project and files in database       
        print("\nStep 2b: Analyzing skills...")
        self._analyze_skills()

        if is_incremental:
            project_id = existing.id

            # Get existing file hashes
            existing_files = db_manager.get_files_for_project(project_id)
            existing_hashes = {f.file_hash for f in existing_files if f.file_hash}

            new_files_count = 0
            for file_path in self.code_files:
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

            # 🔹 Recalculate metrics from ALL code files
            print("\nStep X: Recalculating project metrics (incremental)...")
            metrics = self._calculate_metrics()

            # 🔹 Update EVERYTHING that depends on files
            db_manager.update_project(project_id, {
                'lines_of_code': metrics['lines_of_code'],
                'file_count': metrics['file_count'],
                'total_size_bytes': metrics['total_size_bytes'],
                'date_created': metrics['date_created'],
                'date_modified': metrics['date_modified'],
                'languages': list(set(existing.languages + list(self.languages))),
                'frameworks': list(set(existing.frameworks + list(self.frameworks))),
                'updated_at': datetime.now(timezone.utc)
            })

            print(f"  ✓ Added {new_files_count} new files")
            print(f"  ✓ Lines of code: {metrics['lines_of_code']:,}")
            print(f"  ✓ Date range: {metrics['date_created'].date()} → {metrics['date_modified'].date()}")
            print(f"  ✓ Total files: {metrics['file_count']}")

            print("\n✓ Incremental update complete!")

            print(f"  Added {new_files_count} new files")
            print(f"  Total files: {updates['file_count']}")
            
        else:
            # Create new project - FIX: Convert sets to lists
            project_data = {
                'name': self.project_name,
                'file_path': str(self.project_path),
                'file_count': len(self.code_files),
                'project_type': 'code',
                'languages': list(self.languages),
                'frameworks': list(self.frameworks),
                'skills': sorted(self.unified_skills),
                'date_scanned': datetime.now(timezone.utc)
            }
            
            project = db_manager.create_project(project_data)
            project_id = project.id
            
            print(f"\n✓ Project stored with ID: {project_id}")
            
            # Step 3: Store file information
            print("\nStep 3: Storing file information...")
            for file_path in self.code_files:
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
            
            print(f"  ✓ Stored {len(self.code_files)} files")
            # Step X: Calculate + store metrics
            print("\nStep X: Calculating project metrics...")
            metrics = self._calculate_metrics()

            db_manager.update_project(project_id, {
                'lines_of_code': metrics['lines_of_code'],
                'total_size_bytes': metrics['total_size_bytes'],
                'date_created': metrics['date_created'],
                'date_modified': metrics['date_modified'],
                'file_count': metrics['file_count'],
            })
            print(f"  ✓ Lines of code: {metrics['lines_of_code']:,}")
            print(f"  ✓ Date range: {metrics['date_created'].date()} → {metrics['date_modified'].date()}")
        
        # Step 4: Extract Git contributors (if Git repository)
        if is_git_repository(str(self.project_path)):
            print("\nStep 4: Extracting Git contributors...")
            project = db_manager.get_project(project_id)
            try:
                contrib_count = populate_contributors_for_project(project)
                if contrib_count > 0:
                    print(f"  ✓ Added {contrib_count} contributors")
                else:
                    print("  ℹ No Git contributors found")
            except Exception as e:
                print(f"  ⚠️  Could not extract contributors: {e}")
        else:
            print("\nStep 4: Skipping contributor extraction (not a Git repository)")
        
        # Step 5: Calculate and store importance score
        print("\nStep 5: Calculating importance score...")
        try:
            # Fetch project with all relationships loaded for accurate scoring
            project = db_manager.get_project(project_id)
            if project:
                importance_score = calculate_importance_score(project)
                db_manager.update_project(project_id, {'importance_score': importance_score})
                print(f"  ✓ Importance score: {importance_score}")
            else:
                print("  ⚠️  Could not fetch project for scoring")
        except Exception as e:
            print(f"  ⚠️  Could not calculate importance score: {e}")
        
        return project_id
        
    def _find_code_files(self):
        """Find all code files in the project directory using existing config"""
        
        # --- Single-file mode ---
        if self.single_file:
            file_path = self.project_path

            # 1) First: global format check (ALLOWED_FORMATS)
            try:
                check_file_format(str(file_path))
            except InvalidFileFormatError as e:
                # This is where unsupported formats like .zip will show
                print(f"Skipping unsupported file: {file_path} — {e}")
                return

            file_ext = file_path.suffix.lower()

            # 2) Then: is this a code extension we care about?
            if file_ext not in LANGUAGE_BY_EXTENSION:
                print(f"Skipping file with unsupported code extension: {file_path} (ext={file_ext})")
                return

            # 3) Finally: sniff content to confirm it's actually code
            try:
                sniff_type = sniff_supertype(str(file_path))
                if sniff_type != "code":
                    print(f"Skipping file due to content mismatch: {file_path} (sniffed as {sniff_type})")
                    return
            except Exception as e:
                print(f"Skipping file due to sniffing error: {file_path} — {e}")
                return

            self.code_files.append(file_path)
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

                # 1) First: global format check (ALLOWED_FORMATS)
                try:
                    check_file_format(str(file_path))
                except InvalidFileFormatError as e:
                    # ✅ Now you'll see this for disallowed formats like .zip
                    print(f"Skipping unsupported file: {file_path} — {e}")
                    continue

                file_ext = file_path.suffix.lower()

                # 2) Only treat files with known code extensions as "code project" files
                if file_ext not in LANGUAGE_BY_EXTENSION:
                    # Optional log; comment out if it's too noisy
                    print(f"Skipping file with unsupported code extension: {file_path} (ext={file_ext})")
                    continue

                # 3) Sniff actual file content to verify it's code
                try:
                    sniff_type = sniff_supertype(str(file_path))
                    if sniff_type != "code":
                        print(f"Skipping file due to content mismatch: {file_path} (sniffed as {sniff_type})")
                        continue
                except Exception as e:
                    print(f"Skipping file due to sniffing error: {file_path} — {e}")
                    continue

                # If all checks pass, store the file
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
        """Analyze technical skills using refined coding skill extractor"""

        try:
            result = analyze_coding_skills_refined(
                folder_path=str(self.project_path),
                file_extensions={".py", ".js", ".ts", ".java", ".cpp", ".c", ".html", ".css"}
            )
        except Exception as e:
            print(f"  ⚠️ Skill analysis failed: {e}")
            self.all_skills = {}
            self.skill_combinations = {}
            self.unified_skills = set()
            return

        # --- Raw outputs from analyzer ---
        skill_details = result.get("skills", {})
        self.skill_combinations = result.get("skill_combinations", {})

        # --- Filtered skill containers ---
        self.all_skills = {}
        self.unified_skills = set()
        MIN_SKILL_SCORE = 0.01   # minimum normalized score to include

        # Only keep subskill groups we care about
        ALLOWED_SUBSKILL_GROUPS = {"libraries", "tools"}

        for skill, data in skill_details.items():
            score = data.get("score", 0)

            # Only include top-level skills with a significant score
            if score < MIN_SKILL_SCORE:
                continue

            # --- Collect only subskills that actually appear ---
            subskills_cleaned = {}
            for group, items in data.get("subskills", {}).items():
                if group not in ALLOWED_SUBSKILL_GROUPS:
                    continue
                for subskill, count in items.items():
                    if count > 0:  # Only include if detected in this project
                        subskills_cleaned[subskill] = count

            # Store final top-level skill + subskills
            self.all_skills[skill] = {
                "score": score,
                "subskills": subskills_cleaned
            }

            # Unified set for printing
            self.unified_skills.add(skill)

        self._print_skills()



    def _print_skills(self):
        print(f"  ✓ Skills detected ({len(self.all_skills)} total):")
        for skill, data in sorted(self.all_skills.items(), key=lambda x: x[1]["score"], reverse=True):
            print(f"       {skill} (score: {data['score']:.3f})")
            if data["subskills"]:
                subskills_sorted = sorted(data["subskills"].keys())
                print(f"          🔧 {', '.join(subskills_sorted)}")



    
    def _calculate_metrics(self) -> Dict[str, Any]:
        """Calculate basic project metrics"""
        total_lines = 0
        total_size = 0
        created_dates = []
        modified_dates = []

        for file_path in self.code_files:
            try:
                # Count lines robustly
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    total_lines += sum(1 for _ in f)

                stat = file_path.stat()
                total_size += stat.st_size

                # NOTE:
                # - On Windows: st_ctime is creation time
                # - On mac/linux: st_ctime is metadata change time (not true creation)
                created_dates.append(datetime.fromtimestamp(stat.st_ctime, tz=timezone.utc))
                modified_dates.append(datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc))

            except Exception:
                continue

        date_created = min(created_dates) if created_dates else datetime.now(timezone.utc)
        date_modified = max(modified_dates) if modified_dates else datetime.now(timezone.utc)

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
            'skills': sorted(self.unified_skills)
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
                    'category': 'code'
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