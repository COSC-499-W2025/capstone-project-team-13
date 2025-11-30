"""
Generates professional resume bullet points for text/document projects
based on project analysis data from the database.

Features:
- Converts text project data into achievement-focused bullet points
- Includes quantifiable metrics (word count, document count)
- Highlights writing skills, document types, and research abilities
- Formats bullets in professional resume style
"""

import os
import sys
from typing import List, Dict, Any, Optional

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.Databases.database import db_manager, Project


class TextBulletGenerator:
    """Generate professional resume bullets for text/document projects"""
    
    # Action verbs for writing/documentation projects
    ACTION_VERBS = {
        'writing': ['Authored', 'Composed', 'Drafted', 'Published', 'Documented'],
        'research': ['Researched', 'Analyzed', 'Investigated', 'Compiled', 'Synthesized'],
        'editing': ['Edited', 'Refined', 'Revised', 'Polished', 'Curated']
    }
    
    # Impact phrases for writing metrics
    IMPACT_PHRASES = {
        'clarity': ['clear', 'concise', 'accessible', 'readable'],
        'depth': ['comprehensive', 'detailed', 'thorough', 'in-depth'],
        'impact': ['engaging', 'compelling', 'informative', 'insightful']
    }
    
    def __init__(self):
        """Initialize the text bullet generator"""
        self.db = db_manager
    
    def generate_project_header(self, project: Project) -> str:
        """
        Generate the project header line with name and document types
        
        Args:
            project: Project object from database
            
        Returns:
            Formatted header string (e.g., "Technical Documentation | Markdown, PDF")
        """
        tech_stack = []
        
        # For text projects, show document types from tags
        if project.tags:
            tech_stack.extend(project.tags[:2])  # Top 2 document types
        
        # Add "Writing" if no tags
        if not tech_stack:
            tech_stack.append('Writing')
        
        # Format tech stack
        tech_string = ', '.join(tech_stack) if tech_stack else 'Documentation'
        
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
        # Default to writing verbs for text projects
        category = 'writing'
        
        # Get available verbs for this category
        available_verbs = [v for v in self.ACTION_VERBS[category] if v not in used_verbs]
        
        # If all verbs used, try research category
        if not available_verbs:
            category = 'research'
            available_verbs = [v for v in self.ACTION_VERBS[category] if v not in used_verbs]
        
        # If still none, reset to writing
        if not available_verbs:
            available_verbs = self.ACTION_VERBS['writing']
        
        return available_verbs[0]
    
    def _generate_main_description_bullet(self, project: Project) -> str:
        """
        Generate the main description bullet for text/document project
        
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
    
    def _generate_scale_bullet(self, project: Project, used_verbs: List[str]) -> Optional[str]:
        """
        Generate a bullet point highlighting scale/scope for text projects
        
        Args:
            project: Project object
            used_verbs: List of already used action verbs
            
        Returns:
            Scale-focused bullet point or None
        """
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
    
    def _generate_skills_bullet(self, project: Project, used_verbs: List[str]) -> Optional[str]:
        """
        Generate a bullet point highlighting writing skills
        
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
        
        return f"{action_verb} using {skills_text.lower()} to deliver clear and engaging content"
    
    def generate_resume_bullets(self, project: Project, num_bullets: int = 3) -> List[str]:
        """
        Generate resume bullet points for a text/document project
        
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
        Generate a complete formatted resume component for a text project
        
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
        Generate resume bullets for a text project (does not store in database)
        
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
        
        # Verify it's a text project
        if project.project_type != 'text':
            return {
                'success': False,
                'error': f'Project {project_id} is not a text project (type: {project.project_type})'
            }
        
        # Generate bullets
        bullets = self.generate_resume_bullets(project, num_bullets)
        header = self.generate_project_header(project)
        
        return {
            'success': True,
            'project_id': project_id,
            'project_type': 'text',
            'header': header,
            'bullets': bullets,
            'formatted_component': self.format_resume_component(project, num_bullets)
        }


if __name__ == "__main__":
    # Example usage
    print("Text Resume Bullet Generator")
    print("=" * 70)
    
    # Get all text projects
    projects = db_manager.get_all_projects()
    text_projects = [p for p in projects if p.project_type == 'text']
    
    if not text_projects:
        print("No text projects found in database.")
    else:
        print(f"Found {len(text_projects)} text project(s)\n")
        
        # Generate bullets for first project as example
        generator = TextBulletGenerator()
        result = generator.generate_bullets_for_project(text_projects[0].id, num_bullets=3)
        
        if result['success']:
            print("Generated Resume Component:")
            print("-" * 70)
            print(result['formatted_component'])
            print("-" * 70)
        else:
            print(f"Error: {result['error']}")