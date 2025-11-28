"""
Resume Bullet Generator Menu
=============================

Unified interface for generating, viewing, improving, and managing
resume bullets for projects in the database.

Features:
- Generate bullets for any project type (code/media/text)
- View stored bullets with metadata
- Improve bullets with analytics (role-level, ATS, type-specific)
- Side-by-side comparison before replacing
- Delete stored bullets

Usage:
    from src.Resume.resumeMenu import run_resume_menu
    run_resume_menu()
"""

import os
import sys
from typing import List, Tuple, Optional, Dict, Any

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.Databases.database import db_manager, Project
from src.Resume.codeBulletGenerator import CodeBulletGenerator
from src.Resume.mediaBulletGenerator import MediaBulletGenerator
from src.Resume.textBulletGenerator import TextBulletGenerator
from src.Resume.resumeAnalytics import (
    calculate_ats_score, generate_before_after_comparison,
    generate_role_context, get_role_appropriate_verb, score_all_bullets
)
from src.Resume.codeResumeAnalytics import analyze_code_project_comprehensive
from src.Resume.mediaResumeAnalytics import analyze_media_project_comprehensive
from src.Resume.textResumeAnalytics import analyze_text_project_comprehensive


# ============================================
# HELPER FUNCTIONS
# ============================================

def list_all_projects_with_indicators() -> List[Tuple[Project, bool]]:
    """
    Get all projects with indicator if they have bullets
    
    Returns:
        List of tuples: (project, has_bullets_bool)
    """
    projects = db_manager.get_all_projects()
    return [(project, project.bullets is not None) for project in projects]


def display_projects_menu(projects_with_indicators: List[Tuple[Project, bool]]) -> None:
    """Display projects with bullet indicators"""
    print("\n" + "="*60)
    print("PROJECTS")
    print("="*60)
    
    if not projects_with_indicators:
        print("No projects found in database.")
        return
    
    for i, (project, has_bullets) in enumerate(projects_with_indicators, 1):
        indicator = "[✓]" if has_bullets else "[ ]"
        project_type = project.project_type or "unknown"
        print(f"{i}. {indicator} {project.name} ({project_type})")
    
    print()


def select_project_interactive() -> Optional[Project]:
    """
    Let user select a project interactively
    
    Returns:
        Selected Project object or None if cancelled
    """
    projects_with_indicators = list_all_projects_with_indicators()
    
    if not projects_with_indicators:
        print("No projects available.")
        input("Press Enter to continue...")
        return None
    
    display_projects_menu(projects_with_indicators)
    
    try:
        choice = input("Select project number (or 'c' to cancel): ").strip()
        if choice.lower() == 'c':
            return None
        
        idx = int(choice) - 1
        if 0 <= idx < len(projects_with_indicators):
            return projects_with_indicators[idx][0]
        else:
            print("Invalid selection.")
            input("Press Enter to continue...")
            return None
    except ValueError:
        print("Invalid input.")
        input("Press Enter to continue...")
        return None


def show_side_by_side_comparison(old_bullets: List[str], new_bullets: List[str]) -> None:
    """
    Display side-by-side comparison of old and new bullets
    
    Args:
        old_bullets: Current bullets
        new_bullets: Improved bullets
    """
    print("\n" + "="*80)
    print("BULLET COMPARISON")
    print("="*80)
    
    max_bullets = max(len(old_bullets), len(new_bullets))
    
    # Header
    print(f"{'CURRENT BULLETS':<38} | {'NEW BULLETS':<38}")
    print("-"*80)
    
    # Bullets
    for i in range(max_bullets):
        old = old_bullets[i] if i < len(old_bullets) else ""
        new = new_bullets[i] if i < len(new_bullets) else ""
        
        # Wrap long bullets
        old_wrapped = _wrap_text(old, 36)
        new_wrapped = _wrap_text(new, 36)
        
        max_lines = max(len(old_wrapped), len(new_wrapped))
        
        for j in range(max_lines):
            old_line = old_wrapped[j] if j < len(old_wrapped) else ""
            new_line = new_wrapped[j] if j < len(new_wrapped) else ""
            
            if j == 0:
                print(f"• {old_line:<36} | • {new_line:<36}")
            else:
                print(f"  {old_line:<36} |   {new_line:<36}")
        
        if i < max_bullets - 1:
            print()
    
    print("="*80 + "\n")


def _wrap_text(text: str, width: int) -> List[str]:
    """Wrap text to specified width"""
    if not text:
        return [""]
    
    words = text.split()
    lines = []
    current_line = []
    current_length = 0
    
    for word in words:
        if current_length + len(word) + 1 <= width:
            current_line.append(word)
            current_length += len(word) + 1
        else:
            if current_line:
                lines.append(" ".join(current_line))
            current_line = [word]
            current_length = len(word)
    
    if current_line:
        lines.append(" ".join(current_line))
    
    return lines if lines else [""]


def confirm_action(message: str) -> bool:
    """
    Get yes/no confirmation from user
    
    Args:
        message: Confirmation message
        
    Returns:
        True if confirmed, False otherwise
    """
    while True:
        response = input(f"{message} (y/n): ").strip().lower()
        if response in ['y', 'yes']:
            return True
        elif response in ['n', 'no']:
            return False
        else:
            print("Please enter 'y' or 'n'")


def get_generator_for_project(project: Project):
    """Get appropriate bullet generator for project type"""
    if project.project_type == 'code':
        return CodeBulletGenerator()
    elif project.project_type == 'visual_media':
        return MediaBulletGenerator()
    elif project.project_type == 'text':
        return TextBulletGenerator()
    else:
        raise ValueError(f"Unknown project type: {project.project_type}")


# ============================================
# MAIN MENU FUNCTIONS
# ============================================

def generate_new_bullets():
    """Generate and store new resume bullets for a project"""
    print("\n" + "="*60)
    print("GENERATE RESUME BULLETS")
    print("="*60)
    
    project = select_project_interactive()
    if not project:
        return
    
    # Ask for number of bullets
    while True:
        try:
            num_bullets = input("\nHow many bullets to generate? (2-5, default 3): ").strip()
            if not num_bullets:
                num_bullets = 3
            else:
                num_bullets = int(num_bullets)
            
            if 2 <= num_bullets <= 5:
                break
            else:
                print("Please enter a number between 2 and 5.")
        except ValueError:
            print("Invalid input. Please enter a number.")
    
    print(f"\nGenerating {num_bullets} bullets for '{project.name}'...")
    
    try:
        # Get appropriate generator
        generator = get_generator_for_project(project)
        
        # Generate bullets and header
        bullets = generator.generate_resume_bullets(project, num_bullets)
        header = generator.generate_project_header(project)
        
        # Score bullets
        scoring = score_all_bullets(bullets, project.project_type)
        ats_score = scoring['overall_score']
        
        # Display generated bullets
        print(f"\n{header}")
        print("-" * 60)
        for i, bullet in enumerate(bullets, 1):
            print(f"{i}. {bullet}")
        print(f"\nOverall ATS Score: {ats_score:.1f}/100")
        
        # Ask to save
        if confirm_action("\nSave these bullets to database?"):
            success = db_manager.save_resume_bullets(
                project_id=project.id,
                bullets=bullets,
                header=header,
                ats_score=ats_score
            )
            
            if success:
                print("✅ Bullets saved successfully!")
            else:
                print("❌ Failed to save bullets.")
        else:
            print("Bullets discarded.")
    
    except Exception as e:
        print(f"❌ Error generating bullets: {e}")
    
    input("\nPress Enter to continue...")


def view_stored_bullets():
    """View stored resume bullets for a project"""
    print("\n" + "="*60)
    print("VIEW STORED BULLETS")
    print("="*60)
    
    project = select_project_interactive()
    if not project:
        return
    
    bullets_data = project.bullets
    
    if not bullets_data:
        print(f"\nNo bullets stored for '{project.name}'.")
        if confirm_action("Generate bullets now?"):
            generate_new_bullets()
        return
    
    # Display bullets
    print(f"\n{bullets_data['header']}")
    print("-" * 60)
    print(f"Generated: {bullets_data['generated_at']}")
    print(f"ATS Score: {bullets_data.get('ats_score', 'N/A')}/100")
    print(f"Number of bullets: {bullets_data['num_bullets']}\n")
    
    for i, bullet in enumerate(bullets_data['bullets'], 1):
        print(f"{i}. {bullet}")
    
    input("\nPress Enter to continue...")


def improve_bullets_menu():
    """Improve existing bullets with analytics"""
    print("\n" + "="*60)
    print("IMPROVE EXISTING BULLETS")
    print("="*60)
    
    project = select_project_interactive()
    if not project:
        return
    
    bullets_data = project.bullets
    
    if not bullets_data:
        print(f"\nNo bullets stored for '{project.name}'.")
        print("Generate bullets first before improving them.")
        input("Press Enter to continue...")
        return
    
    old_bullets = bullets_data['bullets']
    
    # Show improvement options
    print("\nChoose improvement type:")
    print("a) Role-level targeting (Junior/Mid/Senior/Lead)")
    print("b) ATS optimization & scoring")
    print("c) Before/After comparison")
    
    if project.project_type == 'code':
        print("d) Code-specific: Efficiency & technical depth analysis")
    elif project.project_type == 'visual_media':
        print("d) Media-specific: Portfolio impact analysis")
    elif project.project_type == 'text':
        print("d) Text-specific: Writing quality analysis")
    
    print("e) Cancel")
    
    choice = input("\nSelect option: ").strip().lower()
    
    if choice == 'a':
        improve_with_role_level(project, old_bullets)
    elif choice == 'b':
        improve_with_ats(project, old_bullets)
    elif choice == 'c':
        show_before_after(project, old_bullets)
    elif choice == 'd':
        improve_type_specific(project, old_bullets)
    elif choice == 'e':
        return
    else:
        print("Invalid option.")
        input("Press Enter to continue...")


def improve_with_role_level(project: Project, old_bullets: List[str]):
    """Improve bullets with role-level targeting"""
    print("\nSelect target role level:")
    print("1. Junior")
    print("2. Mid-level")
    print("3. Senior")
    print("4. Lead")
    
    role_map = {
        '1': 'junior',
        '2': 'mid',
        '3': 'senior',
        '4': 'lead'
    }
    
    choice = input("Select: ").strip()
    role_level = role_map.get(choice)
    
    if not role_level:
        print("Invalid selection.")
        input("Press Enter to continue...")
        return
    
    print(f"\nGenerating {role_level}-level bullets...")
    
    try:
        generator = get_generator_for_project(project)
        
        # Generate new bullets with role-level context
        role_context = generate_role_context(project, role_level)
        new_bullets = []
        
        for i in range(len(old_bullets)):
            # Use role-appropriate verb
            verb = get_role_appropriate_verb(role_level, project.project_type)
            
            # Generate bullet with role context
            bullets_temp = generator.generate_resume_bullets(project, 1)
            if bullets_temp:
                bullet = bullets_temp[0]
                # Replace verb with role-appropriate one
                words = bullet.split()
                if words:
                    words[0] = verb
                    bullet = ' '.join(words)
                new_bullets.append(bullet)
        
        # Show comparison
        show_side_by_side_comparison(old_bullets, new_bullets)
        
        # Ask to replace
        if confirm_action("Keep new role-targeted bullets?"):
            replace_bullets(project, new_bullets)
        else:
            print("Keeping old bullets.")
    
    except Exception as e:
        print(f"❌ Error improving bullets: {e}")
    
    input("\nPress Enter to continue...")


def improve_with_ats(project: Project, old_bullets: List[str]):
    """Improve bullets with ATS optimization"""
    print("\nAnalyzing ATS scores for current bullets...\n")
    
    # Score each bullet
    for i, bullet in enumerate(old_bullets, 1):
        score_data = calculate_ats_score(bullet, project.project_type)
        print(f"Bullet {i}: {score_data['score']}/100 ({score_data['grade']})")
        print(f"  {bullet}")
        print(f"  Feedback: {score_data['feedback']}\n")
    
    # Overall scoring
    scoring = score_all_bullets(old_bullets, project.project_type)
    print(f"Overall ATS Score: {scoring['overall_score']:.1f}/100")
    print(f"Grade Distribution: {scoring['grade_distribution']}")
    
    input("\nPress Enter to continue...")


def show_before_after(project: Project, old_bullets: List[str]):
    """Show before/after comparison"""
    print("\nGenerating before/after comparisons...\n")
    
    for i, bullet in enumerate(old_bullets, 1):
        comparison = generate_before_after_comparison(project, bullet)
        
        print(f"Bullet {i}:")
        print(f"BEFORE: {comparison['before']['bullet']}")
        print(f"AFTER:  {comparison['after']['bullet']}")
        print(f"Improvement: +{comparison['improvement_percentage']:.0f}%")
        print(f"Changes: {', '.join(comparison['improvements'])}\n")
    
    input("Press Enter to continue...")


def improve_type_specific(project: Project, old_bullets: List[str]):
    """Improve with type-specific analytics"""
    print(f"\nAnalyzing {project.project_type} project...\n")
    
    try:
        if project.project_type == 'code':
            analysis = analyze_code_project_comprehensive(project)
            
            print("CODE ANALYSIS RESULTS:")
            if analysis['efficiency'].get('efficiency_available'):
                eff = analysis['efficiency']
                print(f"  Efficiency: {eff['efficiency_level']} ({eff['avg_efficiency_score']:.1f}/100)")
                print(f"  Suggestion: {eff['bullet_phrase']}")
            
            if analysis['technical_density'].get('density_available'):
                density = analysis['technical_density']
                print(f"  Technical Depth: {density['density_level']}")
                print(f"  Suggestion: {density['bullet_phrase']}")
            
            if analysis['skills'].get('skills_available'):
                skills = analysis['skills']
                print(f"  Top Skills: {', '.join(skills['top_skills'][:3])}")
        
        elif project.project_type == 'visual_media':
            analysis = analyze_media_project_comprehensive(project)
            
            print("MEDIA ANALYSIS RESULTS:")
            if analysis['portfolio_impact'].get('impact_available'):
                impact = analysis['portfolio_impact']
                print(f"  Portfolio Impact: {impact['grade']} ({impact['impact_score']}/100)")
                for insight in impact['insights']:
                    print(f"    {insight}")
            
            if analysis['software_proficiency'].get('proficiency_available'):
                prof = analysis['software_proficiency']
                print(f"  Software Skill: {prof['skill_tier']}")
                print(f"  Recommended verb: {prof['recommended_verb']}")
        
        elif project.project_type == 'text':
            analysis = analyze_text_project_comprehensive(project)
            
            print("TEXT ANALYSIS RESULTS:")
            if analysis['writing_quality'].get('quality_available'):
                quality = analysis['writing_quality']
                print(f"  Writing Quality: {quality['quality_level']} ({quality['quality_score']}/100)")
            
            if analysis['publication_readiness'].get('readiness_available'):
                ready = analysis['publication_readiness']
                print(f"  Publication Ready: {ready['is_job_ready']}")
                print(f"  Readiness Score: {ready['readiness_score']}/100")
        
        print("\nUse this analysis to manually improve your bullets.")
    
    except Exception as e:
        print(f"❌ Error analyzing project: {e}")
    
    input("\nPress Enter to continue...")


def replace_bullets(project: Project, new_bullets: List[str]):
    """Replace old bullets with new ones"""
    try:
        generator = get_generator_for_project(project)
        header = generator.generate_project_header(project)
        scoring = score_all_bullets(new_bullets, project.project_type)
        
        success = db_manager.save_resume_bullets(
            project_id=project.id,
            bullets=new_bullets,
            header=header,
            ats_score=scoring['overall_score']
        )
        
        if success:
            print("✅ Bullets updated successfully!")
        else:
            print("❌ Failed to update bullets.")
    except Exception as e:
        print(f"❌ Error updating bullets: {e}")


def delete_stored_bullets():
    """Delete stored resume bullets"""
    print("\n" + "="*60)
    print("DELETE STORED BULLETS")
    print("="*60)
    
    project = select_project_interactive()
    if not project:
        return
    
    bullets_data = project.bullets
    
    if not bullets_data:
        print(f"\nNo bullets stored for '{project.name}'.")
        input("Press Enter to continue...")
        return
    
    # Show current bullets
    print(f"\nCurrent bullets for '{project.name}':")
    print("-" * 60)
    for i, bullet in enumerate(bullets_data['bullets'], 1):
        print(f"{i}. {bullet}")
    
    # Confirm deletion
    if confirm_action("\nDelete these bullets?"):
        success = db_manager.delete_resume_bullets(project.id)
        
        if success:
            print("✅ Bullets deleted successfully!")
        else:
            print("❌ Failed to delete bullets.")
    else:
        print("Deletion cancelled.")
    
    input("\nPress Enter to continue...")


# ============================================
# MAIN MENU
# ============================================

def run_resume_menu():
    """Main resume bullet generator menu"""
    while True:
        print("\n" + "="*60)
        print("RESUME BULLET GENERATOR")
        print("="*60)
        print("1. Generate Resume Bullets (New)")
        print("2. View Stored Bullets")
        print("3. Improve Existing Bullets")
        print("4. Delete Stored Bullets")
        print("5. Back to Main Menu")
        print("="*60)
        
        choice = input("Select option: ").strip()
        
        if choice == '1':
            generate_new_bullets()
        elif choice == '2':
            view_stored_bullets()
        elif choice == '3':
            improve_bullets_menu()
        elif choice == '4':
            delete_stored_bullets()
        elif choice == '5':
            break
        else:
            print("Invalid option. Please try again.")
            input("Press Enter to continue...")


if __name__ == "__main__":
    run_resume_menu()