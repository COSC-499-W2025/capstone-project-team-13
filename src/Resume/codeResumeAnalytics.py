"""
Code-specific resume analytics functions.

Features:
- Integration with codeEfficiency.py for complexity scoring
- Integration with keywordAnalytics.py for technical density
- Integration with skillsExtractCoding.py for skill extraction
- Code quality metrics for bullet enhancement
"""

import os
import sys
from typing import Dict, Any, List, Optional
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.Databases.database import db_manager, Project
from src.Analysis.codeEfficiency import grade_efficiency
from src.Analysis.keywordAnalytics import technical_density, keyword_clustering, calculate_final_score
from src.Analysis.skillsExtractCoding import extract_skills_from_folder


# ============================================
# CODE EFFICIENCY INTEGRATION
# ============================================

def analyze_code_efficiency(project: Project) -> Dict[str, Any]:
    """
    Analyze code efficiency for a coding project using codeEfficiency.py
    
    Calculates time and space complexity scores for code files in the project.
    
    Args:
        project: Project object from database
        
    Returns:
        Dictionary with efficiency scores and analysis
    """
    if project.project_type != 'code':
        return {
            'error': f'Project type is {project.project_type}, not code',
            'efficiency_available': False
        }
    
    # Get code files from project
    files = db_manager.get_files_for_project(project.id)
    
    if not files:
        return {
            'efficiency_available': False,
            'message': 'No files found for analysis'
        }
    
    # Analyze each code file
    efficiency_results = []
    total_time_score = 0
    total_space_score = 0
    total_efficiency_score = 0
    files_analyzed = 0
    
    for file in files:
        file_path = file.file_path
        
        # Skip non-code files
        if not file_path or not os.path.exists(file_path):
            continue
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                code = f.read()
            
            result = grade_efficiency(code, file_path)
            
            if result.get('efficiency_score') is not None:
                efficiency_results.append({
                    'file': file.file_name,
                    'time_score': result.get('time_score'),
                    'space_score': result.get('space_score'),
                    'efficiency_score': result.get('efficiency_score'),
                    'max_loop_depth': result.get('max_loop_depth', 0),
                    'total_loops': result.get('total_loops', 0)
                })
                
                total_time_score += result.get('time_score', 0) or 0
                total_space_score += result.get('space_score', 0) or 0
                total_efficiency_score += result.get('efficiency_score', 0) or 0
                files_analyzed += 1
        
        except Exception as e:
            continue
    
    if files_analyzed == 0:
        return {
            'efficiency_available': False,
            'message': 'Could not analyze any files'
        }
    
    # Calculate averages
    avg_time_score = round(total_time_score / files_analyzed, 2)
    avg_space_score = round(total_space_score / files_analyzed, 2)
    avg_efficiency_score = round(total_efficiency_score / files_analyzed, 2)
    
    # Determine efficiency level
    if avg_efficiency_score >= 80:
        efficiency_level = 'Highly Efficient'
        bullet_phrase = 'optimized, efficient code'
    elif avg_efficiency_score >= 60:
        efficiency_level = 'Efficient'
        bullet_phrase = 'well-structured code'
    elif avg_efficiency_score >= 40:
        efficiency_level = 'Moderate'
        bullet_phrase = 'functional code'
    else:
        efficiency_level = 'Needs Optimization'
        bullet_phrase = 'code'
    
    return {
        'efficiency_available': True,
        'avg_time_score': avg_time_score,
        'avg_space_score': avg_space_score,
        'avg_efficiency_score': avg_efficiency_score,
        'efficiency_level': efficiency_level,
        'bullet_phrase': bullet_phrase,
        'files_analyzed': files_analyzed,
        'file_details': efficiency_results[:5]  # Top 5 files
    }


# ============================================
# TECHNICAL DENSITY INTEGRATION
# ============================================

def analyze_technical_density(project: Project) -> Dict[str, Any]:
    """
    Analyze technical density of code project using keywordAnalytics.py
    
    Measures code complexity and technical depth through keyword analysis.
    
    Args:
        project: Project object from database
        
    Returns:
        Dictionary with technical density metrics
    """
    if project.project_type != 'code':
        return {
            'error': f'Project type is {project.project_type}, not code',
            'density_available': False
        }
    
    # Get code files from project
    files = db_manager.get_files_for_project(project.id)
    
    if not files:
        return {
            'density_available': False,
            'message': 'No files found for analysis'
        }
    
    # Analyze density for each file
    density_results = []
    total_density = 0
    files_analyzed = 0
    
    for file in files:
        file_path = file.file_path
        
        if not file_path or not os.path.exists(file_path):
            continue
        
        try:
            density_result = technical_density(file_path)
            
            if density_result and 'technical_density' in density_result:
                density_results.append({
                    'file': file.file_name,
                    'density': density_result['technical_density'],
                    'density_raw': density_result.get('technical_density_raw', 0)
                })
                
                total_density += density_result['technical_density']
                files_analyzed += 1
        
        except Exception:
            continue
    
    if files_analyzed == 0:
        return {
            'density_available': False,
            'message': 'Could not analyze technical density'
        }
    
    # Calculate average density
    avg_density = round(total_density / files_analyzed, 3)
    
    # Determine density level
    if avg_density >= 0.7:
        density_level = 'High Technical Depth'
        bullet_phrase = 'advanced technical implementation'
    elif avg_density >= 0.5:
        density_level = 'Moderate Technical Depth'
        bullet_phrase = 'solid technical foundation'
    elif avg_density >= 0.3:
        density_level = 'Standard Technical Depth'
        bullet_phrase = 'functional implementation'
    else:
        density_level = 'Basic Technical Depth'
        bullet_phrase = 'basic implementation'
    
    return {
        'density_available': True,
        'avg_density': avg_density,
        'density_level': density_level,
        'bullet_phrase': bullet_phrase,
        'files_analyzed': files_analyzed,
        'file_details': density_results[:5]  # Top 5 files
    }


# ============================================
# KEYWORD CLUSTERING INTEGRATION
# ============================================

def analyze_keyword_clusters(project: Project) -> Dict[str, Any]:
    """
    Analyze keyword clustering for code project
    
    Groups technical keywords into skill clusters.
    
    Args:
        project: Project object from database
        
    Returns:
        Dictionary with clustered keywords
    """
    if project.project_type != 'code':
        return {
            'error': f'Project type is {project.project_type}, not code',
            'clustering_available': False
        }
    
    # Get a representative code file (largest or first)
    files = db_manager.get_files_for_project(project.id)
    
    if not files:
        return {
            'clustering_available': False,
            'message': 'No files found'
        }
    
    # Find largest code file
    code_files = [f for f in files if f.file_path and os.path.exists(f.file_path)]
    if not code_files:
        return {
            'clustering_available': False,
            'message': 'No accessible code files'
        }
    
    # Use largest file as representative
    largest_file = max(code_files, key=lambda f: f.file_size or 0)
    
    try:
        cluster_df = keyword_clustering(largest_file.file_path)
        
        # Convert DataFrame to dict
        clusters = cluster_df.to_dict('records')
        
        # Get top 3 clusters
        top_clusters = [c['Cluster'] for c in clusters[:3] if c['Cluster'] != 'Uncategorized']
        
        return {
            'clustering_available': True,
            'top_clusters': top_clusters,
            'all_clusters': clusters,
            'dominant_cluster': clusters[0]['Cluster'] if clusters else None
        }
    
    except Exception as e:
        return {
            'clustering_available': False,
            'message': f'Clustering failed: {str(e)}'
        }


# ============================================
# SKILL EXTRACTION INTEGRATION
# ============================================

def extract_project_skills(project: Project) -> Dict[str, Any]:
    """
    Extract coding skills from project using skillsExtractCoding.py
    
    Args:
        project: Project object from database
        
    Returns:
        Dictionary with extracted skills and scores
    """
    if project.project_type != 'code':
        return {
            'error': f'Project type is {project.project_type}, not code',
            'skills_available': False
        }
    
    folder_path = project.file_path
    
    if not folder_path or not os.path.exists(folder_path):
        return {
            'skills_available': False,
            'message': 'Project folder not found'
        }
    
    try:
        # Extract skills from folder
        skills_scores = extract_skills_from_folder(folder_path)
        
        if not skills_scores:
            return {
                'skills_available': False,
                'message': 'No skills detected'
            }
        
        # Get top skills
        top_skills = list(skills_scores.keys())[:5]
        
        return {
            'skills_available': True,
            'top_skills': top_skills,
            'skill_scores': skills_scores,
            'primary_skill': top_skills[0] if top_skills else None
        }
    
    except Exception as e:
        return {
            'skills_available': False,
            'message': f'Skill extraction failed: {str(e)}'
        }


# ============================================
# COMPREHENSIVE CODE ANALYSIS
# ============================================

def analyze_code_project_comprehensive(project: Project) -> Dict[str, Any]:
    """
    Perform comprehensive analysis of code project
    
    Combines efficiency, density, clustering, and skill extraction.
    
    Args:
        project: Project object from database
        
    Returns:
        Dictionary with all analysis results
    """
    return {
        'efficiency': analyze_code_efficiency(project),
        'technical_density': analyze_technical_density(project),
        'keyword_clusters': analyze_keyword_clusters(project),
        'skills': extract_project_skills(project)
    }


# ============================================
# BULLET ENHANCEMENT HELPERS
# ============================================

def get_code_quality_phrase(project: Project) -> str:
    """
    Get a quality descriptor phrase based on code analysis
    
    Args:
        project: Project object
        
    Returns:
        Phrase describing code quality (e.g., "optimized, efficient code")
    """
    efficiency = analyze_code_efficiency(project)
    
    if efficiency.get('efficiency_available'):
        return efficiency.get('bullet_phrase', 'well-structured code')
    
    return 'functional code'


def get_technical_depth_phrase(project: Project) -> str:
    """
    Get a technical depth descriptor based on density analysis
    
    Args:
        project: Project object
        
    Returns:
        Phrase describing technical depth
    """
    density = analyze_technical_density(project)
    
    if density.get('density_available'):
        return density.get('bullet_phrase', 'solid technical foundation')
    
    return 'technical implementation'


def should_emphasize_efficiency(project: Project) -> bool:
    """
    Determine if efficiency should be emphasized in bullets
    
    Args:
        project: Project object
        
    Returns:
        True if efficiency scores are high enough to emphasize
    """
    efficiency = analyze_code_efficiency(project)
    
    if efficiency.get('efficiency_available'):
        return efficiency.get('avg_efficiency_score', 0) >= 70
    
    return False


if __name__ == "__main__":
    print("Code Resume Analytics")
    print("=" * 70)
    print("\nThis module provides code-specific analytics:")
    print("  - Code Efficiency Analysis (codeEfficiency.py)")
    print("  - Technical Density Measurement (keywordAnalytics.py)")
    print("  - Keyword Clustering")
    print("  - Skill Extraction (skillsExtractCoding.py)")