"""
Generates professional resume bullet points for coding projects
based on project analysis data from the database.

Features:
- Converts coding project data into achievement-focused bullet points
- Includes quantifiable metrics (lines of code, file count, team size)
- Highlights programming languages, frameworks, and technical skills
- Formats bullets in professional resume style
"""

import os
import sys
from typing import List, Dict, Any, Optional

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.Databases.database import db_manager, Project


class CodeBulletGenerator:
    """Generate professional resume bullets for coding projects"""
    
    # Action verbs for coding projects
    ACTION_VERBS = {
        'development': ['Developed', 'Built', 'Created', 'Engineered', 'Implemented'],
        'improvement': ['Enhanced', 'Optimized', 'Improved', 'Refactored', 'Upgraded'],
        'design': ['Designed', 'Architected', 'Structured', 'Planned', 'Modeled'],
        'integration': ['Integrated', 'Connected', 'Linked', 'Interfaced', 'Combined'],
        'testing': ['Tested', 'Validated', 'Verified', 'Debugged', 'Troubleshot'],
        'deployment': ['Deployed', 'Released', 'Launched', 'Delivered', 'Published']
    }
    
    # Impact phrases for different metrics
    IMPACT_PHRASES = {
        'scale': ['managing', 'processing', 'handling', 'supporting'],
        'efficiency': ['reducing', 'improving', 'optimizing', 'streamlining'],
        'quality': ['ensuring', 'maintaining', 'achieving', 'delivering'],
        'collaboration': ['collaborating with', 'working alongside', 'partnering with']
    }
    
    def __init__(self):
        """Initialize the code bullet generator"""
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
        
        # Add primary frameworks first
        if project.frameworks:
            tech_stack.extend(project.frameworks[:2])  # Limit to top 2 frameworks
        
        # Add primary languages
        if project.languages:
            # Filter out markup languages for cleaner tech stack
            code_languages = [lang for lang in project.languages 
                            if lang not in ['HTML', 'CSS']]
            tech_stack.extend(code_languages[:2])  # Limit to top 2 languages
        
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
        # Determine project category based on available data
        if project.frameworks or project.languages:
            category = 'development'
        elif project.lines_of_code and project.lines_of_code > 5000:
            category = 'design'
        else:
            category = 'development'
        
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
    
    def generate_resume_bullets(self, project: Project, num_bullets: int = 3) -> List[str]:
        """
        Generate resume bullet points for a coding project
        
        Args:
            project: Project object from database
            num_bullets: Number of bullets to generate (default: 3)
            
        Returns:
            List of formatted bullet points
        """
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
    
    def format_resume_component(self, project: Project, num_bullets: int = 3) -> str:
        """
        Generate a complete formatted resume component for a coding project
        
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
        Generate resume bullets for a coding project (does not store in database)
        
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
        
        # Verify it's a coding project
        if project.project_type != 'code':
            return {
                'success': False,
                'error': f'Project {project_id} is not a coding project (type: {project.project_type})'
            }
        
        # Generate bullets
        bullets = self.generate_resume_bullets(project, num_bullets)
        header = self.generate_project_header(project)
        
        return {
            'success': True,
            'project_id': project_id,
            'project_type': 'code',
            'header': header,
            'bullets': bullets,
            'formatted_component': self.format_resume_component(project, num_bullets)
        }


if __name__ == "__main__":
    # Example usage
    print("Code Resume Bullet Generator")
    print("=" * 70)
    
    # Get all coding projects
    projects = db_manager.get_all_projects()
    coding_projects = [p for p in projects if p.project_type == 'code']
    
    if not coding_projects:
        print("No coding projects found in database.")
    else:
        print(f"Found {len(coding_projects)} coding project(s)\n")
        
        # Generate bullets for first project as example
        generator = CodeBulletGenerator()
        result = generator.generate_bullets_for_project(coding_projects[0].id, num_bullets=3)
        
        if result['success']:
            print("Generated Resume Component:")
            print("-" * 70)
            print(result['formatted_component'])
            print("-" * 70)
        else:
            print(f"Error: {result['error']}")