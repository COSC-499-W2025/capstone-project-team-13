"""
Generates professional resume bullet points for all project types
based on project analysis data from the database.

Supported Project Types:
- Coding Projects (languages, frameworks, LOC, files)
- Visual Media Projects (design software, skills, file count)
- Text/Document Projects (writing skills, word count, documents)

Features:
- Converts project data into achievement-focused bullet points
- Includes quantifiable metrics appropriate to each project type
- Formats bullets in professional resume style
- Supports multiple bullet generation strategies
"""

import os
import sys
import re
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timezone

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.Databases.database import db_manager, Project


class ResumeBulletGenerator:
    """Generate professional resume bullets for all project types"""
    
    # Action verbs for different project types
    ACTION_VERBS = {
        'development': ['Developed', 'Built', 'Created', 'Engineered', 'Implemented'],
        'improvement': ['Enhanced', 'Optimized', 'Improved', 'Refactored', 'Upgraded'],
        'design': ['Designed', 'Architected', 'Structured', 'Planned', 'Modeled'],
        'integration': ['Integrated', 'Connected', 'Linked', 'Interfaced', 'Combined'],
        'testing': ['Tested', 'Validated', 'Verified', 'Debugged', 'Troubleshot'],
        'deployment': ['Deployed', 'Released', 'Launched', 'Delivered', 'Published'],
        'creative': ['Produced', 'Crafted', 'Illustrated', 'Animated', 'Rendered'],
        'writing': ['Authored', 'Composed', 'Drafted', 'Published', 'Documented']
    }
    
    # Impact phrases for different metrics
    IMPACT_PHRASES = {
        'scale': ['managing', 'processing', 'handling', 'supporting'],
        'efficiency': ['reducing', 'improving', 'optimizing', 'streamlining'],
        'quality': ['ensuring', 'maintaining', 'achieving', 'delivering'],
        'collaboration': ['collaborating with', 'working alongside', 'partnering with']
    }
    
    def __init__(self):
        """Initialize the resume bullet generator"""
        self.db = db_manager
    
    def generate_project_header(self, project: Project) -> str:
        """
        Generate the project header line with name and tech stack
        
        Args:
            project: Project object from database
            
        Returns:
            Formatted header string (e.g., "PacMan Ghost Hunter | Unity, C#")
        """
        tech_stack = []
        
        # Handle different project types
        if project.project_type == 'code':
            # Add primary frameworks first
            if project.frameworks:
                tech_stack.extend(project.frameworks[:2])  # Limit to top 2 frameworks
            
            # Add primary languages
            if project.languages:
                # Filter out markup languages for cleaner tech stack
                code_languages = [lang for lang in project.languages 
                                if lang not in ['HTML', 'CSS']]
                tech_stack.extend(code_languages[:2])  # Limit to top 2 languages
        
        elif project.project_type == 'visual_media':
            # For media projects, languages field contains software used
            if project.languages:  # Software tools
                tech_stack.extend(project.languages[:3])  # Top 3 tools
        
        elif project.project_type == 'text':
            # For text projects, show document types from tags
            if project.tags:
                tech_stack.extend(project.tags[:2])  # Top 2 document types
            # Add "Writing" if no tags
            if not tech_stack:
                tech_stack.append('Writing')
        
        # Format tech stack
        tech_string = ', '.join(tech_stack) if tech_stack else 'Multiple Technologies'
        
        return f"{project.name} | {tech_string}"
    
    def _select_action_verb(self, project: Project, used_verbs: List[str]) -> str:
        """
        Select an appropriate action verb based on project characteristics
        
        Args:
            project: Project object
            used_verbs: List of already used verbs to avoid repetition
            
        Returns:
            Selected action verb
        """
        # Determine project category based on type
        if project.project_type == 'code':
            if project.frameworks or project.languages:
                category = 'development'
            elif project.lines_of_code and project.lines_of_code > 5000:
                category = 'design'
            else:
                category = 'development'
        
        elif project.project_type == 'visual_media':
            category = 'creative'
        
        elif project.project_type == 'text':
            category = 'writing'
        
        else:
            category = 'development'  # Default fallback
        
        # Get available verbs for this category
        available_verbs = [v for v in self.ACTION_VERBS[category] if v not in used_verbs]
        
        # If all verbs used, reset and use category verbs
        if not available_verbs:
            available_verbs = self.ACTION_VERBS[category]
        
        return available_verbs[0]
    
    def _generate_main_description_bullet(self, project: Project) -> str:
        """
        Generate the main description bullet describing what was built
        
        Args:
            project: Project object
            
        Returns:
            Main description bullet point
        """
        action_verb = self._select_action_verb(project, [])
        
        # Use custom description if available
        if project.custom_description:
            description = project.custom_description
        elif project.description:
            description = project.description
        else:
            # Generate description based on tech stack
            tech_desc = self._generate_tech_description(project)
            description = f"a {tech_desc} application"
        
        # Add technical features if available
        features = self._extract_technical_features(project)
        if features:
            feature_text = ', '.join(features[:3])  # Limit to 3 features
            bullet = f"{action_verb} {description} with {feature_text}"
        else:
            bullet = f"{action_verb} {description}"
        
        return bullet
    
    def _generate_tech_description(self, project: Project) -> str:
        """Generate a technical description based on project tech stack"""
        if project.frameworks:
            primary_framework = project.frameworks[0]
            return f"{primary_framework}-based"
        elif project.languages:
            primary_language = project.languages[0]
            return f"{primary_language}"
        else:
            return "software"
    
    def _extract_technical_features(self, project: Project) -> List[str]:
        """
        Extract technical features from project data
        
        Args:
            project: Project object
            
        Returns:
            List of technical feature descriptions
        """
        features = []
        
        # Check for specific technical patterns in skills
        skill_patterns = {
            'API': 'RESTful API integration',
            'Database': 'database management',
            'Authentication': 'user authentication',
            'Testing': 'automated testing',
            'Frontend': 'responsive UI',
            'Backend': 'backend services',
            'Cloud': 'cloud deployment',
            'Mobile': 'mobile compatibility'
        }
        
        if project.skills:
            for skill in project.skills:
                for pattern, feature in skill_patterns.items():
                    if pattern.lower() in skill.lower():
                        features.append(feature)
                        break
        
        # Add features based on frameworks
        if project.frameworks:
            for framework in project.frameworks:
                if framework.lower() in ['react', 'vue', 'angular']:
                    features.append('dynamic user interfaces')
                elif framework.lower() in ['django', 'flask', 'express']:
                    features.append('scalable backend architecture')
        
        return list(set(features))  # Remove duplicates
    
    def _generate_scale_bullet(self, project: Project, used_verbs: List[str]) -> Optional[str]:
        """
        Generate a bullet point highlighting scale/scope
        
        Args:
            project: Project object
            used_verbs: List of already used action verbs
            
        Returns:
            Scale-focused bullet point or None
        """
        metrics = []
        
        # Lines of code metric
        if project.lines_of_code and project.lines_of_code >= 1000:
            loc_formatted = f"{project.lines_of_code:,}"
            metrics.append(f"{loc_formatted}+ lines of code")
        
        # File count metric
        if project.file_count and project.file_count >= 10:
            metrics.append(f"{project.file_count}+ files")
        
        # Contributor metric
        contributors = self.db.get_contributors_for_project(project.id)
        if len(contributors) > 1:
            metrics.append(f"{len(contributors)}-person team")
        
        if not metrics:
            return None
        
        action_verb = self._select_action_verb(project, used_verbs)
        metric_text = ' and '.join(metrics[:2])  # Limit to 2 metrics
        
        # Create impact statement
        if len(contributors) > 1:
            return f"{action_verb} and maintained {metric_text}, demonstrating strong collaboration and code management skills"
        else:
            return f"{action_verb} and maintained {metric_text}, ensuring code quality and project scalability"
    
    def _generate_skills_bullet(self, project: Project, used_verbs: List[str]) -> Optional[str]:
        """
        Generate a bullet point highlighting technical skills applied
        
        Args:
            project: Project object
            used_verbs: List of already used action verbs
            
        Returns:
            Skills-focused bullet point or None
        """
        if not project.skills or len(project.skills) < 2:
            return None
        
        action_verb = self._select_action_verb(project, used_verbs)
        
        # Get top skills (limit to 4)
        top_skills = project.skills[:4]
        
        # Format skills list
        if len(top_skills) == 2:
            skills_text = f"{top_skills[0]} and {top_skills[1]}"
        elif len(top_skills) == 3:
            skills_text = f"{top_skills[0]}, {top_skills[1]}, and {top_skills[2]}"
        else:
            skills_text = f"{', '.join(top_skills[:-1])}, and {top_skills[-1]}"
        
        return f"{action_verb} using {skills_text} to deliver robust and maintainable solutions"
    
    def _generate_impact_bullet(self, project: Project, used_verbs: List[str]) -> Optional[str]:
        """
        Generate a bullet point highlighting project impact or results
        
        Args:
            project: Project object
            used_verbs: List of already used action verbs
            
        Returns:
            Impact-focused bullet point or None
        """
        # Check for success metrics
        if not project.success_metrics:
            return None
        
        action_verb = self._select_action_verb(project, used_verbs)
        metrics = project.success_metrics
        
        # Generate impact statement based on available metrics
        impact_statements = []
        
        if 'users' in metrics or 'user_count' in metrics:
            user_count = metrics.get('users', metrics.get('user_count', 0))
            impact_statements.append(f"supporting {user_count}+ users")
        
        if 'performance_improvement' in metrics:
            improvement = metrics['performance_improvement']
            impact_statements.append(f"improving performance by {improvement}%")
        
        if 'success_rate' in metrics:
            rate = metrics['success_rate']
            impact_statements.append(f"achieving {rate}% success rate")
        
        if not impact_statements:
            return None
        
        impact_text = ' and '.join(impact_statements[:2])
        return f"{action_verb} {impact_text}"
    
    # ============================================
    # VISUAL MEDIA PROJECT BULLETS
    # ============================================
    
    def _generate_media_main_bullet(self, project: Project) -> str:
        """Generate main description bullet for visual media projects"""
        action_verb = self._select_action_verb(project, [])
        
        # Use custom description if available
        if project.custom_description:
            description = project.custom_description
        elif project.description:
            description = project.description
        else:
            # Generate description based on software/skills
            if project.languages:  # Software tools stored in languages field
                software = project.languages[0]
                description = f"visual content using {software}"
            else:
                description = "visual media assets"
        
        # Add skills if available
        if project.skills and len(project.skills) >= 2:
            skills_text = ' and '.join(project.skills[:2])
            bullet = f"{action_verb} {description}, demonstrating expertise in {skills_text}"
        else:
            bullet = f"{action_verb} {description}"
        
        return bullet
    
    def _generate_media_scale_bullet(self, project: Project, used_verbs: List[str]) -> Optional[str]:
        """Generate scale bullet for visual media projects"""
        metrics = []
        
        # File count metric
        if project.file_count and project.file_count >= 10:
            metrics.append(f"{project.file_count}+ assets")
        
        # Size metric
        if project.total_size_bytes and project.total_size_bytes >= 100 * 1024 * 1024:  # 100 MB
            size_mb = project.total_size_bytes / (1024 * 1024)
            if size_mb >= 1024:  # Show in GB
                metrics.append(f"{size_mb/1024:.1f} GB of content")
            else:
                metrics.append(f"{size_mb:.0f} MB of content")
        
        # Contributors
        contributors = self.db.get_contributors_for_project(project.id)
        if len(contributors) > 1:
            metrics.append(f"{len(contributors)}-person creative team")
        
        if not metrics:
            return None
        
        action_verb = self._select_action_verb(project, used_verbs)
        metric_text = ' and '.join(metrics[:2])
        
        return f"{action_verb} {metric_text} with consistent quality and professional standards"
    
    # ============================================
    # TEXT/DOCUMENT PROJECT BULLETS
    # ============================================
    
    def _generate_text_main_bullet(self, project: Project) -> str:
        """Generate main description bullet for text/document projects"""
        action_verb = self._select_action_verb(project, [])
        
        # Use custom description if available
        if project.custom_description:
            description = project.custom_description
        elif project.description:
            description = project.description
        else:
            # Generate description based on document types
            if project.tags:
                doc_types = ' and '.join(project.tags[:2])
                description = f"comprehensive {doc_types} documentation"
            else:
                description = "written content"
        
        # Add skills if available
        if project.skills and len(project.skills) >= 2:
            skills_text = ' and '.join(project.skills[:2])
            bullet = f"{action_verb} {description}, applying {skills_text.lower()}"
        else:
            bullet = f"{action_verb} {description}"
        
        return bullet
    
    def _generate_text_scale_bullet(self, project: Project, used_verbs: List[str]) -> Optional[str]:
        """Generate scale bullet for text/document projects"""
        metrics = []
        
        # Word count metric
        if project.word_count and project.word_count >= 1000:
            if project.word_count >= 10000:
                metrics.append(f"{project.word_count//1000}K+ words")
            else:
                metrics.append(f"{project.word_count:,}+ words")
        
        # Document count metric
        if project.file_count and project.file_count >= 5:
            metrics.append(f"{project.file_count}+ documents")
        
        # Contributors
        contributors = self.db.get_contributors_for_project(project.id)
        if len(contributors) > 1:
            metrics.append(f"{len(contributors)}-person writing team")
        
        if not metrics:
            return None
        
        action_verb = self._select_action_verb(project, used_verbs)
        metric_text = ' and '.join(metrics[:2])
        
        return f"{action_verb} {metric_text}, ensuring clarity and consistency across all materials"
    
    def generate_resume_bullets(self, project: Project, num_bullets: int = 3) -> List[str]:
        """
        Generate resume bullet points for a project (any type)
        
        Args:
            project: Project object from database
            num_bullets: Number of bullets to generate (default: 3)
            
        Returns:
            List of formatted bullet points
        """
        bullets = []
        used_verbs = []
        
        # Route to appropriate generator based on project type
        if project.project_type == 'visual_media':
            return self._generate_media_bullets(project, num_bullets)
        elif project.project_type == 'text':
            return self._generate_text_bullets(project, num_bullets)
        else:
            # Default to coding project logic
            return self._generate_code_bullets(project, num_bullets)
    
    def _generate_code_bullets(self, project: Project, num_bullets: int) -> List[str]:
        """Generate bullets specifically for coding projects"""
        bullets = []
        used_verbs = []
        
        # Always generate main description bullet
        main_bullet = self._generate_main_description_bullet(project)
        bullets.append(main_bullet)
        used_verbs.append(main_bullet.split()[0])
        
        # Generate additional bullets based on available data
        potential_bullets = []
        
        # Try to generate scale bullet
        scale_bullet = self._generate_scale_bullet(project, used_verbs)
        if scale_bullet:
            potential_bullets.append((scale_bullet, 'scale'))
            used_verbs.append(scale_bullet.split()[0])
        
        # Try to generate skills bullet
        skills_bullet = self._generate_skills_bullet(project, used_verbs)
        if skills_bullet:
            potential_bullets.append((skills_bullet, 'skills'))
            used_verbs.append(skills_bullet.split()[0])
        
        # Try to generate impact bullet
        impact_bullet = self._generate_impact_bullet(project, used_verbs)
        if impact_bullet:
            potential_bullets.append((impact_bullet, 'impact'))
        
        # Add bullets up to num_bullets
        for bullet, _ in potential_bullets[:num_bullets - 1]:
            bullets.append(bullet)
        
        # If we don't have enough bullets, generate a generic technical bullet
        while len(bullets) < num_bullets and project.frameworks:
            generic = f"Utilized {project.frameworks[0]} framework to implement efficient and scalable solutions"
            bullets.append(generic)
            break
        
        return bullets
    
    def _generate_media_bullets(self, project: Project, num_bullets: int) -> List[str]:
        """Generate bullets specifically for visual media projects"""
        bullets = []
        used_verbs = []
        
        # Main description bullet
        main_bullet = self._generate_media_main_bullet(project)
        bullets.append(main_bullet)
        used_verbs.append(main_bullet.split()[0])
        
        # Scale bullet
        scale_bullet = self._generate_media_scale_bullet(project, used_verbs)
        if scale_bullet:
            bullets.append(scale_bullet)
            used_verbs.append(scale_bullet.split()[0])
        
        # Skills bullet (reuse from coding, works for media too)
        if len(bullets) < num_bullets:
            skills_bullet = self._generate_skills_bullet(project, used_verbs)
            if skills_bullet:
                bullets.append(skills_bullet)
        
        # Generic software bullet if needed
        while len(bullets) < num_bullets and project.languages:
            software = project.languages[0]
            generic = f"Leveraged {software} to produce professional-grade visual content"
            bullets.append(generic)
            break
        
        return bullets
    
    def _generate_text_bullets(self, project: Project, num_bullets: int) -> List[str]:
        """Generate bullets specifically for text/document projects"""
        bullets = []
        used_verbs = []
        
        # Main description bullet
        main_bullet = self._generate_text_main_bullet(project)
        bullets.append(main_bullet)
        used_verbs.append(main_bullet.split()[0])
        
        # Scale bullet
        scale_bullet = self._generate_text_scale_bullet(project, used_verbs)
        if scale_bullet:
            bullets.append(scale_bullet)
            used_verbs.append(scale_bullet.split()[0])
        
        # Skills bullet (reuse from coding, works for text too)
        if len(bullets) < num_bullets:
            skills_bullet = self._generate_skills_bullet(project, used_verbs)
            if skills_bullet:
                bullets.append(skills_bullet)
        
        # Generic writing bullet if needed
        while len(bullets) < num_bullets:
            if project.tags:
                doc_type = project.tags[0]
                generic = f"Produced clear and engaging {doc_type} content for diverse audiences"
            else:
                generic = "Developed comprehensive written materials with attention to clarity and accuracy"
            bullets.append(generic)
            break
        
        return bullets
    
    def format_resume_component(self, project: Project, num_bullets: int = 3) -> str:
        """
        Generate a complete formatted resume component for a project
        
        Args:
            project: Project object from database
            num_bullets: Number of bullet points to generate
            
        Returns:
            Formatted resume component as string
        """
        header = self.generate_project_header(project)
        bullets = self.generate_resume_bullets(project, num_bullets)
        
        # Format with bullets
        formatted = f"{header}\n"
        for bullet in bullets:
            formatted += f"• {bullet}\n"
        
        return formatted.strip()
    
    def generate_bullets_for_project(self, project_id: int, num_bullets: int = 3) -> Dict[str, Any]:
        """
        Generate resume bullets for a project (does not store in database)
        
        Args:
            project_id: ID of project to generate bullets for
            num_bullets: Number of bullets to generate
            
        Returns:
            Dictionary containing generated component and status
        """
        # Get project from database
        project = self.db.get_project(project_id)
        if not project:
            return {
                'success': False,
                'error': f'Project {project_id} not found'
            }
        
        # Generate bullets
        bullets = self.generate_resume_bullets(project, num_bullets)
        header = self.generate_project_header(project)
        
        return {
            'success': True,
            'project_id': project_id,
            'header': header,
            'bullets': bullets,
            'formatted_component': self.format_resume_component(project, num_bullets)
        }
    
    def batch_generate_bullets(self, project_ids: List[int], num_bullets: int = 3) -> List[Dict[str, Any]]:
        """
        Generate resume bullets for multiple projects
        
        Args:
            project_ids: List of project IDs
            num_bullets: Number of bullets per project
            
        Returns:
            List of results for each project
        """
        results = []
        
        for project_id in project_ids:
            result = self.generate_bullets_for_project(project_id, num_bullets)
            results.append(result)
        
        return results


def generate_resume_bullets_for_all_projects(num_bullets: int = 3) -> List[Dict[str, Any]]:
    """
    Generate resume bullets for all projects in database (all types)
    
    Args:
        num_bullets: Number of bullets per project
        
    Returns:
        List of generated components
    """
    generator = ResumeBulletGenerator()
    projects = db_manager.get_all_projects()
    
    results = []
    for project in projects:
        # Generate for all project types
        result = generator.generate_bullets_for_project(project.id, num_bullets)
        results.append(result)
    
    return results


def print_resume_component(project_id: int, num_bullets: int = 3):
    """
    Generate and print a resume component for a project
    
    Args:
        project_id: Project ID
        num_bullets: Number of bullets to generate
    """
    generator = ResumeBulletGenerator()
    result = generator.generate_bullets_for_project(project_id, num_bullets)
    
    if result['success']:
        print(f"\n{result['formatted_component']}\n")
    else:
        print(f"Error: {result['error']}")


if __name__ == "__main__":
    # Example usage
    print("Resume Bullet Generator - All Project Types")
    print("=" * 70)
    
    # Get all projects
    projects = db_manager.get_all_projects()
    
    if not projects:
        print("No projects found in database.")
    else:
        print(f"Found {len(projects)} project(s)\n")
        
        # Generate bullets for first project of each type as example
        generator = ResumeBulletGenerator()
        
        for project_type in ['code', 'visual_media', 'text']:
            type_projects = [p for p in projects if p.project_type == project_type]
            if type_projects:
                print(f"\n--- {project_type.upper().replace('_', ' ')} PROJECT ---")
                result = generator.generate_bullets_for_project(type_projects[0].id, num_bullets=3)
                
                if result['success']:
                    print(result['formatted_component'])
                    print("-" * 70)