"""
AI Project Analyzer : Enhanced Project Summaries
==========================================================
Provides AI-powered deep analysis of coding projects, going beyond surface-level
descriptions to uncover technical reasoning, design patterns, and skill evidence.
Based on TA announcement:
- Identify OOP principles (abstraction, encapsulation, polymorphism)
- Analyze data structure choices and performance implications
- Detect algorithmic complexity awareness
- Evaluate technical decision-making
- Uncover evidence of advanced computer science concepts
"""

import os
import sys
import json
import hashlib
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from collections import defaultdict, Counter

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

try:
    from src.AI.ai_service import get_ai_service, AIService
    from src.Databases.database import db_manager
    from src.Analysis.codeIdentifier import identify_language_and_framework
    from src.Extraction.keywordExtractorCode import extract_code_keywords_with_scores
except ImportError as e:
    print(f"⚠️ Import error: {e}")
    print("Make sure you're running from the project root and Week 1 AI service is set up")
    sys.exit(1)


class AIProjectAnalyzer:
    """
    Advanced AI-powered project analyzer with technical depth.
    
    Features:
    - Natural language project descriptions
    - Deep technical analysis (OOP, algorithms, data structures)
    - Skill evidence extraction
    - Smart caching to minimize API costs
    - Batch processing for efficiency
    """

    # Analysis prompt templates for different aspects
    ANALYSIS_PROMPTS = {
        "overview": """Analyze this coding project and provide a 2-3 sentence natural language description.
        Focus on: What does the project do? What technologies are used? What is its scope/complexity?
        Project: {project_name}
        Languages: {languages}
        Frameworks: {frameworks}
        File count: {file_count}
        Lines of code: {lines_of_code}
        Key files: {key_files}
        Provide a concise, professional description suitable for a portfolio or resume.""",

                "technical_depth": """Analyze the technical depth and computer science concepts in this project.
        Look for evidence of:
        1. Object-oriented principles (abstraction, encapsulation, inheritance, polymorphism)
        2. Data structure choices (hash maps, trees, graphs, etc.) and their performance implications
        3. Algorithm complexity awareness (O(n), O(n²), O(log n), etc.)
        4. Design patterns (MVC, Factory, Observer, etc.)
        5. Code organization and architecture decisions
        6. Testing and code quality practices
        Project: {project_name}
        Languages: {languages}
        Code structure: {code_structure}
        Sample keywords: {keywords}
        For each concept found, provide:
        - Evidence (what specifically shows this)
        - Impact (why this choice matters for performance/maintainability)
        - Skill level (novice/intermediate/advanced)
        Be specific and cite actual patterns you detect. If something isn't evident, say so.""",

                "skills_extraction": """Based on this project's technical characteristics, identify the SPECIFIC skills demonstrated.
        Be precise - don't just list languages, identify what the developer can DO.
        Project: {project_name}
        Languages: {languages}
        Frameworks: {frameworks}
        Technical patterns: {technical_patterns}
        Keywords: {keywords}
        For each skill, provide:
        1. Skill name (e.g., "Asynchronous Programming", "API Design", "State Management")
        2. Evidence level (Strong/Moderate/Weak)
        3. One-line justification
        Focus on skills that are DEMONSTRABLE from the code, not assumed.""",

                "skill_growth": """Analyze this project to identify evidence of developer skill progression.
        Look for:
        - Improvements in code organization over time
        - Progression from simple to complex features
        - Refactoring evidence
        - Increasing use of advanced patterns
        - Performance optimization attempts
        Project: {project_name}
        Date created: {date_created}
        Date modified: {date_modified}
        Commit history: {has_commits}
        Describe any visible signs of technical growth or learning."""
    }

    def __init__(self):
        """Initialize the AI analyzer with caching and rate limiting."""
        self.ai_service = get_ai_service()
        self.cache_dir = Path("data/ai_project_analysis_cache")
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Track analysis counts for cost monitoring
        self.analyses_count = 0
        self.cache_hits = 0
        self.cache = {}

    def _get_cache_key(self, project_id: int, analysis_type: str) -> str:
        """Generate cache key for a project analysis."""
        return f"proj_{project_id}_{analysis_type}"

    def _get_cached_analysis(self, project_id: int, analysis_type: str) -> Optional[str]:
        """Retrieve cached analysis if available and fresh (< 7 days)."""
        cache_key = self._get_cache_key(project_id, analysis_type)
        cache_file = self.cache_dir / f"{cache_key}.json"

        if not cache_file.exists():
            return None

        try:
            with open(cache_file, 'r') as f:
                data = json.load(f)

            # Check if cache is still fresh (7 days)
            cached_time = datetime.fromisoformat(data['timestamp'])
            age_days = (datetime.now() - cached_time).days

            if age_days < 7:
                self.cache_hits += 1
                return data['analysis']
            else:
                cache_file.unlink()  # Delete stale cache
                return None
        except Exception as e:
            print(f"⚠️ Cache read error: {e}")
            return None

    def _cache_analysis(self, project_id: int, analysis_type: str, analysis: str):
        """Cache analysis result."""
        cache_key = self._get_cache_key(project_id, analysis_type)
        cache_file = self.cache_dir / f"{cache_key}.json"

        try:
            with open(cache_file, 'w') as f:
                json.dump({
                    'project_id': project_id,
                    'analysis_type': analysis_type,
                    'analysis': analysis,
                    'timestamp': datetime.now().isoformat()
                }, f, indent=2)
        except Exception as e:
            print(f"⚠️ Cache write error: {e}")

    def _gather_project_context(self, project) -> Dict[str, Any]:
        """Gather comprehensive context about a project from database."""
        context = {
            'project_name': project.name,
            'languages': ', '.join(project.languages) if project.languages else 'Not detected',
            'frameworks': ', '.join(project.frameworks) if project.frameworks else 'None',
            'file_count': project.file_count or 0,
            'lines_of_code': project.lines_of_code or 0,
            'date_created': project.date_created.strftime('%Y-%m-%d') if project.date_created else 'Unknown',
            'date_modified': project.date_modified.strftime('%Y-%m-%d') if project.date_modified else 'Unknown',
            'project_id': project.id
        }

        # Get keywords for context
        keywords = db_manager.get_keywords_for_project(project.id)
        context['keywords'] = ', '.join([kw.keyword for kw in keywords[:20]]) if keywords else 'None extracted'

        # Get key files (attempt to identify important files)
        context['key_files'] = self._identify_key_files(project)

        # Get code structure hints
        context['code_structure'] = self._analyze_structure(project)

        # Check for version control
        if project.file_path:
            git_path = Path(project.file_path) / '.git'
            context['has_commits'] = 'Yes' if git_path.exists() else 'No'
        else:
            context['has_commits'] = 'Unknown'

        return context

    def _identify_key_files(self, project) -> str:
        """Identify important files in the project structure."""
        if not project.file_path or not Path(project.file_path).exists():
            return "Not available"

        key_patterns = {
            'entry': ['main.py', 'app.py', 'index.js', 'main.js', 'server.js', 'index.html'],
            'config': ['package.json', 'requirements.txt', 'Cargo.toml', 'pom.xml', 'build.gradle'],
            'test': ['test_', '_test.', 'spec.', '.test.', '.spec.'],
            'readme': ['README', 'readme']
        }

        found = []
        try:
            project_path = Path(project.file_path)
            for file in project_path.rglob('*'):
                if file.is_file():
                    name = file.name.lower()
                    for category, patterns in key_patterns.items():
                        if any(pattern in name for pattern in patterns):
                            found.append(f"{file.name} ({category})")
                            break
                if len(found) >= 5:
                    break
        except Exception:
            return "Not available"

        return ', '.join(found[:5]) if found else "Standard project structure"

    def _analyze_structure(self, project) -> str:
        """Analyze project structure for patterns."""
        if not project.file_path or not Path(project.file_path).exists():
            return "Unknown structure"

        try:
            project_path = Path(project.file_path)
            dirs = [d.name for d in project_path.iterdir() if d.is_dir() and not d.name.startswith('.')]

            patterns = []
            if any(d in ['src', 'lib'] for d in dirs):
                patterns.append("organized source structure")
            if any(d in ['test', 'tests', '__tests__'] for d in dirs):
                patterns.append("dedicated test directory")
            if any(d in ['docs', 'documentation'] for d in dirs):
                patterns.append("documentation")
            if any(d in ['api', 'routes', 'controllers'] for d in dirs):
                patterns.append("API/web architecture")
            if any(d in ['models', 'schemas'] for d in dirs):
                patterns.append("data modeling")
            if any(d in ['components', 'views'] for d in dirs):
                patterns.append("component-based UI")

            if patterns:
                return ', '.join(patterns)
            return f"{len(dirs)} directories, flat structure"
        except Exception:
            return "Unknown structure"

    def analyze_project_overview(self, project_id: int) -> Optional[str]:
        """
        Generate a natural language overview of the project.
        This is the primary description for portfolios/resumes.
        """
        cache_key = self._get_cache_key(project_id, "overview")

        # ✅ Only count one cache hit per retrieval
        if cache_key in self.cache:
            self.cache_hits += 1
            return self.cache[cache_key]

        project = db_manager.get_project(project_id)
        ai_service = get_ai_service()

        # Gather context
        context = self._gather_project_context(project)

        # Generate prompt - use the context dict
        prompt = self.ANALYSIS_PROMPTS['overview'].format(**context)

        print(f"🤖 Generating overview for: {project.name}...")

        result = ai_service.generate_text(prompt)
        self.cache[cache_key] = result

        # ✅ Count total analyses only once per generation
        self.analyses_count += 1
        return result

    def analyze_technical_depth(self, project_id: int) -> Optional[Dict[str, Any]]:
        """
        Perform deep technical analysis to identify CS concepts and patterns.
        This goes beyond surface-level to find evidence of advanced thinking.
        """
        # Check cache first
        cached = self._get_cached_analysis(project_id, 'technical_depth')
        if cached:
            # Parse cached JSON
            try:
                return json.loads(cached)
            except:
                pass  # Fall through to regenerate

        # Get project from database
        project = db_manager.get_project(project_id)
        if not project:
            return None

        # Gather context
        context = self._gather_project_context(project)
        context['technical_patterns'] = "To be analyzed"

        # Generate prompt
        prompt = self.ANALYSIS_PROMPTS['technical_depth'].format(**context)

        # Get AI analysis
        print(f"🔬 Performing deep technical analysis for: {project.name}...")
        analysis_text = self.ai_service.generate_text(
            prompt,
            temperature=0.3,  # Lower temperature for factual analysis
            max_tokens=800
        )

        self.analyses_count += 1

        # Parse the analysis into structured format
        analysis = {
            'raw_analysis': analysis_text,
            'project_id': project_id,
            'analyzed_at': datetime.now().isoformat()
        }

        # Cache as JSON
        self._cache_analysis(project_id, 'technical_depth', json.dumps(analysis))

        return analysis

    def extract_demonstrated_skills(self, project_id: int) -> Optional[List[Dict[str, str]]]:
        """
        Extract specific, demonstrable skills from the project.
        Goes beyond just listing technologies to identify what the developer CAN DO.
        """
        # Check cache first
        cached = self._get_cached_analysis(project_id, 'skills')
        if cached:
            try:
                return json.loads(cached)
            except:
                pass

        # Get project from database
        project = db_manager.get_project(project_id)
        if not project:
            return None

        # Gather context
        context = self._gather_project_context(project)

        # Get technical depth for better skill extraction
        tech_analysis = self.analyze_technical_depth(project_id)
        context['technical_patterns'] = tech_analysis.get('raw_analysis', 'None analyzed') if tech_analysis else 'None'

        # Generate prompt
        prompt = self.ANALYSIS_PROMPTS['skills_extraction'].format(**context)

        # Get AI analysis
        print(f"💡 Extracting demonstrable skills for: {project.name}...")
        skills_text = self.ai_service.generate_text(
            prompt,
            temperature=0.2,  # Low temperature for precise skill identification
            max_tokens=500
        )

        self.analyses_count += 1

        # Parse skills into structured format
        # The AI should return skills in a parseable format
        skills = self._parse_skills_from_text(skills_text)

        # Cache as JSON
        self._cache_analysis(project_id, 'skills', json.dumps(skills))

        return skills

    def _parse_skills_from_text(self, text: str) -> List[Dict[str, str]]:
        """Parse AI-generated skills text into structured format."""
        skills = []
        lines = text.strip().split('\n')

        for line in lines:
            line = line.strip()
            if not line or line.startswith('#'):
                continue

            # Try to parse skill format: "Skill Name (Evidence): Justification"
            # Or simpler format: "Skill Name - Evidence - Justification"
            if '(' in line and ')' in line:
                parts = line.split('(', 1)
                skill_name = parts[0].strip('- •123456789.').strip()
                rest = parts[1].split(')', 1)
                evidence = rest[0].strip()
                justification = rest[1].strip(' :-') if len(rest) > 1 else ""

                if skill_name:
                    skills.append({
                        'skill': skill_name,
                        'evidence': evidence,
                        'justification': justification
                    })
            elif '-' in line:
                parts = line.split('-')
                if len(parts) >= 2:
                    skill_name = parts[0].strip('- •123456789.').strip()
                    evidence = parts[1].strip() if len(parts) > 1 else "Demonstrated"
                    justification = parts[2].strip() if len(parts) > 2 else ""

                    if skill_name:
                        skills.append({
                            'skill': skill_name,
                            'evidence': evidence,
                            'justification': justification
                        })

        return skills

    def analyze_project_complete(self, project_id: int) -> Dict[str, Any]:
        """
        Perform complete AI analysis on a project.
        Returns all analysis types in one comprehensive result.
        """
        print(f"\n{'='*70}")
        print(f"🤖 AI Analysis: Complete Project Analysis")
        print(f"{'='*70}\n")

        project = db_manager.get_project(project_id)
        if not project:
            return {'error': 'Project not found'}

        print(f"📁 Project: {project.name}")
        print(f"🔬 Running comprehensive AI analysis...\n")

        results = {
            'project_id': project_id,
            'project_name': project.name,
            'analyzed_at': datetime.now().isoformat(),
            'overview': None,
            'technical_depth': None,
            'skills': None,
            'cache_stats': {
                'analyses_run': self.analyses_count,
                'cache_hits': self.cache_hits
            }
        }

        # Run all analyses
        try:
            results['overview'] = self.analyze_project_overview(project_id)
            results['technical_depth'] = self.analyze_technical_depth(project_id)
            results['skills'] = self.extract_demonstrated_skills(project_id)
        except Exception as e:
            results['error'] = str(e)
            print(f"❌ Analysis error: {e}")

        # Update cache stats
        results['cache_stats']['analyses_run'] = self.analyses_count
        results['cache_stats']['cache_hits'] = self.cache_hits

        print(f"\n✅ Analysis complete!")
        print(f"📊 API calls made: {self.analyses_count}")
        print(f"💾 Cache hits: {self.cache_hits}")

        return results

    def batch_analyze_projects(self, project_ids: List[int], 
                              analysis_types: List[str] = None) -> List[Dict[str, Any]]:
        """
        Batch process multiple projects for efficiency.
        
        Args:
            project_ids: List of project IDs to analyze
            analysis_types: Types of analysis to run (default: all)
                          Options: ['overview', 'technical_depth', 'skills']
        
        Returns:
            List of analysis results
        """
        if analysis_types is None:
            analysis_types = ['overview', 'technical_depth', 'skills']

        print(f"\n{'='*70}")
        print(f"🚀 Batch Analysis: {len(project_ids)} projects")
        print(f"{'='*70}\n")

        results = []
        total_start_analyses = self.analyses_count
        total_start_cache = self.cache_hits

        for i, project_id in enumerate(project_ids, 1):
            project = db_manager.get_project(project_id)
            if not project:
                print(f"⚠️ Project {project_id} not found, skipping...")
                continue

            print(f"\n[{i}/{len(project_ids)}] Processing: {project.name}")

            project_result = {
                'project_id': project_id,
                'project_name': project.name,
                'analyzed_at': datetime.now().isoformat()
            }

            # Run requested analyses
            try:
                if 'overview' in analysis_types:
                    project_result['overview'] = self.analyze_project_overview(project_id)

                if 'technical_depth' in analysis_types:
                    project_result['technical_depth'] = self.analyze_technical_depth(project_id)

                if 'skills' in analysis_types:
                    project_result['skills'] = self.extract_demonstrated_skills(project_id)

                print(f"   ✅ Complete")
            except Exception as e:
                project_result['error'] = str(e)
                print(f"   ❌ Error: {e}")

            results.append(project_result)

        # Print batch summary
        print(f"\n{'='*70}")
        print(f"📊 Batch Analysis Summary")
        print(f"{'='*70}")
        print(f"Projects processed: {len(results)}")
        print(f"Total API calls: {self.analyses_count - total_start_analyses}")
        print(f"Cache hits: {self.cache_hits - total_start_cache}")
        print(f"Cache hit rate: {(self.cache_hits - total_start_cache) / max(1, (self.analyses_count - total_start_analyses)) * 100:.1f}%")

        return results

    def update_database_with_analysis(self, project_id: int, analysis: Dict[str, Any]) -> bool:
        """
        Update the database with AI-generated analysis results.
        Stores the overview as ai_description in the project record.
        """
        if not analysis or 'overview' not in analysis:
            return False

        try:
            # Update project with AI description
            success = db_manager.update_project(project_id, {
                'ai_description': analysis['overview']
            })

            if success:
                print(f"✅ Updated database for project {project_id}")

            return success
        except Exception as e:
            print(f"❌ Database update error: {e}")
            return False


def analyze_single_project_cli():
    """CLI function to analyze a single project."""
    print("\n=== AI Project Analyzer ===\n")

    # Get project
    project_id = input("Enter project ID: ").strip()
    if not project_id.isdigit():
        print("❌ Invalid project ID")
        return

    analyzer = AIProjectAnalyzer()
    results = analyzer.analyze_project_complete(int(project_id))

    if 'error' in results:
        print(f"\n❌ Error: {results['error']}")
        return

    # Display results
    print(f"\n{'='*70}")
    print(f"📋 AI Analysis Results")
    print(f"{'='*70}\n")

    if results['overview']:
        print(f"📝 Overview:")
        print(f"{results['overview']}\n")

    if results['technical_depth']:
        print(f"🔬 Technical Depth:")
        print(f"{results['technical_depth'].get('raw_analysis', 'No analysis')}\n")

    if results['skills']:
        print(f"💡 Demonstrated Skills ({len(results['skills'])}):")
        for skill in results['skills'][:10]:
            print(f"   • {skill['skill']} ({skill['evidence']})")
            if skill['justification']:
                print(f"     {skill['justification']}")
        if len(results['skills']) > 10:
            print(f"   ... and {len(results['skills']) - 10} more")

    # Ask to update database
    update = input("\n💾 Update database with AI description? (yes/no): ").strip().lower()
    if update == 'yes':
        analyzer.update_database_with_analysis(int(project_id), results)


def batch_analyze_all_projects():
    """Analyze all projects in the database."""
    print("\n=== Batch AI Project Analysis ===\n")

    projects = db_manager.get_all_projects()
    if not projects:
        print("📭 No projects found in database")
        return

    print(f"Found {len(projects)} projects in database\n")

    # Ask which analyses to run
    print("Select analyses to run:")
    print("1. Overview only (fastest")
    print("2. Overview + Technical Depth")
    print("3. Complete analysis (all types")

    choice = input("\nChoice (1-3): ").strip()

    analysis_types = []
    if choice == '1':
        analysis_types = ['overview']
    elif choice == '2':
        analysis_types = ['overview', 'technical_depth']
    else:
        analysis_types = ['overview', 'technical_depth', 'skills']

    # Run batch analysis
    analyzer = AIProjectAnalyzer()
    project_ids = [p.id for p in projects]
    results = analyzer.batch_analyze_projects(project_ids, analysis_types)

    # Offer to update database
    if 'overview' in analysis_types:
        update = input("\n💾 Update all projects in database with AI descriptions? (yes/no): ").strip().lower()
        if update == 'yes':
            updated = 0
            for result in results:
                if 'error' not in result and 'overview' in result:
                    if analyzer.update_database_with_analysis(result['project_id'], result):
                        updated += 1
            print(f"✅ Updated {updated} projects in database")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        if sys.argv[1] == '--batch':
            batch_analyze_all_projects()
        elif sys.argv[1] == '--project' and len(sys.argv) > 2:
            analyzer = AIProjectAnalyzer()
            results = analyzer.analyze_project_complete(int(sys.argv[2]))
            print(json.dumps(results, indent=2))
        else:
            print("Usage:")
            print("  python ai_project_analyzer.py              # Interactive single project")
            print("  python ai_project_analyzer.py --batch      # Batch analyze all")
            print("  python ai_project_analyzer.py --project ID # Analyze specific project")
    else:
        analyze_single_project_cli()