"""
Shared resume analytics functions that apply to ALL project types.

Features:
- ATS (Applicant Tracking System) optimization scoring
- Before/After comparison for bullet transformation
- Role-level targeted bullet generation (Junior/Mid/Senior/Lead)
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
    'Produced', 'Crafted', 'Authored', 'Published', 'Analyzed', 'Researched'
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
# BEFORE/AFTER COMPARISON
# ============================================

def improve_bullet(bullet: str, project: Project, used_additions: Dict[str, bool] = None) -> tuple:
    """
    Improve a single bullet point based on ATS analysis.
    Tracks what additions have been used to avoid repetition.
    
    Args:
        bullet: Current bullet text
        project: Project object for context
        used_additions: Dictionary tracking what's been added already
            Keys: 'loc', 'files', 'size', 'words', 'tech_0', 'tech_1', etc.
        
    Returns:
        Tuple of (improved bullet text, updated used_additions dict)
    """
    if used_additions is None:
        used_additions = {}
    
    score_data = calculate_ats_score(bullet, project.project_type)
    improved = bullet
    
    # Get first word (verb)
    words = improved.split()
    if not words:
        return improved, used_additions
    
    current_verb = words[0]
    
    # 1. Upgrade weak action verb (only if not already strong)
    if current_verb not in STRONG_ACTION_VERBS:
        if project.project_type == 'code':
            new_verb = 'Developed'
        elif project.project_type == 'visual_media':
            new_verb = 'Designed'
        else:
            new_verb = 'Authored'
        words[0] = new_verb
        improved = ' '.join(words)
    
    # 2. Add metrics if missing (use different metrics for each bullet)
    if not score_data['has_metrics']:
        metric_added = False
        
        if project.project_type == 'code':
            # Try LOC first
            if not used_additions.get('loc') and project.lines_of_code and project.lines_of_code > 0:
                loc = project.lines_of_code
                if loc >= 1000:
                    metric = f"comprising {loc//1000}K+ lines of code"
                else:
                    metric = f"comprising {loc}+ lines of code"
                improved = improved.rstrip('.,') + f", {metric}"
                used_additions['loc'] = True
                metric_added = True
            # Try file count
            elif not used_additions.get('files') and project.file_count and project.file_count > 0:
                improved = improved.rstrip('.,') + f", spanning {project.file_count}+ files"
                used_additions['files'] = True
                metric_added = True
            # Try size
            elif not used_additions.get('size') and project.total_size_bytes and project.total_size_bytes > 0:
                size_kb = project.total_size_bytes / 1024
                if size_kb >= 1000:
                    improved = improved.rstrip('.,') + f", totaling {size_kb/1024:.1f} MB of code"
                else:
                    improved = improved.rstrip('.,') + f", totaling {size_kb:.0f} KB of code"
                used_additions['size'] = True
                metric_added = True
                
        elif project.project_type == 'visual_media':
            # Try file count first
            if not used_additions.get('files') and project.file_count and project.file_count > 0:
                improved = improved.rstrip('.,') + f", delivering {project.file_count}+ assets"
                used_additions['files'] = True
                metric_added = True
            # Try size
            elif not used_additions.get('size') and project.total_size_bytes and project.total_size_bytes > 0:
                size_mb = project.total_size_bytes / (1024 * 1024)
                if size_mb >= 1000:
                    improved = improved.rstrip('.,') + f", totaling {size_mb/1024:.1f} GB of content"
                else:
                    improved = improved.rstrip('.,') + f", totaling {size_mb:.0f} MB of content"
                used_additions['size'] = True
                metric_added = True
                
        else:  # text
            # Try word count first
            if not used_additions.get('words') and project.word_count and project.word_count > 0:
                wc = project.word_count
                if wc >= 1000:
                    improved = improved.rstrip('.,') + f", totaling {wc//1000}K+ words"
                else:
                    improved = improved.rstrip('.,') + f", totaling {wc}+ words"
                used_additions['words'] = True
                metric_added = True
            # Try document count
            elif not used_additions.get('files') and project.file_count and project.file_count > 0:
                improved = improved.rstrip('.,') + f", comprising {project.file_count}+ documents"
                used_additions['files'] = True
                metric_added = True
    
    # 3. Add technical keywords if missing (use different keywords for each bullet)
    if len(score_data['keywords']) < 2:
        if project.languages:
            # Find an unused language/tech
            for i, tech in enumerate(project.languages):
                tech_key = f'tech_{i}'
                if not used_additions.get(tech_key) and tech.lower() not in improved.lower():
                    if project.project_type == 'code':
                        improved = improved.rstrip('.,') + f" using {tech}"
                    else:
                        improved = improved.rstrip('.,') + f" with {tech}"
                    used_additions[tech_key] = True
                    break
    
    return improved, used_additions


def generate_before_after_comparison(project: Project, current_bullet: str, 
                                      used_additions: Dict[str, bool] = None) -> tuple:
    """
    Generate before/after comparison showing bullet transformation.
    Takes the current bullet and generates an improved version.
    
    Args:
        project: Project object from database
        current_bullet: The current bullet to improve
        used_additions: Dictionary tracking what's been added (for batch processing)
        
    Returns:
        Tuple of (comparison dict, updated used_additions)
    """
    if used_additions is None:
        used_additions = {}
    
    # Score current bullet
    current_score = calculate_ats_score(current_bullet, project.project_type)
    
    # Generate improved bullet (tracking used additions)
    improved_bullet, used_additions = improve_bullet(current_bullet, project, used_additions)
    improved_score = calculate_ats_score(improved_bullet, project.project_type)
    
    # Calculate improvements
    improvements = []
    
    # Check verb improvement
    current_verb = current_bullet.split()[0] if current_bullet else ""
    improved_verb = improved_bullet.split()[0] if improved_bullet else ""
    if improved_verb != current_verb and improved_verb in STRONG_ACTION_VERBS:
        improvements.append(f"Upgraded action verb: '{current_verb}' → '{improved_verb}'")
    
    # Check metrics added
    if improved_score['has_metrics'] and not current_score['has_metrics']:
        improvements.append("Added quantifiable metrics")
    
    # Check keywords added
    new_keywords = set(improved_score['keywords']) - set(current_score['keywords'])
    if new_keywords:
        improvements.append(f"Added technical keywords: {', '.join(list(new_keywords)[:3])}")
    
    # Check word count change
    if improved_score['word_count'] > current_score['word_count']:
        improvements.append(f"Added detail ({current_score['word_count']} → {improved_score['word_count']} words)")
    
    # Check score improvement
    if improved_score['score'] > current_score['score']:
        improvement_points = improved_score['score'] - current_score['score']
        improvements.append(f"ATS score improved by +{improvement_points} points")
    
    # If no improvements were made
    if not improvements:
        improvements.append("Bullet already well-optimized")
    
    # Calculate improvement percentage
    if current_score['score'] > 0:
        improvement_percentage = round(
            ((improved_score['score'] - current_score['score']) / current_score['score']) * 100, 1
        )
    else:
        improvement_percentage = 0
    
    comparison = {
        'before': {
            'bullet': current_bullet,
            'ats_score': current_score['score'],
            'grade': current_score['grade'],
            'word_count': current_score['word_count']
        },
        'after': {
            'bullet': improved_bullet,
            'ats_score': improved_score['score'],
            'grade': improved_score['grade'],
            'word_count': improved_score['word_count']
        },
        'improvements': improvements,
        'improvement_percentage': improvement_percentage
    }
    
    return comparison, used_additions


def generate_all_improved_bullets(project: Project, current_bullets: List[str]) -> List[str]:
    """
    Generate improved versions of all bullets with unique additions.
    
    Args:
        project: Project object
        current_bullets: List of current bullets
        
    Returns:
        List of improved bullets
    """
    improved_bullets = []
    used_additions = {}  # Track what's been added across all bullets
    
    for bullet in current_bullets:
        improved, used_additions = improve_bullet(bullet, project, used_additions)
        improved_bullets.append(improved)
    
    return improved_bullets


# ============================================
# ROLE-LEVEL TARGETED BULLETS
# ============================================

# Role-specific action verbs (universal - work for any profession)
ROLE_SPECIFIC_VERBS = {
    'junior': ['Developed', 'Built', 'Created', 'Produced', 'Contributed', 'Assisted'],
    'mid': ['Designed', 'Delivered', 'Managed', 'Executed', 'Implemented', 'Developed'],
    'senior': ['Led', 'Established', 'Spearheaded', 'Drove', 'Pioneered', 'Oversaw'],
    'lead': ['Directed', 'Orchestrated', 'Championed', 'Transformed', 'Strategized', 'Scaled']
}

# Role-specific emphasis phrases (5 unique options per role level - UNIVERSAL for any profession)
ROLE_EMPHASIS = {
    'junior': {
        'code': [
            'while building practical skills and technical foundation',
            'contributing to team deliverables and project milestones',
            'gaining hands-on experience with industry tools',
            'following established standards and best practices',
            'collaborating with senior team members on implementation'
        ],
        'visual_media': [
            'while developing creative and technical abilities',
            'contributing to project deliverables and deadlines',
            'gaining hands-on experience with professional tools',
            'following brand guidelines and design standards',
            'collaborating with senior creatives on production'
        ],
        'text': [
            'while developing professional writing capabilities',
            'contributing to publication deadlines and content goals',
            'gaining hands-on experience with editorial workflows',
            'following style guides and quality standards',
            'collaborating with senior editors on final drafts'
        ]
    },
    'mid': {
        'code': [
            'ensuring quality and long-term maintainability',
            'delivering polished solutions within project timelines',
            'owning end-to-end development of key features',
            'implementing thorough testing and documentation',
            'optimizing performance and resource efficiency'
        ],
        'visual_media': [
            'ensuring consistency and professional quality',
            'delivering polished work within project timelines',
            'owning creative direction for key deliverables',
            'implementing feedback from stakeholder reviews',
            'optimizing workflows for improved output quality'
        ],
        'text': [
            'ensuring clarity, accuracy, and audience engagement',
            'delivering publication-ready content on deadline',
            'owning editorial direction for key pieces',
            'implementing rigorous fact-checking and revision',
            'optimizing content for target audience and platform'
        ]
    },
    'senior': {
        'code': [
            'establishing standards and best practices for the team',
            'mentoring junior team members on technical skills',
            'driving key decisions and quality improvements',
            'ensuring scalability and long-term sustainability',
            'leading technical initiatives and process improvements'
        ],
        'visual_media': [
            'establishing creative standards and style guidelines',
            'mentoring junior designers on professional skills',
            'driving creative vision and quality benchmarks',
            'ensuring consistency across all project deliverables',
            'leading creative initiatives and process improvements'
        ],
        'text': [
            'establishing editorial standards and style guidelines',
            'mentoring junior writers on professional craft',
            'driving content strategy and quality benchmarks',
            'ensuring consistency across all publications',
            'leading editorial initiatives and process improvements'
        ]
    },
    'lead': {
        'code': [
            'driving alignment with organizational objectives',
            'scaling team capabilities and operational excellence',
            'transforming processes and technical infrastructure',
            'defining strategic roadmap and long-term vision',
            'building high-performing teams and culture'
        ],
        'visual_media': [
            'driving alignment with brand and business objectives',
            'scaling creative operations and team capabilities',
            'transforming creative processes and workflows',
            'defining creative strategy and long-term vision',
            'building high-performing creative teams and culture'
        ],
        'text': [
            'driving alignment with communication objectives',
            'scaling editorial operations and team capabilities',
            'transforming content strategy and distribution',
            'defining editorial roadmap and long-term vision',
            'building high-performing editorial teams and culture'
        ]
    }
}


def get_role_appropriate_verb(role_level: str, project_type: str = 'code') -> str:
    """
    Get an appropriate action verb for the role level
    
    Args:
        role_level: 'junior', 'mid', 'senior', or 'lead'
        project_type: Type of project
        
    Returns:
        Appropriate action verb
    """
    if role_level not in ROLE_SPECIFIC_VERBS:
        role_level = 'mid'  # Default
    
    return ROLE_SPECIFIC_VERBS[role_level][0]


def generate_role_context(project: Project, role_level: str) -> Dict[str, str]:
    """
    Generate role-appropriate context for bullet generation
    
    Args:
        project: Project object
        role_level: Target role level
        
    Returns:
        Dictionary with role-appropriate framing
    """
    contributors = db_manager.get_contributors_for_project(project.id)
    team_size = len(contributors)
    
    contexts = {
        'junior': {
            'focus': 'implementation and learning',
            'team_phrase': f'Collaborated with {team_size}-person team' if team_size > 1 else 'Independently developed',
            'emphasis': 'building practical skills',
            'complexity': 'functional components'
        },
        'mid': {
            'focus': 'design and delivery',
            'team_phrase': f'Contributed to {team_size}-person team' if team_size > 1 else 'Owned end-to-end development',
            'emphasis': 'maintainability and performance',
            'complexity': 'complete features'
        },
        'senior': {
            'focus': 'architecture and leadership',
            'team_phrase': f'Led team of {team_size} developers' if team_size > 1 else 'Established technical foundation',
            'emphasis': 'scalability and best practices',
            'complexity': 'system architecture'
        },
        'lead': {
            'focus': 'strategy and business impact',
            'team_phrase': f'Directed cross-functional team of {team_size} engineers' if team_size > 1 else 'Championed technical excellence',
            'emphasis': 'business objectives and innovation',
            'complexity': 'strategic initiatives'
        }
    }
    
    return contexts.get(role_level, contexts['mid'])


def improve_bullet_for_role(bullet: str, project: Project, role_level: str, 
                            used_verbs: List[str] = None, used_emphasis_indices: List[int] = None) -> tuple:
    """
    Enhance a bullet for a specific role level.
    
    Args:
        bullet: Current bullet text
        project: Project object for context
        role_level: Target role level ('junior', 'mid', 'senior', 'lead')
        used_verbs: List of already used verbs to avoid repetition
        used_emphasis_indices: List of already used emphasis indices to avoid repetition
        
    Returns:
        Tuple of (enhanced bullet text, used verb, used emphasis index)
    """
    if used_verbs is None:
        used_verbs = []
    if used_emphasis_indices is None:
        used_emphasis_indices = []
    
    if role_level not in ROLE_SPECIFIC_VERBS:
        role_level = 'mid'
    
    words = bullet.split()
    if not words:
        return bullet, None, None
    
    project_type = project.project_type or 'code'
    
    # 1. Select role-appropriate verb (avoid repetition)
    available_verbs = [v for v in ROLE_SPECIFIC_VERBS[role_level] if v not in used_verbs]
    if not available_verbs:
        available_verbs = ROLE_SPECIFIC_VERBS[role_level]
    new_verb = available_verbs[0]
    
    # 2. Extract the core content (remove old verb)
    core_content = ' '.join(words[1:])
    
    # 3. Select unique emphasis phrase (avoid repetition)
    emphasis_options = ROLE_EMPHASIS.get(role_level, {}).get(project_type, [
        'delivering quality solutions',
        'meeting project objectives',
        'supporting team goals',
        'ensuring successful outcomes',
        'achieving key milestones'
    ])
    
    # Find an unused emphasis index
    available_indices = [i for i in range(len(emphasis_options)) if i not in used_emphasis_indices]
    if not available_indices:
        # All used, reset but try to pick different from last used
        available_indices = list(range(len(emphasis_options)))
    
    emphasis_index = available_indices[0]
    emphasis = emphasis_options[emphasis_index]
    
    # 4. Build role-enhanced bullet
    # Remove trailing punctuation from core content for clean appending
    core_content = core_content.rstrip('.,;')
    enhanced = f"{new_verb} {core_content}, {emphasis}"
    
    # Clean up any double spaces or awkward punctuation
    enhanced = re.sub(r'\s+', ' ', enhanced)
    enhanced = re.sub(r',\s*,', ',', enhanced)
    enhanced = enhanced.strip()
    
    return enhanced, new_verb, emphasis_index


def improve_all_bullets_for_role(bullets: List[str], project: Project, role_level: str) -> List[str]:
    """
    Enhance all bullets for a specific role level with unique extensions.
    
    Args:
        bullets: List of current bullets
        project: Project object for context
        role_level: Target role level
        
    Returns:
        List of role-enhanced bullets
    """
    improved = []
    used_verbs = []
    used_emphasis_indices = []
    
    for bullet in bullets:
        enhanced, used_verb, used_emphasis_idx = improve_bullet_for_role(
            bullet, project, role_level, used_verbs, used_emphasis_indices
        )
        improved.append(enhanced)
        
        # Track used verb and emphasis
        if used_verb:
            used_verbs.append(used_verb)
        if used_emphasis_idx is not None:
            used_emphasis_indices.append(used_emphasis_idx)
    
    return improved


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
    print("  - Before/After Comparison")
    print("  - Role-Level Context Generation")
    print("  - Success Evidence Utilities")