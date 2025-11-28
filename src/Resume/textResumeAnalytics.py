"""

Text-specific resume analytics functions.

Features:
- Integration with skillsExtractDocs.py for writing skill detection
- Writing quality assessment
- Publication readiness validation
- Content volume analysis
"""

import os
import sys
from typing import Dict, Any, List, Optional

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.Databases.database import db_manager, Project
from src.Analysis.skillsExtractDocs import analyze_folder_for_skills, analyze_document_for_skills


# ============================================
# WRITING SKILL EXTRACTION INTEGRATION
# ============================================

def extract_writing_skills(project: Project) -> Dict[str, Any]:
    """
    Extract writing skills from text project using skillsExtractDocs.py
    
    Args:
        project: Project object from database
        
    Returns:
        Dictionary with detected writing skills
    """
    if project.project_type != 'text':
        return {
            'error': f'Project type is {project.project_type}, not text',
            'skills_available': False
        }
    
    folder_path = project.file_path
    
    if not folder_path or not os.path.exists(folder_path):
        return {
            'skills_available': False,
            'message': 'Project folder not found'
        }
    
    try:
        # Analyze folder for skills
        skills_with_counts = analyze_folder_for_skills(folder_path)
        
        if not skills_with_counts:
            return {
                'skills_available': False,
                'message': 'No writing skills detected'
            }
        
        # Extract top skills
        top_skills = [skill for skill, count in skills_with_counts[:5]]
        skill_scores = {skill: count for skill, count in skills_with_counts}
        
        return {
            'skills_available': True,
            'top_skills': top_skills,
            'skill_scores': skill_scores,
            'primary_skill': top_skills[0] if top_skills else None
        }
    
    except Exception as e:
        return {
            'skills_available': False,
            'message': f'Skill extraction failed: {str(e)}'
        }


# ============================================
# WRITING QUALITY ANALYSIS
# ============================================

def analyze_writing_quality(project: Project) -> Dict[str, Any]:
    """
    Assess writing quality based on portfolio metrics
    
    Scoring based on:
    - Word count (volume)
    - Document diversity
    - Writing skills demonstrated
    
    Args:
        project: Project object from database
        
    Returns:
        Dictionary with quality score and analysis
    """
    if project.project_type != 'text':
        return {
            'error': f'Project type is {project.project_type}, not text',
            'quality_available': False
        }
    
    quality_score = 0
    insights = []
    
    # Word count analysis (30 points)
    word_count = project.word_count or 0
    if word_count >= 50000:
        quality_score += 30
        insights.append(f"✅ Extensive writing portfolio ({word_count//1000}K+ words) - book-length content")
    elif word_count >= 20000:
        quality_score += 25
        insights.append(f"⚠️  Substantial content ({word_count//1000}K+ words)")
    elif word_count >= 5000:
        quality_score += 15
        insights.append(f"📊 Moderate portfolio ({word_count//1000}K+ words)")
    else:
        insights.append(f"❌ Limited content ({word_count} words) - aim for 10K+ words")
    
    # Document diversity (35 points)
    file_count = project.file_count or 0
    if file_count >= 20:
        quality_score += 35
        insights.append(f"✅ Diverse portfolio with {file_count}+ documents")
    elif file_count >= 10:
        quality_score += 25
        insights.append(f"⚠️  Good variety with {file_count}+ documents")
    elif file_count >= 5:
        quality_score += 15
        insights.append(f"📊 Moderate variety with {file_count} documents")
    else:
        insights.append(f"❌ Limited variety ({file_count} documents) - aim for 10+")
    
    # Writing skills (35 points)
    skills = extract_writing_skills(project)
    if skills.get('skills_available'):
        skill_count = len(skills.get('top_skills', []))
        if skill_count >= 5:
            quality_score += 35
            insights.append(f"✅ Demonstrates {skill_count} writing competencies")
        elif skill_count >= 3:
            quality_score += 25
            insights.append(f"⚠️  Shows {skill_count} writing skills")
        else:
            quality_score += 15
            insights.append(f"📊 Basic skill demonstration ({skill_count} skills)")
    else:
        insights.append("❌ Writing skills not detected")
    
    # Determine quality level
    if quality_score >= 80:
        quality_level = "Professional"
        writing_type = "professional-grade"
    elif quality_score >= 60:
        quality_level = "Intermediate"
        writing_type = "competent"
    elif quality_score >= 40:
        quality_level = "Developing"
        writing_type = "developing"
    else:
        quality_level = "Beginner"
        writing_type = "foundational"
    
    return {
        'quality_available': True,
        'quality_score': quality_score,
        'quality_level': quality_level,
        'writing_type': writing_type,
        'insights': insights
    }


# ============================================
# PUBLICATION READINESS VALIDATION
# ============================================

def validate_publication_readiness(project: Project) -> Dict[str, Any]:
    """
    Check if writing portfolio meets publication standards
    
    Checklist:
    - Minimum word count (5K+ for articles)
    - Document variety (5+ pieces)
    - Professional skills (3+ demonstrated)
    - Editorial polish (editing skills present)
    
    Args:
        project: Project object from database
        
    Returns:
        Dictionary with readiness assessment
    """
    if project.project_type != 'text':
        return {
            'error': f'Project type is {project.project_type}, not text',
            'readiness_available': False
        }
    
    # Extract skills for editorial check
    skills = extract_writing_skills(project)
    skill_list = skills.get('top_skills', []) if skills.get('skills_available') else []
    
    # Check for editorial skills
    editorial_skills = ['editing', 'proofreading', 'revising']
    has_editorial = any(skill.lower() in ' '.join(skill_list).lower() for skill in editorial_skills)
    
    checklist = {
        'sufficient_length': {
            'pass': (project.word_count or 0) >= 5000,
            'current': project.word_count or 0,
            'target': 5000,
            'label': 'Minimum Word Count'
        },
        'document_variety': {
            'pass': (project.file_count or 0) >= 5,
            'current': project.file_count or 0,
            'target': 5,
            'label': 'Document Variety'
        },
        'professional_skills': {
            'pass': len(skill_list) >= 3,
            'current': len(skill_list),
            'target': 3,
            'label': 'Writing Skills'
        },
        'editorial_polish': {
            'pass': has_editorial,
            'current': 1 if has_editorial else 0,
            'target': 1,
            'label': 'Editorial Skills'
        }
    }
    
    # Calculate score (25% per item)
    score = sum(25 for item in checklist.values() if item['pass'])
    
    # Generate recommendations
    recommendations = []
    if not checklist['sufficient_length']['pass']:
        current = checklist['sufficient_length']['current']
        needed = checklist['sufficient_length']['target'] - current
        recommendations.append(f"📝 Add {needed} more words (currently: {current})")
    
    if not checklist['document_variety']['pass']:
        current = checklist['document_variety']['current']
        needed = checklist['document_variety']['target'] - current
        recommendations.append(f"📄 Create {needed} more document{'s' if needed != 1 else ''} (currently: {current})")
    
    if not checklist['professional_skills']['pass']:
        current = checklist['professional_skills']['current']
        needed = checklist['professional_skills']['target'] - current
        recommendations.append(f"✍️  Demonstrate {needed} more writing skill{'s' if needed != 1 else ''} (currently: {current})")
    
    if not checklist['editorial_polish']['pass']:
        recommendations.append("📖 Include evidence of editing/proofreading skills")
    
    # Determine readiness
    if score >= 100:
        readiness_level = "Publication Ready"
        status = "✅ Portfolio meets publication standards"
    elif score >= 75:
        readiness_level = "Nearly Ready"
        status = "⚠️  Portfolio is strong, minor polish needed"
    elif score >= 50:
        readiness_level = "Developing"
        status = "📊 Portfolio needs strengthening"
    else:
        readiness_level = "Not Ready"
        status = "❌ Portfolio needs significant development"
    
    return {
        'readiness_available': True,
        'publication_score': score,
        'readiness_level': readiness_level,
        'status': status,
        'is_publication_ready': score >= 75,
        'checklist': checklist,
        'recommendations': recommendations
    }


# ============================================
# CONTENT VOLUME BENCHMARKING
# ============================================

def benchmark_content_volume(project: Project) -> Dict[str, Any]:
    """
    Benchmark writing volume against industry standards
    
    Benchmarks:
    - Blog portfolio: 20-30 posts (500-1000 words each)
    - Technical writing: 5-10 guides (3000+ words each)
    - Academic: 3-5 papers (8000+ words each)
    - Book: 1 manuscript (50,000-100,000 words)
    
    Args:
        project: Project object from database
        
    Returns:
        Dictionary with benchmark comparison
    """
    if project.project_type != 'text':
        return {
            'error': f'Project type is {project.project_type}, not text',
            'benchmark_available': False
        }
    
    benchmarks = {
        'blog_portfolio': {
            'target_docs': 25,
            'target_words': 20000,
            'description': 'Blog/Article Portfolio'
        },
        'technical_portfolio': {
            'target_docs': 8,
            'target_words': 25000,
            'description': 'Technical Writing Portfolio'
        },
        'academic_portfolio': {
            'target_docs': 4,
            'target_words': 35000,
            'description': 'Academic Writing Portfolio'
        },
        'book_manuscript': {
            'target_docs': 1,
            'target_words': 60000,
            'description': 'Book Manuscript'
        }
    }
    
    current_docs = project.file_count or 0
    current_words = project.word_count or 0
    
    # Find best matching benchmark
    best_match = None
    best_score = 0
    
    for name, bench in benchmarks.items():
        doc_ratio = min(current_docs / bench['target_docs'], 1.0) if current_docs else 0
        word_ratio = min(current_words / bench['target_words'], 1.0) if current_words else 0
        score = (doc_ratio + word_ratio) / 2
        
        if score > best_score:
            best_score = score
            best_match = name
    
    # Default to blog_portfolio if no match found
    if best_match is None:
        best_match = 'blog_portfolio'
    
    selected = benchmarks[best_match]
    
    return {
        'benchmark_available': True,
        'benchmark_type': selected['description'],
        'completion_percentage': round(best_score * 100, 1),
        'target_docs': selected['target_docs'],
        'current_docs': current_docs,
        'target_words': selected['target_words'],
        'current_words': current_words,
        'on_track': best_score >= 0.75
    }


# ============================================
# WRITING STYLE IDENTIFICATION
# ============================================

def identify_writing_style(project: Project) -> Dict[str, Any]:
    """
    Identify writing style based on skills and content
    
    Styles: academic, technical, creative, business, journalistic
    
    Args:
        project: Project object from database
        
    Returns:
        Dictionary with identified style
    """
    if project.project_type != 'text':
        return {
            'error': f'Project type is {project.project_type}, not text',
            'style_available': False
        }
    
    skills = extract_writing_skills(project)
    
    if not skills.get('skills_available'):
        return {
            'style_available': False,
            'message': 'Cannot determine style without skills'
        }
    
    skill_list = skills.get('top_skills', [])
    skill_text = ' '.join(skill_list).lower()
    
    # Detect style based on skills
    styles = {
        'academic': ['research_writing', 'critical_thinking'],
        'technical': ['technical_writing'],
        'creative': ['creative_writing'],
        'business': ['content_writing', 'communication'],
        'journalistic': ['journalistic_writing']
    }
    
    style_scores = {}
    for style, keywords in styles.items():
        score = sum(1 for kw in keywords if kw in skill_text)
        if score > 0:
            style_scores[style] = score
    
    if not style_scores:
        primary_style = 'general'
    else:
        primary_style = max(style_scores, key=style_scores.get)
    
    # Style-specific emphasis
    emphasis_map = {
        'academic': 'rigorous research and scholarly writing',
        'technical': 'clear, accessible technical documentation',
        'creative': 'compelling narratives and storytelling',
        'business': 'professional business communication',
        'journalistic': 'informative, engaging journalism',
        'general': 'versatile writing across formats'
    }
    
    return {
        'style_available': True,
        'primary_style': primary_style,
        'emphasis': emphasis_map[primary_style],
        'style_scores': style_scores
    }


# ============================================
# COMPREHENSIVE TEXT ANALYSIS
# ============================================

def analyze_text_project_comprehensive(project: Project) -> Dict[str, Any]:
    """
    Perform comprehensive analysis of text project
    
    Combines all text-specific analyses.
    
    Args:
        project: Project object from database
        
    Returns:
        Dictionary with all analysis results
    """
    return {
        'writing_skills': extract_writing_skills(project),
        'writing_quality': analyze_writing_quality(project),
        'publication_readiness': validate_publication_readiness(project),
        'content_benchmark': benchmark_content_volume(project),
        'writing_style': identify_writing_style(project)
    }


# ============================================
# BULLET ENHANCEMENT HELPERS
# ============================================

def get_writing_quality_phrase(project: Project) -> str:
    """
    Get a quality descriptor phrase for writing
    
    Args:
        project: Project object
        
    Returns:
        Phrase describing writing quality
    """
    quality = analyze_writing_quality(project)
    
    if quality.get('quality_available'):
        return quality.get('writing_type', 'competent') + ' writing'
    
    return 'written content'


def get_volume_descriptor(project: Project) -> str:
    """
    Get a volume descriptor based on word count
    
    Args:
        project: Project object
        
    Returns:
        Phrase describing content volume
    """
    word_count = project.word_count or 0
    
    if word_count >= 50000:
        return 'extensive'
    elif word_count >= 20000:
        return 'substantial'
    elif word_count >= 10000:
        return 'comprehensive'
    else:
        return 'focused'


def should_emphasize_publication_ready(project: Project) -> bool:
    """
    Determine if publication readiness should be emphasized
    
    Args:
        project: Project object
        
    Returns:
        True if portfolio is publication-ready
    """
    readiness = validate_publication_readiness(project)
    
    if readiness.get('readiness_available'):
        return readiness.get('is_publication_ready', False)
    
    return False


if __name__ == "__main__":
    print("Text Resume Analytics")
    print("=" * 70)
    print("\nThis module provides text-specific analytics:")
    print("  - Writing Skill Extraction (skillsExtractDocs.py)")
    print("  - Writing Quality Assessment")
    print("  - Publication Readiness Validation")
    print("  - Content Volume Benchmarking")
    print("  - Writing Style Identification")