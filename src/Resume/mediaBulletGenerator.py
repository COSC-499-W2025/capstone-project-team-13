"""
Generates professional resume bullet points for visual media projects
based on project analysis data from the database.

Features:
- Converts visual media project data into achievement-focused bullet points
- Generates 10 different bullet types and scores them
- Returns top N bullets based on scoring (supports 2-5 bullets)
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
        'development': ['Developed', 'Created', 'Built', 'Generated', 'Established'],
        'collaboration': ['Coordinated', 'Facilitated', 'Led', 'Managed', 'Directed'],
        'delivery': ['Delivered', 'Completed', 'Finalized', 'Published', 'Released']
    }
    
    # Technical keywords for scoring (media-specific)
    TECHNICAL_KEYWORDS = [
        'Photoshop', 'Illustrator', 'InDesign', 'After Effects', 'Premiere', 'Figma', 'Sketch',
        'Blender', 'Maya', 'Cinema 4D', 'Unity', 'Unreal',
        'UI', 'UX', '3D', 'animation', 'video', 'motion graphics', 'branding', 'typography',
        'vector', 'raster', 'rendering', 'compositing', 'editing'
    ]
    
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
    
    def _select_action_verb(self, project: Project, used_verbs: List[str], category: str = 'creative') -> str:
        """
        Select an appropriate action verb based on category
        
        Args:
            project: Project object
            used_verbs: List of already used verbs to avoid repetition
            category: Verb category to select from
            
        Returns:
            Selected action verb
        """
        # Get available verbs for this category
        available_verbs = [v for v in self.ACTION_VERBS[category] if v not in used_verbs]
        
        # If all verbs used, reset and use category verbs
        if not available_verbs:
            available_verbs = self.ACTION_VERBS[category]
        
        return available_verbs[0]
    
    def _score_bullet(self, bullet: str, project: Project) -> float:
        """
        Score a bullet point from 0.0 to 1.0 based on quality metrics
        
        Scoring criteria:
        - Has metrics/numbers (25%)
        - Contains technical keywords (25%)
        - Appropriate length 10-20 words (25%)
        - Strong action verb (25%)
        
        Args:
            bullet: Bullet text to score
            project: Project object for context
            
        Returns:
            Score from 0.0 to 1.0
        """
        score = 0.0
        
        # Check for metrics (25%)
        if any(char.isdigit() for char in bullet):
            score += 0.25
        
        # Check for technical keywords (25%)
        bullet_lower = bullet.lower()
        keyword_count = sum(1 for keyword in self.TECHNICAL_KEYWORDS if keyword.lower() in bullet_lower)
        if keyword_count >= 3:
            score += 0.25
        elif keyword_count >= 1:
            score += 0.15
        
        # Check length (25%)
        words = len(bullet.split())
        if 10 <= words <= 20:
            score += 0.25
        elif 8 <= words <= 22:
            score += 0.15
        
        # Check action verb (25%)
        first_word = bullet.split()[0] if bullet else ""
        all_strong_verbs = [verb for verbs in self.ACTION_VERBS.values() for verb in verbs]
        if first_word in all_strong_verbs:
            score += 0.25
        
        return score
    
    def _generate_main_description_bullet(self, project: Project, used_verbs: List[str]) -> str:
        """
        Generate the main description bullet for visual media project
        
        Args:
            project: Project object
            used_verbs: List of already used verbs
            
        Returns:
            Main description bullet point
        """
        action_verb = self._select_action_verb(project, used_verbs, 'creative')
        
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
        
        action_verb = self._select_action_verb(project, used_verbs, 'creative')
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
        
        action_verb = self._select_action_verb(project, used_verbs, 'creative')
        
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
    
    def _generate_software_mastery_bullet(self, project: Project, used_verbs: List[str]) -> Optional[str]:
        """
        Generate a bullet point highlighting software tool mastery
        
        Args:
            project: Project object
            used_verbs: List of already used action verbs
            
        Returns:
            Software-focused bullet point or None
        """
        if not project.languages or len(project.languages) < 2:
            return None
        
        action_verb = self._select_action_verb(project, used_verbs, 'creative')
        
        # Get top software tools (limit to 3)
        top_software = project.languages[:3]
        
        # Format software list
        if len(top_software) == 2:
            software_text = f"{top_software[0]} and {top_software[1]}"
        else:
            software_text = f"{', '.join(top_software[:-1])}, and {top_software[-1]}"
        
        return f"{action_verb} professional-grade assets using {software_text} to meet industry standards"
    
    def _generate_collaboration_bullet(self, project: Project, used_verbs: List[str]) -> Optional[str]:
        """
        Generate a bullet point highlighting collaboration and teamwork
        
        Args:
            project: Project object
            used_verbs: List of already used action verbs
            
        Returns:
            Collaboration-focused bullet point or None
        """
        contributors = self.db.get_contributors_for_project(project.id)
        
        # Only generate if there are multiple contributors
        if len(contributors) <= 1:
            return None
        
        action_verb = self._select_action_verb(project, used_verbs, 'collaboration')
        
        # Get primary software
        software = "creative projects"
        if project.languages:
            software = f"{project.languages[0]} projects"
        
        return f"{action_verb} with {len(contributors)}-person creative team on {software}, ensuring brand consistency"
    
    def _generate_design_process_bullet(self, project: Project, used_verbs: List[str]) -> Optional[str]:
        """
        Generate a bullet point highlighting design process/workflow
        
        Args:
            project: Project object
            used_verbs: List of already used action verbs
            
        Returns:
            Process-focused bullet point or None
        """
        # Look for design process-related skills
        process_keywords = ['branding', 'ui', 'ux', 'design system', 'style guide', 'typography', 'layout']
        
        if not project.skills:
            return None
        
        relevant_skills = [skill for skill in project.skills 
                          if any(keyword in skill.lower() for keyword in process_keywords)]
        
        if not relevant_skills:
            return None
        
        action_verb = self._select_action_verb(project, used_verbs, 'design')
        
        # Build process description
        process_desc = "following design best practices"
        if any('ui' in skill.lower() or 'ux' in skill.lower() for skill in relevant_skills):
            process_desc = "applying user-centered design principles"
        elif any('brand' in skill.lower() for skill in relevant_skills):
            process_desc = "maintaining brand identity guidelines"
        elif any('typography' in skill.lower() or 'layout' in skill.lower() for skill in relevant_skills):
            process_desc = "implementing strong visual hierarchy"
        
        return f"{action_verb} creative assets {process_desc} to ensure cohesive visual communication"
    
    def _generate_technical_complexity_bullet(self, project: Project, used_verbs: List[str]) -> Optional[str]:
        """
        Generate a bullet point showcasing technical complexity
        
        Args:
            project: Project object
            used_verbs: List of already used action verbs
            
        Returns:
            Technical complexity-focused bullet point or None
        """
        # Look for advanced technical concepts
        advanced_skills = ['3d', 'animation', 'motion graphics', 'rendering', 'compositing', 
                          'video editing', 'color grading', 'visual effects']
        
        if not project.skills:
            return None
        
        relevant_skills = [skill for skill in project.skills[:3]
                          if any(keyword in skill.lower() for keyword in advanced_skills)]
        
        if len(relevant_skills) < 2:
            return None
        
        action_verb = self._select_action_verb(project, used_verbs, 'creative')
        
        skills_text = ' and '.join(relevant_skills[:2])
        return f"{action_verb} advanced {skills_text} to create visually striking and polished content"
    
    def _generate_portfolio_impact_bullet(self, project: Project, used_verbs: List[str]) -> Optional[str]:
        """
        Generate a bullet point about portfolio impact and quality
        
        Args:
            project: Project object
            used_verbs: List of already used action verbs
            
        Returns:
            Impact-focused bullet point or None
        """
        # Check if we have enough assets to make an impact statement
        if not project.file_count or project.file_count < 5:
            return None
        
        action_verb = self._select_action_verb(project, used_verbs, 'delivery')
        
        # Build impact statement based on project type
        impact = "production-ready visual content"
        if project.skills:
            if any('ui' in skill.lower() or 'ux' in skill.lower() for skill in project.skills):
                impact = "user interface designs for web and mobile platforms"
            elif any('3d' in skill.lower() for skill in project.skills):
                impact = "3D models and rendered assets for digital media"
            elif any('video' in skill.lower() or 'motion' in skill.lower() for skill in project.skills):
                impact = "motion graphics and video content for marketing"
            elif any('brand' in skill.lower() for skill in project.skills):
                impact = "brand identity materials across multiple touchpoints"
        
        return f"{action_verb} {impact} meeting client specifications and industry standards"
    
    def _generate_creative_innovation_bullet(self, project: Project, used_verbs: List[str]) -> Optional[str]:
        """
        Generate a bullet point highlighting creative innovation
        
        Args:
            project: Project object
            used_verbs: List of already used action verbs
            
        Returns:
            Innovation-focused bullet point or None
        """
        # Look for modern/cutting-edge tools and techniques
        modern_tools = ['Figma', 'Sketch', 'Adobe XD', 'Cinema 4D', 'Blender', 'Unreal', 'Unity']
        
        found_tools = []
        if project.languages:
            found_tools = [tool for tool in project.languages if tool in modern_tools]
        
        if not found_tools:
            return None
        
        action_verb = self._select_action_verb(project, used_verbs, 'design')
        
        tools_text = ' and '.join(found_tools[:2])
        return f"{action_verb} innovative visual solutions using {tools_text} to achieve modern aesthetic appeal"
    
    def _generate_delivery_quality_bullet(self, project: Project, used_verbs: List[str]) -> Optional[str]:
        """
        Generate a bullet point about delivery and quality standards
        
        Args:
            project: Project object
            used_verbs: List of already used action verbs
            
        Returns:
            Delivery-focused bullet point or None
        """
        # Need some measurable output
        has_measurable = (project.file_count and project.file_count >= 5) or \
                        (project.total_size_bytes and project.total_size_bytes >= 50 * 1024 * 1024)
        
        if not has_measurable:
            return None
        
        action_verb = self._select_action_verb(project, used_verbs, 'delivery')
        
        # Build quality statement
        quality_aspect = "professional standards"
        if project.skills:
            if any('typography' in skill.lower() for skill in project.skills):
                quality_aspect = "meticulous attention to typography and layout"
            elif any('color' in skill.lower() for skill in project.skills):
                quality_aspect = "strong color theory and visual balance"
            else:
                quality_aspect = "high-quality execution and attention to detail"
        
        return f"{action_verb} polished deliverables with {quality_aspect} for client satisfaction"
    
    def generate_resume_bullets(self, project: Project, num_bullets: int = 3) -> List[str]:
        """
        Generate resume bullet points for a visual media project
        
        NEW APPROACH:
        1. Generate ALL possible bullet types (9 types)
        2. Score each bullet
        3. Return top N bullets based on scores
        
        Args:
            project: Project object from database
            num_bullets: Number of bullets to generate (2-5)
            
        Returns:
            List of top N formatted bullet points
        """
        used_verbs = []
        all_bullets_with_scores = []
        
        # Generate all bullet types
        bullet_generators = [
            ('main', self._generate_main_description_bullet),
            ('scale', self._generate_scale_bullet),
            ('skills', self._generate_skills_bullet),
            ('software_mastery', self._generate_software_mastery_bullet),
            ('collaboration', self._generate_collaboration_bullet),
            ('design_process', self._generate_design_process_bullet),
            ('technical_complexity', self._generate_technical_complexity_bullet),
            ('portfolio_impact', self._generate_portfolio_impact_bullet),
            ('creative_innovation', self._generate_creative_innovation_bullet),
            ('delivery_quality', self._generate_delivery_quality_bullet)
        ]
        
        for bullet_type, generator in bullet_generators:
            bullet = generator(project, used_verbs)
            if bullet:
                score = self._score_bullet(bullet, project)
                all_bullets_with_scores.append((bullet, score, bullet_type))
                
                # Track used verb to encourage variety
                first_word = bullet.split()[0] if bullet else ""
                if first_word:
                    used_verbs.append(first_word)
        
        # Sort by score (descending)
        all_bullets_with_scores.sort(key=lambda x: x[1], reverse=True)
        
        # Return top N bullets
        top_bullets = [bullet for bullet, score, bullet_type in all_bullets_with_scores[:num_bullets]]
        
        # If we still don't have enough bullets (rare), add a generic one
        if len(top_bullets) < num_bullets and project.languages:
            generic = f"Leveraged {project.languages[0]} to produce professional-grade visual content"
            top_bullets.append(generic)
        
        return top_bullets
    
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
            num_bullets: Number of bullets to generate (2-5)
            
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
        
        # Test with different bullet counts
        for num in [3, 5]:
            print(f"\n{'='*70}")
            print(f"Testing with {num} bullets:")
            print('='*70)
            
            generator = MediaBulletGenerator()
            result = generator.generate_bullets_for_project(media_projects[0].id, num_bullets=num)
            
            if result['success']:
                print("Generated Resume Component:")
                print("-" * 70)
                print(result['formatted_component'])
                print("-" * 70)
            else:
                print(f"Error: {result['error']}")