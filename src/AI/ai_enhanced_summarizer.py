"""
AI-Enhanced Project Summarizer
========================================

Enhances the existing summarizeProjects.py with AI-powered natural language
descriptions and deep technical insights.

This module maintains backward compatibility with the original summarizer
while adding optional AI enhancement capabilities.

Integration Strategy:
1. Use original summarizer for scoring and ranking
2. Enhance top projects with AI-generated descriptions
3. Cache results to minimize API costs
4. Provide both AI and non-AI modes
"""


import sys
import os
import re
from typing import List, Dict, Any, Optional
from datetime import datetime


# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))


try:
    from src.Analysis.summarizeProjects import summarize_projects as original_summarize
    from src.AI.ai_service import get_ai_service
    from src.Databases.database import db_manager
except ImportError as e:
    print(f"⚠️ Import error: {e}")
    print("Make sure you're running from the project root")
    sys.exit(1)


def ai_enhance_project_summary(
    project_dict: Dict[str, Any],
    ai_service=None,
    include_technical_depth: bool = False
) -> Dict[str, Any]:
    """
    Enhance a single project dictionary with AI-generated description.
    
    Args:
        project_dict: Project data (must have 'project_name' and other fields)
        ai_service: Optional AI service instance (will create if None)
        include_technical_depth: If True, adds technical analysis
    
    Returns:
        Enhanced project dictionary with 'ai_description' field
    """
    if ai_service is None:
        ai_service = get_ai_service()


    # Create a concise prompt focusing on portfolio/resume context
    prompt = f"""Write a 2-3 sentence professional description for this project suitable for a portfolio or resume.
                Focus on: purpose, key technologies, and complexity/scope.

                Project: {project_dict.get('project_name', 'Unnamed Project')}
                Technologies: {', '.join(project_dict.get('skills', [])[:5])}
                Scope: {project_dict.get('file_count', 'Unknown')} files, {project_dict.get('lines_of_code', 'unknown')} lines
                Success Score: {project_dict.get('success_score', 0):.2f}
                Contribution: {project_dict.get('contribution_score', 0):.2f}

                Description:"""


    try:
        description = ai_service.generate_text(
            prompt,
            temperature=0.7,
            max_tokens=150
        )
        project_dict['ai_description'] = description.strip()


        # Optionally add technical depth analysis
        if include_technical_depth:
            tech_prompt = f"""Briefly identify key technical concepts in this project (1-2 sentences).
            Look for: OOP principles, data structures, algorithms, design patterns.

            Project: {project_dict.get('project_name')}
            Technologies: {', '.join(project_dict.get('skills', [])[:8])}

            Technical Concepts:"""


            tech_analysis = ai_service.generate_text(
                tech_prompt,
                temperature=0.3,
                max_tokens=100
            )
            project_dict['technical_insights'] = tech_analysis.strip()


    except Exception as e:
        print(f"⚠️ AI enhancement failed for {project_dict.get('project_name')}: {e}")
        project_dict['ai_description'] = f"A {', '.join(project_dict.get('skills', ['software'])[:2])} project."


    return project_dict


def summarize_projects_with_ai(
    projects: List[Dict[str, Any]],
    top_k: int = 3,
    use_ai: bool = True,
    enhance_all: bool = False,
    include_technical_depth: bool = False,
    weights: Optional[Dict[str, float]] = None,
    diversity_alpha: float = 0.1,
) -> Dict[str, Any]:
    """
    Enhanced version of summarize_projects with optional AI descriptions.
    
    Args:
        projects: List of project dictionaries
        top_k: Number of top projects to select
        use_ai: If True, enhance selected projects with AI descriptions
        enhance_all: If True, enhance ALL projects (not just top k). 
        include_technical_depth: If True, adds technical analysis 
        weights: Scoring weights (passed to original summarizer)
        diversity_alpha: Diversity factor (passed to original summarizer)
    
    Returns:
        Enhanced summary dictionary with AI-generated content
    """
    # Step 1: Use original summarizer for ranking
    result = original_summarize(
        projects=projects,
        top_k=top_k,
        weights=weights,
        diversity_alpha=diversity_alpha
    )


    # Step 2: Optionally enhance with AI
    if not use_ai:
        return result


    print(f"\n🤖 Enhancing projects with AI descriptions...")
    ai_service = get_ai_service()


    # Determine which projects to enhance
    projects_to_enhance = result['all_projects_scored'] if enhance_all else result['selected_projects']


    enhanced_count = 0
    cache_hits = 0


    for project in projects_to_enhance:
        # Check if we already have AI description in DB
        project_name = project.get('project_name', '')
        cached = _get_cached_ai_description(project_name)


        if cached:
            project['ai_description'] = cached
            cache_hits += 1
        else:
            ai_enhance_project_summary(
                project,
                ai_service=ai_service,
                include_technical_depth=include_technical_depth
            )
            # Cache the result
            if 'ai_description' in project:
                _cache_ai_description(project_name, project['ai_description'])


        enhanced_count += 1


    print(f"✅ Enhanced {enhanced_count} projects (💾 {cache_hits} from cache)")


    # Step 3: Generate AI-powered summary
    if use_ai:
        result['ai_summary'] = _generate_portfolio_summary(result, ai_service)


    return result


def _get_cached_ai_description(project_name: str) -> Optional[str]:
    """Check if we have a cached AI description for this project in the database."""
    try:
        # Try to find project by name
        projects = db_manager.get_all_projects()
        for p in projects:
            if p.name == project_name:
                # Check if it has ai_description field
                if hasattr(p, 'ai_description') and p.ai_description:
                    return p.ai_description
        return None
    except Exception:
        return None


def _cache_ai_description(project_name: str, description: str):
    """Cache AI description in the database if project exists."""
    try:
        projects = db_manager.get_all_projects()
        for p in projects:
            if p.name == project_name:
                db_manager.update_project(p.id, {
                    'ai_description': description
                })
                break
    except Exception as e:
        print(f"⚠️ Cache write warning: {e}")


def _generate_portfolio_summary(result: Dict[str, Any], ai_service) -> str:
    """
    Generate an AI-powered portfolio summary based on all projects.
    This creates a cohesive narrative suitable for a professional portfolio.
    """
    # Extract key information
    top_projects = result['selected_projects']
    all_skills = result['unique_skills']
    avg_score = result['average_score']


    # Build context for AI
    project_summaries = []
    for p in top_projects:
        name = p['project_name']
        skills = ', '.join(p['skills'][:3])
        desc = p.get('ai_description', f"A project using {skills}")
        project_summaries.append(f"- {name}: {desc}")


    prompt = f"""Create a professional 3-4 sentence portfolio summary based on these projects.
            Focus on: breadth of skills, notable projects, and overall technical capability.
            Write in third person (e.g., "demonstrates", "has experience in").

            Projects:
            {chr(10).join(project_summaries)}

            All Skills: {', '.join(all_skills[:15])}
            Average Project Score: {avg_score:.2f}/1.00

            Portfolio Summary:"""


    try:
        summary = ai_service.generate_text(
            prompt,
            temperature=0.7,
            max_tokens=200
        )
        return summary.strip()
    except Exception as e:
        print(f"⚠️ AI summary generation failed: {e}")
        return result['summary']  # Fall back to original summary


def generate_resume_bullets(project: Dict[str, Any], num_bullets: int = 3) -> List[str]:
    """
    Generate professional resume bullet points for a project.
    Uses AI to create achievement-focused descriptions.
    """
    ai_service = get_ai_service()


    prompt = f"""Generate exactly {num_bullets} resume bullet points for this project.
            Start each bullet with a number and period (1. 2. 3.).

            Project: {project.get('project_name', 'Project')}
            Technologies: {', '.join(project.get('skills', [])[:6])}
            Context: {project.get('ai_description', '')}
            Score: {project.get('overall_score', 0):.2f}

            Format:
            1. [First bullet starting with action verb]
            2. [Second bullet starting with action verb]
            3. [Third bullet starting with action verb]

            Resume Bullets:"""


    try:
        response = ai_service.generate_text(
            prompt,
            temperature=0.6,
            max_tokens=250
        )


        # DEBUG: Print what we got
        print(f"\n[DEBUG] AI Response:\n{repr(response)}\n")


        # ULTRA-ROBUST PARSING - Handles ANY format
        import re
        bullets = []


        # First, try to find lines that look like bullets
        lines = response.strip().split('\n')


        for line in lines:
            line = line.strip()


            # Skip empty lines and markdown
            if not line or line.startswith('```'):
                continue


            # Remove ALL leading non-letter characters
            # This catches: "1. ", "• ", "- ", "* ", "1) ", etc.
            cleaned = re.sub(r'^[^a-zA-Z]+', '', line).strip()


            # If we got something substantial, keep it
            if cleaned and len(cleaned) >= 15:
                bullets.append(cleaned)
                print(f"[DEBUG] Added bullet: {cleaned[:50]}...")


                if len(bullets) >= num_bullets:
                    break


        print(f"[DEBUG] Total bullets found: {len(bullets)}\n")


        # Return what we found
        if len(bullets) >= num_bullets:
            return bullets[:num_bullets]
        elif len(bullets) > 0:
            # Got some bullets but not enough
            return bullets
        else:
            # Parsing completely failed - return fallback
            print("[DEBUG] Parsing failed, using fallback")
            return [
                f"Developed {project.get('project_name')} using {', '.join(project.get('skills', ['various technologies'])[:3])}",
                f"Implemented features using {', '.join(project.get('skills', ['technologies'])[1:3])}",
                f"Contributed to {project.get('project_name')} project development"
            ][:num_bullets]


    except Exception as e:
        print(f"⚠️ Resume bullet generation failed: {e}")
        return [f"Developed {project.get('project_name')} using {', '.join(project.get('skills', ['various technologies'])[:3])}"]


# CLI Functions


def demo_ai_summarizer():
    """Interactive demo of AI-enhanced summarizer."""
    print("\n" + "="*70)
    print("AI-Enhanced Project Summarizer Demo")
    print("="*70 + "\n")


    # Get projects from database
    from src.Analysis.runSummaryFromDb import fetch_projects_for_summary
    projects = fetch_projects_for_summary()


    if not projects:
        print("📭 No projects found in database")
        return


    print(f"Found {len(projects)} projects\n")


    # Ask for preferences
    print("Options:")
    print("1. Quick summary (original, no AI)")
    print("2. AI-enhanced summary (top projects only)")
    print("3. Full AI analysis (all projects + technical depth)")


    choice = input("\nChoice (1-3): ").strip()


    # Configure based on choice
    use_ai = choice in ['2', '3']
    enhance_all = choice == '3'
    include_tech = choice == '3'


    # Run summarizer
    print("\n🔄 Processing...\n")


    result = summarize_projects_with_ai(
        projects=projects,
        top_k=min(5, len(projects)),
        use_ai=use_ai,
        enhance_all=enhance_all,
        include_technical_depth=include_tech
    )


    # Display results
    print("\n" + "="*70)
    print("📊 Results")
    print("="*70 + "\n")


    # Show AI summary if available
    if 'ai_summary' in result:
        print("🤖 AI-Generated Portfolio Summary:")
        print(result['ai_summary'])
        print()
    else:
        print("📝 Summary:")
        print(result['summary'])
        print()


    # Show top projects
    print(f"🏆 Top {len(result['selected_projects'])} Projects:\n")


    for i, proj in enumerate(result['selected_projects'], 1):
        print(f"{i}. {proj['project_name']} (Score: {proj['overall_score']:.3f})")
        print(f"   Skills: {', '.join(proj['skills'][:5])}")


        if 'ai_description' in proj:
            print(f"   📝 {proj['ai_description']}")


        if 'technical_insights' in proj:
            print(f"   🔬 {proj['technical_insights']}")


        print()


    # Offer to generate resume bullets
    if use_ai:
        gen_bullets = input("Generate resume bullets for top project? (yes/no): ").strip().lower()
        if gen_bullets == 'yes' and result['selected_projects']:
            print("\n📋 Resume Bullets:\n")
            bullets = generate_resume_bullets(result['selected_projects'][0])
            for bullet in bullets:
                print(f"• {bullet}")


if __name__ == "__main__":

    demo_ai_summarizer()