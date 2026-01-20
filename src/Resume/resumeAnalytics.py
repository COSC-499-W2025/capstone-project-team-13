"""
Shared resume analytics functions that apply to ALL project types.

Features:
- ATS (Applicant Tracking System) optimization scoring
- Bullet quality analysis and feedback
- Success evidence utility functions
"""

import os
import sys
import re
import json
from typing import List, Dict, Any, Optional

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.Databases.database import db_manager, Project


# ============================================
# ATS OPTIMIZATION SCORING
# ============================================

# Technical keywords for ATS scoring (applies to all project types)
TECHNICAL_KEYWORDS = {
    'code': {
        'languages': ['Python', 'Java', 'JavaScript', 'TypeScript', 'C++', 'C#', 'Go', 'Rust', 'Swift', 'Kotlin'],
        'frameworks': ['React', 'Angular', 'Vue', 'Django', 'Flask', 'Spring', 'Express', 'Node'],
        'databases': ['SQL', 'PostgreSQL', 'MySQL', 'MongoDB', 'Redis', 'DynamoDB'],
        'cloud': ['AWS', 'Azure', 'GCP', 'Docker', 'Kubernetes'],
        'concepts': ['API', 'REST', 'GraphQL', 'microservices', 'CI/CD', 'testing', 'agile']
    },
    'visual_media': {
        'software': ['Photoshop', 'Illustrator', 'InDesign', 'After Effects', 'Premiere', 'Figma', 'Sketch', 
                    'Blender', 'Maya', 'Cinema 4D', 'Unity', 'Unreal'],
        'skills': ['UI', 'UX', '3D', 'animation', 'video', 'motion graphics', 'branding', 'typography'],
        'formats': ['vector', 'raster', '3D modeling', 'rendering', 'compositing']
    },
    'text': {
        'types': ['technical writing', 'copywriting', 'content', 'documentation', 'research', 'journalism'],
        'skills': ['SEO', 'editing', 'proofreading', 'grammar', 'storytelling', 'analysis'],
        'formats': ['blog', 'article', 'whitepaper', 'report', 'documentation']
    }
}

# Strong action verbs for all types
STRONG_ACTION_VERBS = [
    'Developed', 'Built', 'Created', 'Engineered', 'Implemented', 'Designed', 'Architected',
    'Optimized', 'Enhanced', 'Improved', 'Led', 'Managed', 'Delivered', 'Launched',
    'Produced', 'Crafted', 'Authored', 'Published', 'Analyzed', 'Researched',
    'Coordinated', 'Facilitated', 'Directed', 'Composed', 'Rendered', 'Illustrated'
]


def calculate_ats_score(bullet: str, project_type: str = 'code') -> Dict[str, Any]:
    """
    Score a resume bullet for ATS (Applicant Tracking System) compatibility (0-100)
    
    Scoring breakdown:
    - Technical keywords present (40 pts)
    - Quantifiable metrics included (30 pts)
    - Optimal length 10-20 words (20 pts)
    - Strong action verb (10 pts)
    
    Args:
        bullet: Resume bullet text to score
        project_type: Type of project ('code', 'visual_media', 'text')
        
    Returns:
        Dictionary with score, feedback, and detected keywords
    """
    score = 0
    feedback = []
    detected_keywords = []
    
    # Check for metrics/numbers (30 points)
    if any(char.isdigit() for char in bullet):
        score += 30
    else:
        feedback.append("❌ Add quantifiable metrics (e.g., '40% faster', '10K+ lines', '50+ assets')")
    
    # Check length (20 points)
    words = len(bullet.split())
    if 10 <= words <= 20:
        score += 20
    elif words < 10:
        feedback.append(f"❌ Bullet too short ({words} words) - aim for 10-20 words")
        score += 10  # Partial credit
    else:
        feedback.append(f"⚠️  Bullet lengthy ({words} words) - consider condensing")
        score += 15  # Partial credit
    
    # Check for technical keywords (40 points)
    bullet_lower = bullet.lower()
    keywords_to_check = TECHNICAL_KEYWORDS.get(project_type, TECHNICAL_KEYWORDS['code'])
    
    for category, keywords in keywords_to_check.items():
        for keyword in keywords:
            if keyword.lower() in bullet_lower:
                detected_keywords.append(keyword)
    
    if len(detected_keywords) >= 3:
        score += 40
        feedback.append(f"✅ Strong technical keywords: {', '.join(detected_keywords[:3])}")
    elif len(detected_keywords) >= 1:
        score += 20  # Partial credit
        feedback.append(f"⚠️  Add more technical keywords (found: {', '.join(detected_keywords)})")
    else:
        feedback.append("❌ Missing technical keywords - add specific tools, languages, or skills")
    
    # Check action verb strength (10 points)
    first_word = bullet.split()[0] if bullet else ""
    if first_word in STRONG_ACTION_VERBS:
        score += 10
    else:
        feedback.append(f"⚠️  Consider stronger action verb (current: '{first_word}')")
        score += 5  # Partial credit
    
    # Determine grade
    if score >= 90:
        grade = "A+ (Excellent)"
    elif score >= 80:
        grade = "A (Very Good)"
    elif score >= 70:
        grade = "B (Good)"
    elif score >= 60:
        grade = "C (Acceptable)"
    else:
        grade = "D (Needs Improvement)"
    
    return {
        'score': score,
        'grade': grade,
        'feedback': feedback,
        'keywords': detected_keywords,
        'word_count': words,
        'has_metrics': any(char.isdigit() for char in bullet)
    }


def score_all_bullets(bullets: List[str], project_type: str = 'code') -> Dict[str, Any]:
    """
    Score multiple bullets and return aggregate analysis
    
    Args:
        bullets: List of bullet points
        project_type: Type of project
        
    Returns:
        Dictionary with overall score and individual bullet scores
    """
    individual_scores = [calculate_ats_score(bullet, project_type) for bullet in bullets]
    avg_score = sum(s['score'] for s in individual_scores) / len(individual_scores) if individual_scores else 0
    
    all_keywords = []
    for score_data in individual_scores:
        all_keywords.extend(score_data['keywords'])
    
    # Calculate grade distribution
    grade_counts = {'A+': 0, 'A': 0, 'B': 0, 'C': 0, 'D': 0}
    for score_data in individual_scores:
        grade = score_data['grade']
        if 'A+' in grade:
            grade_counts['A+'] += 1
        elif 'A ' in grade or grade.startswith('A'):
            grade_counts['A'] += 1
        elif 'B' in grade:
            grade_counts['B'] += 1
        elif 'C' in grade:
            grade_counts['C'] += 1
        else:
            grade_counts['D'] += 1
    
    return {
        'overall_score': round(avg_score, 1),
        'individual_scores': individual_scores,
        'total_keywords': len(set(all_keywords)),
        'unique_keywords': list(set(all_keywords)),
        'bullets_with_metrics': sum(1 for s in individual_scores if s['has_metrics']),
        'grade_distribution': grade_counts
    }


# ============================================
# SUCCESS EVIDENCE UTILITIES
# ============================================

def populate_success_evidence(project: Project, metrics: Dict[str, Any]) -> None:
    """
    Optional utility to populate success_evidence field in database.
    
    Args:
        project: Project object
        metrics: Dictionary with keys like 'users', 'performance_improvement', etc.
    
    Example:
        populate_success_evidence(project, {
            'users': 1000,
            'performance_improvement': 40,
            'success_rate': 95
        })
    """
    project.success_evidence = json.dumps(metrics)
    db_manager.update_project(project.id, {'success_evidence': project.success_evidence})


def get_success_evidence(project: Project) -> Optional[Dict[str, Any]]:
    """
    Retrieve and parse success_evidence from project
    
    Args:
        project: Project object
        
    Returns:
        Dictionary of success metrics or None
    """
    if not project.success_evidence:
        return None
    
    try:
        return json.loads(project.success_evidence)
    except (json.JSONDecodeError, TypeError):
        return None


def has_success_metrics(project: Project) -> bool:
    """
    Check if project has success evidence populated
    
    Args:
        project: Project object
        
    Returns:
        True if success_evidence exists and is valid
    """
    return get_success_evidence(project) is not None


# ============================================
# UTILITY FUNCTIONS
# ============================================

def extract_metrics_from_bullet(bullet: str) -> List[str]:
    """
    Extract quantifiable metrics from a bullet point
    
    Args:
        bullet: Bullet text
        
    Returns:
        List of detected metrics (e.g., ['40%', '10K+', '5 GB'])
    """
    metrics = []
    
    # Percentage patterns
    percentages = re.findall(r'\d+%', bullet)
    metrics.extend(percentages)
    
    # Number with K/M/B
    large_numbers = re.findall(r'\d+[KMB]\+?', bullet, re.IGNORECASE)
    metrics.extend(large_numbers)
    
    # Numbers with units
    units = re.findall(r'\d+\+?\s*(?:GB|MB|files|lines|words|documents|assets|users)', bullet, re.IGNORECASE)
    metrics.extend(units)
    
    return metrics


def suggest_improvements(bullet: str, project_type: str = 'code') -> List[str]:
    """
    Suggest specific improvements for a bullet point
    
    Args:
        bullet: Bullet text to analyze
        project_type: Type of project
        
    Returns:
        List of actionable improvement suggestions
    """
    suggestions = []
    ats_score = calculate_ats_score(bullet, project_type)
    
    # Add suggestions based on ATS feedback
    if ats_score['score'] < 70:
        if not ats_score['has_metrics']:
            suggestions.append("Add specific numbers or metrics to quantify your impact")
        
        if len(ats_score['keywords']) < 2:
            suggestions.append(f"Include more technical keywords relevant to {project_type}")
        
        if ats_score['word_count'] < 10:
            suggestions.append("Expand with more detail about technologies used or outcomes achieved")
        elif ats_score['word_count'] > 20:
            suggestions.append("Condense to 10-20 words for better ATS compatibility")
    
    return suggestions


if __name__ == "__main__":
    print("Resume Analytics - Shared Functions")
    print("=" * 70)
    print("\nThis module provides shared analytics functions for all project types:")
    print("  - ATS Optimization Scoring")
    print("  - Success Evidence Utilities")
    print("  - Bullet Quality Analysis")
    print("\nNote: Bullets are now optimized during generation.")
    print("Use scoring functions to view quality metrics only.")