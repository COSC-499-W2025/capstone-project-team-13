"""
Generates professional resume bullet points for coding projects
based on project analysis data from the database.

Features:
- Converts coding project data into achievement-focused bullet points
- Generates 9 different bullet types and scores them
- Returns top N bullets based on scoring (supports 2-5 bullets)
- Includes quantifiable metrics (lines of code, file count, team size)
- Highlights programming languages, frameworks, and technical skills
- Formats bullets in professional resume style
"""

import os
import sys
from typing import List, Dict, Any, Optional, Tuple

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
        'deployment': ['Deployed', 'Released', 'Launched', 'Delivered', 'Published'],
        'collaboration': ['Coordinated', 'Facilitated', 'Led', 'Managed', 'Directed']
    }
    
    # Technical keywords for scoring
    TECHNICAL_KEYWORDS = [
        'Python', 'Java', 'JavaScript', 'TypeScript', 'C++', 'C#', 'Go', 'Rust', 'Swift', 'Kotlin',
        'React', 'Angular', 'Vue', 'Django', 'Flask', 'Spring', 'Express', 'Node',
        'SQL', 'PostgreSQL', 'MySQL', 'MongoDB', 'Redis',
        'AWS', 'Azure', 'GCP', 'Docker', 'Kubernetes',
        'API', 'REST', 'GraphQL', 'microservices', 'CI/CD', 'testing', 'agile'
    ]
    
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
    
    def _select_action_verb(self, project: Project, used_verbs: List[str], category: str = 'development') -> str:
        """
        Select an appropriate action verb based on category
        
        Args:
            project: Project object
            used_verbs: List of already used verbs to avoid repetition
            category: Verb category to select from
            
        Returns:
            Selected action verb
        """
        # Guard against invalid category — fall back to 'development' if not found
        if category not in self.ACTION_VERBS:
            category = 'development'
        
        # Filter against used_verbs globally (not just within this category)
        # to prevent the same verb appearing across different bullet types
        available_verbs = [v for v in self.ACTION_VERBS[category] if v not in used_verbs]
        
        # If all verbs in this category are used, reset to category verbs
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
        Generate the main description bullet describing what was built
        
        Args:
            project: Project object
            used_verbs: List of already used verbs
            
        Returns:
            Main description bullet point
        """
        action_verb = self._select_action_verb(project, used_verbs, 'development')
        
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
        has_team_metric = len(contributors) > 1
        if has_team_metric:
            metrics.append(f"{len(contributors)}-person team")
        
        if not metrics:
            return None
        
        action_verb = self._select_action_verb(project, used_verbs, 'development')
        metric_text = ' and '.join(metrics[:2])  # Limit to 2 metrics
        
        # Create impact statement — only use collaboration phrasing if the team metric was actually included
        if has_team_metric:
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
        
        action_verb = self._select_action_verb(project, used_verbs, 'development')
        
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
        
        action_verb = self._select_action_verb(project, used_verbs, 'deployment')
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
        
        # Get primary tech
        tech = "software development"
        if project.frameworks:
            tech = f"{project.frameworks[0]} development"
        elif project.languages:
            tech = f"{project.languages[0]} development"
        
        return f"{action_verb} with {len(contributors)}-person team to deliver {tech}, ensuring code quality through peer reviews"
    
    def _generate_process_bullet(self, project: Project, used_verbs: List[str]) -> Optional[str]:
        """
        Generate a bullet point highlighting development process/methodology
        
        Args:
            project: Project object
            used_verbs: List of already used action verbs
            
        Returns:
            Process-focused bullet point or None
        """
        # Look for process-related skills
        process_keywords = ['agile', 'scrum', 'git', 'version control', 'ci/cd', 'testing', 'deployment']
        
        if not project.skills:
            return None
        
        relevant_skills = [skill for skill in project.skills 
                          if any(keyword in skill.lower() for keyword in process_keywords)]
        
        if not relevant_skills:
            return None
        
        action_verb = self._select_action_verb(project, used_verbs, 'development')
        
        # Build process description
        process_desc = "following industry best practices"
        if any('git' in skill.lower() or 'version' in skill.lower() for skill in relevant_skills):
            process_desc = "utilizing version control and code review workflows"
        elif any('agile' in skill.lower() or 'scrum' in skill.lower() for skill in relevant_skills):
            process_desc = "following Agile methodologies"
        elif any('test' in skill.lower() for skill in relevant_skills):
            process_desc = "implementing comprehensive testing strategies"
        
        tech = project.frameworks[0] if project.frameworks else project.languages[0] if project.languages else "technology"
        
        return f"{action_verb} {tech} solutions {process_desc} to ensure maintainability"
    
    def _generate_innovation_bullet(self, project: Project, used_verbs: List[str]) -> Optional[str]:
        """
        Generate a bullet point highlighting innovative approaches
        
        Args:
            project: Project object
            used_verbs: List of already used action verbs
            
        Returns:
            Innovation-focused bullet point or None
        """
        # Look for cutting-edge tech or frameworks
        modern_tech = ['React', 'Vue', 'Angular', 'Node.js', 'Docker', 'Kubernetes', 
                      'GraphQL', 'TypeScript', 'Rust', 'Go', 'microservices']
        
        found_tech = []
        if project.frameworks:
            found_tech.extend([fw for fw in project.frameworks if fw in modern_tech])
        if project.languages:
            found_tech.extend([lang for lang in project.languages if lang in modern_tech])
        
        if not found_tech:
            return None
        
        action_verb = self._select_action_verb(project, used_verbs, 'design')
        
        tech_text = ' and '.join(found_tech[:2])
        return f"{action_verb} modern architecture using {tech_text} to achieve scalable and maintainable solutions"
    
    def _generate_technical_depth_bullet(self, project: Project, used_verbs: List[str]) -> Optional[str]:
        """
        Generate a bullet point showcasing technical depth and complexity
        
        Args:
            project: Project object
            used_verbs: List of already used action verbs
            
        Returns:
            Technical depth-focused bullet point or None
        """
        # Look for advanced technical concepts
        advanced_skills = ['algorithm', 'optimization', 'architecture', 'design pattern', 
                          'database', 'api', 'security', 'performance']
        
        if not project.skills:
            return None
        
        relevant_skills = [skill for skill in project.skills[:3]
                          if any(keyword in skill.lower() for keyword in advanced_skills)]
        
        if len(relevant_skills) < 2:
            return None
        
        action_verb = self._select_action_verb(project, used_verbs, 'improvement')
        
        skills_text = ' and '.join(relevant_skills[:2])
        return f"{action_verb} {skills_text} to enhance system performance and reliability"
    
    def _generate_deployment_bullet(self, project: Project, used_verbs: List[str]) -> Optional[str]:
        """
        Generate a bullet point about deployment and delivery
        
        Args:
            project: Project object
            used_verbs: List of already used action verbs
            
        Returns:
            Deployment-focused bullet point or None
        """
        # Look for deployment-related keywords
        deployment_keywords = ['deploy', 'cloud', 'aws', 'azure', 'docker', 'kubernetes', 'ci/cd', 'production']
        
        has_deployment = False
        if project.skills:
            has_deployment = any(keyword in skill.lower() 
                               for skill in project.skills 
                               for keyword in deployment_keywords)
        
        if not has_deployment:
            return None
        
        action_verb = self._select_action_verb(project, used_verbs, 'deployment')
        
        # Find deployment platform
        platform = "production environment"
        if project.skills:
            for skill in project.skills:
                if 'aws' in skill.lower():
                    platform = "AWS cloud infrastructure"
                    break
                elif 'azure' in skill.lower():
                    platform = "Azure cloud platform"
                    break
                elif 'docker' in skill.lower() or 'kubernetes' in skill.lower():
                    platform = "containerized environment"
                    break
        
        return f"{action_verb} application to {platform} with automated CI/CD pipeline"
    
    def generate_resume_bullets(self, project: Project, num_bullets: int = 3) -> List[str]:
        """
        Generate resume bullet points for a coding project
        
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
        # Clamp num_bullets to valid range of 2-5
        num_bullets = max(2, min(5, num_bullets))
        
        used_verbs = []
        all_bullets_with_scores = []
        
        # Generate all bullet types
        bullet_generators = [
            ('main', self._generate_main_description_bullet),
            ('scale', self._generate_scale_bullet),
            ('skills', self._generate_skills_bullet),
            ('impact', self._generate_impact_bullet),
            ('collaboration', self._generate_collaboration_bullet),
            ('process', self._generate_process_bullet),
            ('innovation', self._generate_innovation_bullet),
            ('technical_depth', self._generate_technical_depth_bullet),
            ('deployment', self._generate_deployment_bullet)
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
        
        # If we still don't have enough bullets, fill with generic fallbacks
        generic_templates = [
            lambda p: f"Utilized {p.frameworks[0]} framework to implement efficient and scalable solutions" if p.frameworks else None,
            lambda p: f"Developed solutions in {p.languages[0]} focusing on code quality and maintainability" if p.languages else None,
            lambda p: f"Contributed {p.lines_of_code:,} lines of code across {p.file_count} project files" if p.lines_of_code and p.file_count else None,
            lambda p: f"Applied technical skills to design and implement robust software solutions",
            lambda p: f"Built and maintained software components ensuring reliability and performance",
        ]
        
        for template in generic_templates:
            if len(top_bullets) >= num_bullets:
                break
            generic = template(project)
            if generic and generic not in top_bullets:
                top_bullets.append(generic)
        
        return top_bullets
    
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
        
        # Test with different bullet counts
        for num in [3, 5]:
            print(f"\n{'='*70}")
            print(f"Testing with {num} bullets:")
            print('='*70)
            
            generator = CodeBulletGenerator()
            result = generator.generate_bullets_for_project(coding_projects[0].id, num_bullets=num)
            
            if result['success']:
                print("Generated Resume Component:")
                print("-" * 70)
                print(result['formatted_component'])
                print("-" * 70)
            else:
                print(f"Error: {result['error']}")