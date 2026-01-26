"""
Portfolio Data Formatter
Prepares project data from database for portfolio display frontend

Usage:
    from src.Portfolio.portfolioFormatter import PortfolioFormatter
    
    formatter = PortfolioFormatter()
    
    # Get all projects formatted for portfolio
    portfolio_data = formatter.get_portfolio_data()
    
    # Get single project details
    project_detail = formatter.get_project_detail(project_id=1)
    
    # Get filtered projects
    filtered = formatter.get_filtered_projects(project_type='code', search='python')
"""

import sys
import os
from typing import List, Dict, Any, Optional
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.Databases.database import db_manager, Project


class PortfolioFormatter:
    """Format database projects into portfolio-ready JSON structures"""
    
    def __init__(self):
        self.db = db_manager
    
    def _format_date(self, date_obj) -> Optional[str]:
        """Format datetime to readable string"""
        if not date_obj:
            return None
        if hasattr(date_obj, 'strftime'):
            return date_obj.strftime('%B %Y')  # e.g., "March 2024"
        return str(date_obj)
    
    def _format_size(self, size_bytes: Optional[int]) -> str:
        """Format file size to human-readable format"""
        if not size_bytes:
            return "0 B"
        
        units = ['B', 'KB', 'MB', 'GB']
        size = float(size_bytes)
        unit_index = 0
        
        while size >= 1024 and unit_index < len(units) - 1:
            size /= 1024
            unit_index += 1
        
        return f"{size:.1f} {units[unit_index]}"
    
    def _get_project_metrics(self, project: Project) -> Dict[str, Any]:
        """Extract metrics based on project type"""
        metrics = {}
        
        if project.project_type == 'code':
            metrics = {
                'lines_of_code': project.lines_of_code or 0,
                'file_count': project.file_count or 0,
                'contributors': len(self.db.get_contributors_for_project(project.id)),
                'languages': len(self._as_list(project.languages))

            }
        elif project.project_type == 'visual_media':
            metrics = {
                'file_count': project.file_count or 0,
                'total_size': self._format_size(project.total_size_bytes),
                'software_tools': len(self._as_list(project.languages)),
                'skills': len(self._as_list(project.skills))
            }
        elif project.project_type == 'text':
            metrics = {
                'word_count': project.word_count or 0,
                'file_count': project.file_count or 0,
                'document_types': len(project.tags) if project.tags else 0,
                'skills': len(project.skills) if project.skills else 0
            }
        
        return metrics
    
    def _format_project_card(self, project: Project) -> Dict[str, Any]:
        """Format project for card/list view in portfolio"""
        
        # Get description (prefer AI-generated, fall back to custom or default)
        description = None
        if hasattr(project, 'ai_description') and project.ai_description:
            description = project.ai_description
        elif project.custom_description:
            description = project.custom_description
        elif project.description:
            description = project.description
        else:
            description = f"A {project.project_type} project showcasing {', '.join(project.skills[:3]) if project.skills else 'various skills'}."
        
        # Get top skills (limit to 6 for display)
        skills = self._as_list(project.skills)
        top_skills = skills[:6]
                
        # Get tech stack (languages + frameworks)
        tech_stack = []
        languages = self._as_list(project.languages)
        frameworks = self._as_list(project.frameworks)

        tech_stack.extend(languages[:3])
        tech_stack.extend(frameworks[:2])

        
        return {
            'id': project.id,
            'name': project.name,
            'type': project.project_type,
            'description': description,
            'tech_stack': tech_stack,
            'skills': top_skills,
            'metrics': self._get_project_metrics(project),
            'date': self._format_date(project.date_modified or project.date_created),
            'importance_score': project.importance_score or 0,
            'is_featured': project.is_featured or False
        }
    
    def _format_project_detail(self, project: Project) -> Dict[str, Any]:
        """Format complete project details for detail view"""
        
        # Get all descriptions
        descriptions = {
            'ai_generated': getattr(project, 'ai_description', None),
            'custom': project.custom_description,
            'default': project.description
        }
        
        # Get contributors
        contributors = self.db.get_contributors_for_project(project.id)
        contributors_data = [
            {
                'name': c.name,
                'commits': c.commit_count,
                'contribution_percent': c.contribution_percent
            }
            for c in contributors
        ]
        
        # Get keywords
        keywords = self.db.get_keywords_for_project(project.id)
        keywords_data = [
            {
                'keyword': k.keyword,
                'score': k.score,
                'category': k.category
            }
            for k in keywords[:20]  # Top 20 keywords
        ]
        
        # Get resume bullets if available
        bullets_data = None
        if project.bullets:
            bullets_data = {
                'header': project.bullets.get('header'),
                'bullets': project.bullets.get('bullets', []),
                'ats_score': project.bullets.get('ats_score')
            }
        
        return {
            'id': project.id,
            'name': project.name,
            'type': project.project_type,
            'collaboration_type': project.collaboration_type,
            
            # Descriptions
            'descriptions': descriptions,
            
            # Tech details
            'languages': project.languages or [],
            'frameworks': project.frameworks or [],
            'skills': project.skills or [],
            'tags': project.tags or [],
            
            # Metrics
            'metrics': {
                'lines_of_code': project.lines_of_code,
                'word_count': project.word_count,
                'file_count': project.file_count,
                'total_size': self._format_size(project.total_size_bytes),
                'importance_score': project.importance_score
            },
            
            # Dates
            'dates': {
                'created': self._format_date(project.date_created),
                'modified': self._format_date(project.date_modified),
                'scanned': self._format_date(project.date_scanned)
            },
            
            # Additional data
            'contributors': contributors_data,
            'keywords': keywords_data,
            'resume_bullets': bullets_data,
            'user_role': project.user_role,
            
            # Flags
            'is_featured': project.is_featured,
            'is_hidden': project.is_hidden
        }
    
    def get_portfolio_data(self, include_hidden: bool = False) -> Dict[str, Any]:
        """
        Get complete portfolio data
        
        Returns:
            {
                'summary': {...},
                'projects': [...],
                'stats': {...}
            }
        """
        projects = self.db.get_all_projects(include_hidden=include_hidden)
        
        # Format all projects
        formatted_projects = [
            self._format_project_card(p) for p in projects
        ]
        
        # Sort by importance score
        formatted_projects.sort(key=lambda x: x['importance_score'], reverse=True)
        
        # Calculate statistics
        stats = self._calculate_portfolio_stats(projects)
        
        # Generate summary
        summary = self._generate_portfolio_summary(projects)
        
        return {
            'summary': summary,
            'projects': formatted_projects,
            'stats': stats,
            'total_projects': len(formatted_projects),
            'generated_at': datetime.now().isoformat()
        }
    
    def get_project_detail(self, project_id: int) -> Optional[Dict[str, Any]]:
        """Get detailed information for a single project"""
        project = self.db.get_project(project_id)
        
        if not project:
            return None
        
        return self._format_project_detail(project)
    
    def get_filtered_projects(
        self, 
        project_type: Optional[str] = None,
        search: Optional[str] = None,
        min_importance: Optional[float] = None,
        featured_only: bool = False
    ) -> Dict[str, Any]:
        """
        Get filtered projects
        
        Args:
            project_type: Filter by type ('code', 'visual_media', 'text')
            search: Search in project name, description, skills
            min_importance: Minimum importance score
            featured_only: Only return featured projects
        """
        projects = self.db.get_all_projects(include_hidden=False)
        
        # Apply filters
        filtered = projects
        
        if project_type:
            filtered = [p for p in filtered if p.project_type == project_type]
        
        if featured_only:
            filtered = [p for p in filtered if p.is_featured]
        
        if min_importance is not None:
            filtered = [p for p in filtered if (p.importance_score or 0) >= min_importance]
        
        if search:
            search_lower = search.lower()
            filtered = [
                p for p in filtered
                if (search_lower in p.name.lower() or
                    (p.description and search_lower in p.description.lower()) or
                    any(search_lower in skill.lower() for skill in (p.skills or [])))
            ]
        
        # Format filtered projects
        formatted = [self._format_project_card(p) for p in filtered]
        formatted.sort(key=lambda x: x['importance_score'], reverse=True)
        
        return {
            'projects': formatted,
            'total': len(formatted),
            'filters_applied': {
                'type': project_type,
                'search': search,
                'min_importance': min_importance,
                'featured_only': featured_only
            }
        }
    
    def _calculate_portfolio_stats(self, projects: List[Project]) -> Dict[str, Any]:
        """Calculate overall portfolio statistics"""
        total_projects = len(projects)
        
        if total_projects == 0:
            return {
                'total_projects': 0,
                'by_type': {},
                'total_lines_of_code': 0,
                'total_skills': 0,
                'avg_importance': 0
            }
        
        # Count by type
        by_type = {}
        for p in projects:
            ptype = p.project_type or 'unknown'
            by_type[ptype] = by_type.get(ptype, 0) + 1
        
        # Collect all unique skills
        all_skills = set()
        for p in projects:
            all_skills.update(self._as_list(p.skills))

        
        # Calculate totals
        total_loc = sum(p.lines_of_code or 0 for p in projects)
        total_files = sum(p.file_count or 0 for p in projects)
        avg_importance = sum(p.importance_score or 0 for p in projects) / total_projects
        
        return {
            'total_projects': total_projects,
            'by_type': by_type,
            'total_lines_of_code': total_loc,
            'total_files': total_files,
            'total_skills': len(all_skills),
            'unique_skills': sorted(list(all_skills)),
            'avg_importance_score': round(avg_importance, 2),
            'featured_count': sum(1 for p in projects if p.is_featured)
        }
    def _as_list(self, value):
        if not value:
            return []
        if isinstance(value, list):
            return value
        if isinstance(value, str):
            return [v.strip() for v in value.split(",") if v.strip()]
        return list(value)

    def _generate_portfolio_summary(self, projects: List[Project]) -> Dict[str, Any]:
        """Generate natural language summary of portfolio"""
        if not projects:
            return {
                'text': "No projects available.",
                'highlights': []
            }
        
        # Get top 3 projects by importance
        top_projects = sorted(
            projects, 
            key=lambda p: p.importance_score or 0, 
            reverse=True
        )[:3]
        
        # Collect unique skills
        all_skills = set()
        for p in projects:
            if p.skills:
                all_skills.update(p.skills)
        
        # Generate highlights
        highlights = []
        
        if top_projects:
            highlights.append(f"Top project: {top_projects[0].name}")
        
        if len(all_skills) > 0:
            highlights.append(f"{len(all_skills)} unique skills demonstrated")
        
        by_type = {}
        for p in projects:
            ptype = p.project_type or 'unknown'
            by_type[ptype] = by_type.get(ptype, 0) + 1
        
        if by_type:
            type_summary = ', '.join([f"{count} {ptype}" for ptype, count in by_type.items()])
            highlights.append(f"Diverse portfolio: {type_summary}")
        
        # Generate text summary
        focus = ", ".join(list(all_skills)[:3])
        summary_text = (
            f"Portfolio showcasing {len(projects)} projects across "
            f"{len(by_type)} different categories. "
            f"Demonstrates expertise in {len(all_skills)} technical skills"
            + (f" with a focus on {focus}." if focus else ".")
        )

        
        return {
            'text': summary_text,
            'highlights': highlights,
            'top_projects': [p.name for p in top_projects]
        }
    
    def export_to_json(self, output_path: str, include_hidden: bool = False):
        """Export portfolio data to JSON file"""
        import json
        
        data = self.get_portfolio_data(include_hidden=include_hidden)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        return output_path


    def display_portfolio_view(self):
        """Display portfolio in a beautiful CLI format"""
        portfolio = self.get_portfolio_data()
        
        # Header
        print("\n" + "="*80)
        print("📂 PROJECT PORTFOLIO".center(80))
        print("="*80 + "\n")
        
        # Summary Section
        print("📊 PORTFOLIO SUMMARY")
        print("-"*80)
        print(f"{portfolio['summary']['text']}\n")
        
        print("✨ Highlights:")
        for highlight in portfolio['summary']['highlights']:
            print(f"   • {highlight}")
        print()
        
        # Stats Section
        stats = portfolio['stats']
        print("📈 STATISTICS")
        print("-"*80)
        
        # Display stats in a grid
        print(f"{'Total Projects:':<30} {stats['total_projects']}")
        print(f"{'Featured Projects:':<30} {stats['featured_count']}")
        print(f"{'Average Importance Score:':<30} {stats['avg_importance_score']}/100")
        print(f"{'Total Lines of Code:':<30} {stats['total_lines_of_code']:,}")
        print(f"{'Total Files:':<30} {stats['total_files']:,}")
        print(f"{'Unique Skills:':<30} {stats['total_skills']}")
        
        # Project types breakdown
        print(f"\n{'Project Types:':<30}")
        for ptype, count in stats['by_type'].items():
            type_emoji = {'code': '💻', 'visual_media': '🎨', 'text': '📝'}.get(ptype, '📦')
            print(f"   {type_emoji} {ptype.replace('_', ' ').title():<20} {count}")
        print()
        
        # Projects Section
        print("🏆 FEATURED PROJECTS")
        print("="*80 + "\n")
        
        # Get featured projects first, then top by importance
        featured = [p for p in portfolio['projects'] if p['is_featured']]
        non_featured = [p for p in portfolio['projects'] if not p['is_featured']]
        
        # Display featured
        if featured:
            for i, project in enumerate(featured[:3], 1):
                self._display_project_card(project, i, featured=True)
        
        # Display top non-featured
        print("\n📋 ALL PROJECTS")
        print("="*80 + "\n")
        
        for i, project in enumerate(portfolio['projects'][:10], 1):
            self._display_project_card(project, i, featured=False)
        
        if len(portfolio['projects']) > 10:
            print(f"\n... and {len(portfolio['projects']) - 10} more projects")
        
        # Skills Cloud
        if stats['unique_skills']:
            print("\n\n🎯 SKILLS PORTFOLIO")
            print("-"*80)
            # Display skills in columns
            skills = stats['unique_skills'][:30]  # Top 30 skills
            cols = 3
            rows = (len(skills) + cols - 1) // cols
            
            for row in range(rows):
                row_skills = []
                for col in range(cols):
                    idx = row + col * rows
                    if idx < len(skills):
                        row_skills.append(f"• {skills[idx]:<25}")
                print("".join(row_skills))
        
        print("\n" + "="*80 + "\n")
    
    def _display_project_card(self, project: Dict[str, Any], index: int, featured: bool = False):
        """Display a single project card in CLI"""
        
        # Type emoji
        type_emoji = {
            'code': '💻',
            'visual_media': '🎨', 
            'text': '📝'
        }.get(project['type'], '📦')
        
        # Featured star
        star = '⭐ ' if featured else ''
        
        # Header
        print(f"{star}{type_emoji} {index}. {project['name']}")
        print(f"{'─' * 80}")
        
        # Description
        desc = project['description']
        if len(desc) > 150:
            desc = desc[:147] + "..."
        print(f"{desc}\n")
        
        # Tech stack
        if project['tech_stack']:
            tech = ' • '.join(project['tech_stack'][:5])
            print(f"🔧 Tech: {tech}")
        
        # Skills
        if project['skills']:
            skills = ' • '.join(project['skills'][:6])
            print(f"💡 Skills: {skills}")
        
        # Metrics
        metrics = project['metrics']
        metric_parts = []
        
        if 'lines_of_code' in metrics and metrics['lines_of_code'] > 0:
            metric_parts.append(f"{metrics['lines_of_code']:,} LOC")
        if 'word_count' in metrics and metrics['word_count'] > 0:
            metric_parts.append(f"{metrics['word_count']:,} words")
        if 'file_count' in metrics:
            metric_parts.append(f"{metrics['file_count']} files")
        if 'total_size' in metrics:
            metric_parts.append(metrics['total_size'])
        
        if metric_parts:
            print(f"📊 Metrics: {' • '.join(metric_parts)}")
        
        # Date and importance
        date_importance = []
        if project['date']:
            date_importance.append(f"📅 {project['date']}")
        date_importance.append(f"⚡ Score: {project['importance_score']:.0f}/100")
        
        print(f"{' | '.join(date_importance)}")
        print()


if __name__ == "__main__":
    # Example usage
    formatter = PortfolioFormatter()
    
    # Display beautiful portfolio view
    formatter.display_portfolio_view()