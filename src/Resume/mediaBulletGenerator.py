"""
Generates professional resume bullet points for visual media projects
based on project analysis data from the database.

Features:
- Converts visual media project data into achievement-focused bullet points
- Includes quantifiable metrics (file count, GB/MB size, asset count)
- Highlights design software, creative skills, and visual tools
- Formats bullets in professional resume style
"""

import os
import sys
from typing import List, Dict, Any, Optional

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.Databases.database import db_manager, Project


class MediaBulletGenerator:
    """Generate professional resume bullets for visual media projects"""
    
    # Action verbs for creative/media projects
    ACTION_VERBS = {
        'creative': ['Produced', 'Crafted', 'Illustrated', 'Animated', 'Rendered'],
        'design': ['Designed', 'Architected', 'Conceptualized', 'Styled', 'Composed'],
        'development': ['Developed', 'Created', 'Built', 'Generated', 'Established']
    }
    
    # Impact phrases for creative metrics
    IMPACT_PHRASES = {
        'quality': ['professional-grade', 'high-quality', 'polished', 'production-ready'],
        'consistency': ['consistent', 'cohesive', 'unified', 'harmonious'],
        'impact': ['engaging', 'compelling', 'impactful', 'striking']
    }
    
    def __init__(self):
        """Initialize the media bullet generator"""
        self.db = db_manager
    
    def generate_project_header(self, project: Project) -> str:
        """
        Generate the project header line with name and software tools
        
        Args:
            project: Project object from database
            
        Returns:
            Formatted header string (e.g., "Brand Identity Design | Adobe Illustrator, Photoshop")
        """
        tech_stack = []
        
        # For media projects, languages field contains software used
        if project.languages:  # Software tools
            tech_stack.extend(project.languages[:3])  # Top 3 tools
        
        # Format tech stack
        tech_string = ', '.join(tech_stack) if tech_stack else 'Digital Media'
        
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
        # Default to creative verbs for media projects
        category = 'creative'
        
        # Get available verbs for this category
        available_verbs = [v for v in self.ACTION_VERBS[category] if v not in used_verbs]
        
        # If all verbs used, try design category
        if not available_verbs:
            category = 'design'
            available_verbs = [v for v in self.ACTION_VERBS[category] if v not in used_verbs]
        
        # If still none, reset to creative
        if not available_verbs:
            available_verbs = self.ACTION_VERBS['creative']
        
        return available_verbs[0]
    
    def _generate_main_description_bullet(self, project: Project) -> str:
        """
        Generate the main description bullet for visual media project
        
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
    
    def _generate_scale_bullet(self, project: Project, used_verbs: List[str]) -> Optional[str]:
        """
        Generate a bullet point highlighting scale/scope for media projects
        
        Args:
            project: Project object
            used_verbs: List of already used action verbs
            
        Returns:
            Scale-focused bullet point or None
        """
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
    
    def _generate_skills_bullet(self, project: Project, used_verbs: List[str]) -> Optional[str]:
        """
        Generate a bullet point highlighting creative skills
        
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
        
        return f"{action_verb} using {skills_text} to deliver visually compelling and engaging content"
    
    def generate_resume_bullets(self, project: Project, num_bullets: int = 3) -> List[str]:
        """
        Generate resume bullet points for a visual media project
        
        Args:
            project: Project object from database
            num_bullets: Number of bullets to generate (default: 3)
            
        Returns:
            List of formatted bullet points
        """
        bullets = []
        used_verbs = []
        
        # Main description bullet
        main_bullet = self._generate_main_description_bullet(project)
        bullets.append(main_bullet)
        used_verbs.append(main_bullet.split()[0])
        
        # Scale bullet
        scale_bullet = self._generate_scale_bullet(project, used_verbs)
        if scale_bullet:
            bullets.append(scale_bullet)
            used_verbs.append(scale_bullet.split()[0])
        
        # Skills bullet
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
    
    def format_resume_component(self, project: Project, num_bullets: int = 3) -> str:
        """
        Generate a complete formatted resume component for a media project
        
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
        Generate resume bullets for a media project (does not store in database)
        
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
        
        # Verify it's a media project
        if project.project_type != 'visual_media':
            return {
                'success': False,
                'error': f'Project {project_id} is not a media project (type: {project.project_type})'
            }
        
        # Generate bullets
        bullets = self.generate_resume_bullets(project, num_bullets)
        header = self.generate_project_header(project)
        
        return {
            'success': True,
            'project_id': project_id,
            'project_type': 'visual_media',
            'header': header,
            'bullets': bullets,
            'formatted_component': self.format_resume_component(project, num_bullets)
        }


if __name__ == "__main__":
    # Example usage
    print("Media Resume Bullet Generator")
    print("=" * 70)
    
    # Get all media projects
    projects = db_manager.get_all_projects()
    media_projects = [p for p in projects if p.project_type == 'visual_media']
    
    if not media_projects:
        print("No media projects found in database.")
    else:
        print(f"Found {len(media_projects)} media project(s)\n")
        
        # Generate bullets for first project as example
        generator = MediaBulletGenerator()
        result = generator.generate_bullets_for_project(media_projects[0].id, num_bullets=3)
        
        if result['success']:
            print("Generated Resume Component:")
            print("-" * 70)
            print(result['formatted_component'])
            print("-" * 70)
        else:
            print(f"Error: {result['error']}")