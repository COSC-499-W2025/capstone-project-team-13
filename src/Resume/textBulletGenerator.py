"""
Generates professional resume bullet points for text/document projects
based on project analysis data from the database.

Features:
- Converts text project data into achievement-focused bullet points
- Generates 10 different bullet types and scores them
- Returns top N bullets based on scoring (supports 2-5 bullets)
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
        'editing': ['Edited', 'Refined', 'Revised', 'Polished', 'Curated'],
        'collaboration': ['Coordinated', 'Facilitated', 'Led', 'Managed', 'Directed'],
        'delivery': ['Delivered', 'Completed', 'Produced', 'Generated', 'Created']
    }
    
    # Technical keywords for scoring (writing-specific)
    TECHNICAL_KEYWORDS = [
        'technical writing', 'copywriting', 'content', 'documentation', 'research', 'journalism',
        'SEO', 'editing', 'proofreading', 'grammar', 'storytelling', 'analysis',
        'blog', 'article', 'whitepaper', 'report', 'markdown', 'LaTeX',
        'AP style', 'Chicago style', 'academic writing', 'creative writing'
    ]
    
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
    
    def _select_action_verb(self, project: Project, used_verbs: List[str], category: str = 'writing') -> str:
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
        Generate the main description bullet for text/document project
        
        Args:
            project: Project object
            used_verbs: List of already used verbs
            
        Returns:
            Main description bullet point
        """
        action_verb = self._select_action_verb(project, used_verbs, 'writing')
        
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
        
        action_verb = self._select_action_verb(project, used_verbs, 'writing')
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
        
        action_verb = self._select_action_verb(project, used_verbs, 'writing')
        
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
    
    def _generate_research_depth_bullet(self, project: Project, used_verbs: List[str]) -> Optional[str]:
        """
        Generate a bullet point highlighting research capabilities
        
        Args:
            project: Project object
            used_verbs: List of already used action verbs
            
        Returns:
            Research-focused bullet point or None
        """
        # Look for research-related skills
        research_keywords = ['research', 'analysis', 'data', 'investigation', 'study', 'academic']
        
        if not project.skills:
            return None
        
        relevant_skills = [skill for skill in project.skills 
                          if any(keyword in skill.lower() for keyword in research_keywords)]
        
        if not relevant_skills:
            return None
        
        action_verb = self._select_action_verb(project, used_verbs, 'research')
        
        # Build research description
        research_desc = "primary and secondary sources"
        if any('academic' in skill.lower() for skill in relevant_skills):
            research_desc = "scholarly sources and academic literature"
        elif any('data' in skill.lower() for skill in relevant_skills):
            research_desc = "data-driven insights and statistical analysis"
        
        return f"{action_verb} {research_desc} to support evidence-based conclusions"
    
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
        
        # Get document type
        doc_type = "written materials"
        if project.tags:
            doc_type = f"{project.tags[0]} content"
        
        return f"{action_verb} with {len(contributors)}-person team to produce {doc_type}, ensuring voice consistency"
    
    def _generate_audience_focus_bullet(self, project: Project, used_verbs: List[str]) -> Optional[str]:
        """
        Generate a bullet point highlighting audience targeting
        
        Args:
            project: Project object
            used_verbs: List of already used action verbs
            
        Returns:
            Audience-focused bullet point or None
        """
        # Look for audience-related skills or document types
        audience_keywords = ['audience', 'reader', 'technical', 'accessible', 'SEO', 'engagement']
        
        has_audience_focus = False
        if project.skills:
            has_audience_focus = any(keyword in skill.lower() 
                                   for skill in project.skills 
                                   for keyword in audience_keywords)
        
        if not has_audience_focus and not project.tags:
            return None
        
        action_verb = self._select_action_verb(project, used_verbs, 'writing')
        
        # Build audience description
        audience_type = "diverse audiences"
        if project.skills:
            if any('technical' in skill.lower() for skill in project.skills):
                audience_type = "both technical and non-technical stakeholders"
            elif any('seo' in skill.lower() for skill in project.skills):
                audience_type = "web audiences with SEO-optimized content"
            elif any('academic' in skill.lower() for skill in project.skills):
                audience_type = "scholarly and academic readers"
        
        return f"{action_verb} content tailored for {audience_type}, maximizing comprehension and engagement"
    
    def _generate_editing_quality_bullet(self, project: Project, used_verbs: List[str]) -> Optional[str]:
        """
        Generate a bullet point highlighting editing and quality control
        
        Args:
            project: Project object
            used_verbs: List of already used action verbs
            
        Returns:
            Editing-focused bullet point or None
        """
        # Look for editing-related skills
        editing_keywords = ['editing', 'proofreading', 'revision', 'grammar', 'style', 'clarity']
        
        if not project.skills:
            return None
        
        relevant_skills = [skill for skill in project.skills 
                          if any(keyword in skill.lower() for keyword in editing_keywords)]
        
        if not relevant_skills:
            return None
        
        action_verb = self._select_action_verb(project, used_verbs, 'editing')
        
        # Build quality description
        quality_aspect = "grammar, style, and clarity"
        if any('ap style' in skill.lower() or 'chicago' in skill.lower() for skill in relevant_skills):
            quality_aspect = "adherence to style guide standards"
        elif any('technical' in skill.lower() for skill in relevant_skills):
            quality_aspect = "technical accuracy and consistency"
        
        return f"{action_verb} all materials for {quality_aspect}, ensuring professional polish"
    
    def _generate_content_strategy_bullet(self, project: Project, used_verbs: List[str]) -> Optional[str]:
        """
        Generate a bullet point about content strategy and planning
        
        Args:
            project: Project object
            used_verbs: List of already used action verbs
            
        Returns:
            Strategy-focused bullet point or None
        """
        # Look for strategic content skills
        strategy_keywords = ['strategy', 'planning', 'seo', 'marketing', 'content management', 'editorial']
        
        if not project.skills:
            return None
        
        relevant_skills = [skill for skill in project.skills 
                          if any(keyword in skill.lower() for keyword in strategy_keywords)]
        
        if not relevant_skills:
            return None
        
        action_verb = self._select_action_verb(project, used_verbs, 'writing')
        
        # Build strategy description
        strategy_desc = "content strategy and editorial planning"
        if any('seo' in skill.lower() for skill in relevant_skills):
            strategy_desc = "SEO-driven content strategy"
        elif any('marketing' in skill.lower() for skill in relevant_skills):
            strategy_desc = "marketing content and brand messaging"
        
        return f"{action_verb} materials aligned with {strategy_desc} to maximize reach and impact"
    
    def _generate_technical_documentation_bullet(self, project: Project, used_verbs: List[str]) -> Optional[str]:
        """
        Generate a bullet point for technical documentation specifically
        
        Args:
            project: Project object
            used_verbs: List of already used action verbs
            
        Returns:
            Technical documentation-focused bullet point or None
        """
        # Look for technical writing indicators
        tech_keywords = ['technical', 'api', 'documentation', 'developer', 'software', 'code']
        
        has_technical_focus = False
        if project.skills:
            has_technical_focus = any(keyword in skill.lower() 
                                    for skill in project.skills 
                                    for keyword in tech_keywords)
        
        if project.tags:
            has_technical_focus = has_technical_focus or any(
                keyword in tag.lower() 
                for tag in project.tags 
                for keyword in tech_keywords
            )
        
        if not has_technical_focus:
            return None
        
        action_verb = self._select_action_verb(project, used_verbs, 'writing')
        
        return f"{action_verb} technical documentation and developer guides, translating complex concepts into accessible instructions"
    
    def _generate_publication_impact_bullet(self, project: Project, used_verbs: List[str]) -> Optional[str]:
        """
        Generate a bullet point about publication and impact
        
        Args:
            project: Project object
            used_verbs: List of already used action verbs
            
        Returns:
            Publication-focused bullet point or None
        """
        # Need measurable output
        has_measurable = (project.word_count and project.word_count >= 2000) or \
                        (project.file_count and project.file_count >= 3)
        
        if not has_measurable:
            return None
        
        action_verb = self._select_action_verb(project, used_verbs, 'delivery')
        
        # Build publication statement
        publication_type = "written materials"
        if project.tags:
            if any('blog' in tag.lower() or 'article' in tag.lower() for tag in project.tags):
                publication_type = "articles and blog posts"
            elif any('report' in tag.lower() or 'whitepaper' in tag.lower() for tag in project.tags):
                publication_type = "reports and whitepapers"
            elif any('documentation' in tag.lower() for tag in project.tags):
                publication_type = "comprehensive documentation"
        
        return f"{action_verb} {publication_type} meeting publication standards and deadline requirements"
    
    def generate_resume_bullets(self, project: Project, num_bullets: int = 3) -> List[str]:
        """
        Generate resume bullet points for a text/document project
        
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
            ('research_depth', self._generate_research_depth_bullet),
            ('collaboration', self._generate_collaboration_bullet),
            ('audience_focus', self._generate_audience_focus_bullet),
            ('editing_quality', self._generate_editing_quality_bullet),
            ('content_strategy', self._generate_content_strategy_bullet),
            ('technical_documentation', self._generate_technical_documentation_bullet),
            ('publication_impact', self._generate_publication_impact_bullet)
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
        if len(top_bullets) < num_bullets:
            if project.tags:
                doc_type = project.tags[0]
                generic = f"Produced clear and engaging {doc_type} content for diverse audiences"
            else:
                generic = "Developed comprehensive written materials with attention to clarity and accuracy"
            top_bullets.append(generic)
        
        return top_bullets
    
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
        
        # Test with different bullet counts
        for num in [3, 5]:
            print(f"\n{'='*70}")
            print(f"Testing with {num} bullets:")
            print('='*70)
            
            generator = TextBulletGenerator()
            result = generator.generate_bullets_for_project(text_projects[0].id, num_bullets=num)
            
            if result['success']:
                print("Generated Resume Component:")
                print("-" * 70)
                print(result['formatted_component'])
                print("-" * 70)
            else:
                print(f"Error: {result['error']}")