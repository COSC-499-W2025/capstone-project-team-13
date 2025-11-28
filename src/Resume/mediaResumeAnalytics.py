"""
Media-specific resume analytics functions.

Features:
- Integration with visualMediaAnalyzer.py for software/skills detection
- Portfolio impact scoring
- Software proficiency analysis
- Creative skill assessment
"""

import os
import sys
from typing import Dict, Any, List, Optional

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.Databases.database import db_manager, Project
from src.Analysis.visualMediaAnalyzer import analyze_visual_project


# ============================================
# VISUAL MEDIA ANALYZER INTEGRATION
# ============================================

def analyze_media_project(project: Project) -> Dict[str, Any]:
    """
    Analyze visual media project using visualMediaAnalyzer.py
    
    Detects software used and skills based on file types and metadata.
    
    Args:
        project: Project object from database
        
    Returns:
        Dictionary with detected software and skills
    """
    if project.project_type != 'visual_media':
        return {
            'error': f'Project type is {project.project_type}, not visual_media',
            'analysis_available': False
        }
    
    folder_path = project.file_path
    
    if not folder_path or not os.path.exists(folder_path):
        return {
            'analysis_available': False,
            'message': 'Project folder not found'
        }
    
    try:
        analysis = analyze_visual_project(folder_path)
        
        if not analysis or analysis.get('details') == 'No visual media files found.':
            return {
                'analysis_available': False,
                'message': 'No media files found'
            }
        
        return {
            'analysis_available': True,
            'num_files': analysis.get('num_files', 0),
            'total_size': analysis.get('total_size', 0),
            'software_detected': analysis.get('software_used', []),
            'skills_detected': analysis.get('skills_detected', [])
        }
    
    except Exception as e:
        return {
            'analysis_available': False,
            'message': f'Analysis failed: {str(e)}'
        }


# ============================================
# PORTFOLIO IMPACT SCORING
# ============================================

def calculate_portfolio_impact(project: Project) -> Dict[str, Any]:
    """
    Calculate portfolio impact score for media project
    
    Scoring based on:
    - File count (portfolio size)
    - Total size (quality/resolution)
    - Software diversity
    
    Args:
        project: Project object from database
        
    Returns:
        Dictionary with impact score and insights
    """
    if project.project_type != 'visual_media':
        return {
            'error': f'Project type is {project.project_type}, not visual_media',
            'impact_available': False
        }
    
    impact_score = 0
    insights = []
    
    # File count analysis (30 points)
    file_count = project.file_count or 0
    if file_count >= 50:
        impact_score += 30
        insights.append(f"✅ Extensive portfolio with {file_count} assets")
    elif file_count >= 30:
        impact_score += 20
        insights.append(f"⚠️  Solid portfolio with {file_count} assets")
    elif file_count >= 15:
        impact_score += 10
        insights.append(f"📊 Developing portfolio with {file_count} assets")
    else:
        insights.append(f"❌ Limited portfolio size ({file_count} assets) - aim for 30+")
    
    # Size/quality analysis (30 points)
    if project.total_size_bytes:
        size_gb = project.total_size_bytes / (1024**3)
        size_mb = project.total_size_bytes / (1024**2)
        
        if size_gb >= 1:
            impact_score += 30
            insights.append(f"✅ High-resolution content ({size_gb:.1f} GB)")
        elif size_mb >= 500:
            impact_score += 20
            insights.append(f"⚠️  Good quality content ({size_mb:.0f} MB)")
        elif size_mb >= 100:
            impact_score += 10
            insights.append(f"📊 Moderate quality content ({size_mb:.0f} MB)")
        else:
            insights.append(f"❌ Low file sizes ({size_mb:.0f} MB)")
    
    # Software diversity (40 points)
    tool_count = len(project.languages or [])
    if tool_count >= 3:
        impact_score += 40
        tools_text = ', '.join(project.languages[:3])
        insights.append(f"✅ Multi-tool proficiency: {tools_text}")
    elif tool_count >= 2:
        impact_score += 25
        insights.append(f"⚠️  Dual-tool capability: {', '.join(project.languages)}")
    elif tool_count >= 1:
        impact_score += 10
        insights.append(f"📊 Single-tool focus: {project.languages[0]}")
    else:
        insights.append("❌ No software tools specified")
    
    # Determine grade
    if impact_score >= 80:
        grade = "Professional"
        recommendation = "Portfolio ready for senior roles"
    elif impact_score >= 60:
        grade = "Intermediate"
        recommendation = "Strong portfolio, consider adding more variety"
    elif impact_score >= 40:
        grade = "Developing"
        recommendation = "Build portfolio with more high-quality pieces"
    else:
        grade = "Beginner"
        recommendation = "Focus on creating 30+ professional pieces"
    
    return {
        'impact_available': True,
        'impact_score': impact_score,
        'grade': grade,
        'insights': insights,
        'recommendation': recommendation
    }


# ============================================
# SOFTWARE PROFICIENCY DETECTION
# ============================================

# Professional software categorization
PROFESSIONAL_SOFTWARE = {
    'beginner': ['Canva', 'GIMP', 'Paint.NET'],
    'intermediate': ['Adobe Photoshop', 'Adobe Illustrator', 'Adobe InDesign', 'Photoshop', 'Illustrator'],
    'advanced': ['Adobe After Effects', 'Adobe Premiere Pro', 'Lightroom', 'XD', 'After Effects', 'Premiere'],
    'expert': ['Cinema 4D', 'Blender', 'Maya', 'ZBrush', 'Substance Painter', '3ds Max', 'Houdini']
}


def detect_software_skill_level(project: Project) -> Dict[str, Any]:
    """
    Detect software proficiency level based on tools used
    
    Args:
        project: Project object from database
        
    Returns:
        Dictionary with skill tier and recommended verbs
    """
    if project.project_type != 'visual_media':
        return {
            'error': f'Project type is {project.project_type}, not visual_media',
            'skill_level_available': False
        }
    
    tool_count = len(project.languages or [])
    tools = project.languages or []
    
    # Check for expert tools
    expert_tools = []
    for tool in tools:
        for expert in PROFESSIONAL_SOFTWARE['expert']:
            if expert.lower() in tool.lower():
                expert_tools.append(tool)
    
    # Check for advanced tools
    advanced_tools = []
    for tool in tools:
        for advanced in PROFESSIONAL_SOFTWARE['advanced']:
            if advanced.lower() in tool.lower():
                advanced_tools.append(tool)
    
    # Determine tier
    if expert_tools:
        tier = 'expert'
        emphasis = 'multi-discipline creative expertise with industry-leading tools'
        recommended_verb = 'Crafted'
    elif tool_count >= 4 or (advanced_tools and tool_count >= 3):
        tier = 'advanced'
        emphasis = 'comprehensive creative toolkit'
        recommended_verb = 'Produced'
    elif tool_count >= 2:
        tier = 'intermediate'
        emphasis = 'solid design foundation'
        recommended_verb = 'Designed'
    else:
        tier = 'beginner'
        emphasis = 'developing design skills'
        recommended_verb = 'Created'
    
    return {
        'skill_level_available': True,
        'skill_tier': tier,
        'tool_count': tool_count,
        'emphasis': emphasis,
        'recommended_verb': recommended_verb,
        'expert_tools': expert_tools,
        'advanced_tools': advanced_tools
    }


# ============================================
# PORTFOLIO READINESS VALIDATION
# ============================================

def validate_portfolio_readiness(project: Project) -> Dict[str, Any]:
    """
    Validate if portfolio meets professional standards
    
    Checklist:
    - Sufficient quantity (15+ files)
    - Professional software (2+ tools)
    - High quality (100MB+ size)
    - Diverse skills (3+ skills)
    
    Args:
        project: Project object from database
        
    Returns:
        Dictionary with readiness assessment
    """
    if project.project_type != 'visual_media':
        return {
            'error': f'Project type is {project.project_type}, not visual_media',
            'readiness_available': False
        }
    
    checklist = {
        'sufficient_quantity': (project.file_count or 0) >= 15,
        'professional_software': len(project.languages or []) >= 2,
        'high_quality': (project.total_size_bytes or 0) >= 100 * 1024 * 1024,
        'diverse_skills': len(project.skills or []) >= 3
    }
    
    score = sum(25 for passed in checklist.values() if passed)
    
    recommendations = []
    if not checklist['sufficient_quantity']:
        current = project.file_count or 0
        needed = 15 - current
        recommendations.append(f"📈 Add {needed} more pieces (currently: {current})")
    
    if not checklist['professional_software']:
        current = len(project.languages or [])
        recommendations.append(f"🛠️  Expand software toolkit (currently: {current} tool{'s' if current != 1 else ''})")
    
    if not checklist['high_quality']:
        current_mb = (project.total_size_bytes or 0) / (1024 * 1024)
        recommendations.append(f"📸 Include high-resolution work (currently: {current_mb:.0f} MB, target: 100+ MB)")
    
    if not checklist['diverse_skills']:
        current = len(project.skills or [])
        needed = 3 - current
        recommendations.append(f"🎨 Showcase {needed} more skill{'s' if needed != 1 else ''} (currently: {current})")
    
    # Determine readiness
    if score >= 100:
        readiness_level = "Fully Ready"
        status = "✅ Portfolio meets all professional standards"
    elif score >= 75:
        readiness_level = "Nearly Ready"
        status = "⚠️  Portfolio is strong, minor improvements needed"
    elif score >= 50:
        readiness_level = "Developing"
        status = "📊 Portfolio shows promise, needs strengthening"
    else:
        readiness_level = "Not Ready"
        status = "❌ Portfolio needs significant development"
    
    return {
        'readiness_available': True,
        'readiness_score': score,
        'readiness_level': readiness_level,
        'status': status,
        'is_job_ready': score >= 75,
        'checklist': checklist,
        'recommendations': recommendations
    }


# ============================================
# COMPREHENSIVE MEDIA ANALYSIS
# ============================================

def analyze_media_project_comprehensive(project: Project) -> Dict[str, Any]:
    """
    Perform comprehensive analysis of media project
    
    Combines all media-specific analyses.
    
    Args:
        project: Project object from database
        
    Returns:
        Dictionary with all analysis results
    """
    return {
        'media_analysis': analyze_media_project(project),
        'portfolio_impact': calculate_portfolio_impact(project),
        'skill_level': detect_software_skill_level(project),
        'portfolio_readiness': validate_portfolio_readiness(project)
    }


# ============================================
# BULLET ENHANCEMENT HELPERS
# ============================================

def get_portfolio_quality_phrase(project: Project) -> str:
    """
    Get a quality descriptor phrase for portfolio
    
    Args:
        project: Project object
        
    Returns:
        Phrase describing portfolio quality
    """
    impact = calculate_portfolio_impact(project)
    
    if impact.get('impact_available'):
        grade = impact.get('grade', 'Developing')
        if grade == 'Professional':
            return 'professional-grade portfolio'
        elif grade == 'Intermediate':
            return 'comprehensive portfolio'
        else:
            return 'portfolio'
    
    return 'creative work'


def should_emphasize_software_proficiency(project: Project) -> bool:
    """
    Determine if software proficiency should be emphasized
    
    Args:
        project: Project object
        
    Returns:
        True if software skills are notable
    """
    skill_level = detect_software_skill_level(project)
    
    if skill_level.get('skill_level_available'):
        return skill_level.get('skill_tier') in ['advanced', 'expert']
    
    return False


if __name__ == "__main__":
    print("Media Resume Analytics")
    print("=" * 70)
    print("\nThis module provides media-specific analytics:")
    print("  - Visual Media Analysis (visualMediaAnalyzer.py)")
    print("  - Portfolio Impact Scoring")
    print("  - Software Proficiency Detection")
    print("  - Portfolio Readiness Validation")