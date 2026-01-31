"""
Resume Bullet Generator Menu
=============================

Unified interface for generating, viewing, customizing, and managing
resume bullets for projects in the database.

Features:
- Generate bullets for any project type (code/media/text)
- View stored bullets with metadata and ATS scores
- Customize bullets (edit, regenerate, reorder)
- Generate full resume from selected projects
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
from src.Resume.resumeAnalytics import calculate_ats_score, score_all_bullets
from src.Resume.resumeGenerator import generate_full_resume


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
        
        # Display generated bullets
        print("\n" + "="*60)
        print("GENERATED BULLETS")
        print("="*60)
        print(f"{header}\n")
        for i, bullet in enumerate(bullets, 1):
            print(f"{i}. {bullet}")
        
        print("\n" + "-"*60)
        print(f"Overall ATS Score: {scoring['overall_score']:.1f}/100")
        print(f"Bullets with metrics: {scoring['bullets_with_metrics']}/{len(bullets)}")
        print(f"Unique keywords: {scoring['total_keywords']}")
        
        # Ask to save
        if confirm_action("\nSave these bullets to database?"):
            success = db_manager.save_resume_bullets(
                project_id=project.id,
                bullets=bullets,
                header=header,
                ats_score=scoring['overall_score']
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
        input("Press Enter to continue...")
        return
    
    # Display bullets
    print("\n" + "="*60)
    print(f"RESUME BULLETS: {project.name}")
    print("="*60)
    print(f"{bullets_data['header']}\n")
    
    print("Metadata:")
    print(f"Generated: {bullets_data['generated_at']}")
    print(f"ATS Score: {bullets_data.get('ats_score', 'N/A')}/100")
    print(f"Number of bullets: {bullets_data['num_bullets']}\n")
    
    for i, bullet in enumerate(bullets_data['bullets'], 1):
        print(f"{i}. {bullet}")
    
    input("\nPress Enter to continue...")


def customize_bullets_menu():
    """Customize existing bullets (edit, regenerate, reorder)"""
    print("\n" + "="*60)
    print("CUSTOMIZE BULLETS")
    print("="*60)
    
    project = select_project_interactive()
    if not project:
        return
    
    bullets_data = project.bullets
    
    if not bullets_data:
        print(f"\nNo bullets stored for '{project.name}'.")
        print("Generate bullets first before customizing them.")
        input("Press Enter to continue...")
        return
    
    # Customization loop
    while True:
        # Re-fetch bullets from DB each iteration to reflect any changes made by sub-functions
        bullets_data = db_manager.get_resume_bullets(project.id)
        
        if not bullets_data:
            print(f"\nNo bullets stored for '{project.name}' anymore.")
            input("Press Enter to continue...")
            return
        
        bullets = bullets_data['bullets']
        
        print("\n" + "="*60)
        print(f"CURRENT BULLETS: {project.name}")
        print("="*60)
        for i, bullet in enumerate(bullets, 1):
            print(f"{i}. {bullet}")
        
        print("\n" + "="*60)
        print("CUSTOMIZE OPTIONS")
        print("="*60)
        print("a) Edit a specific bullet")
        print("b) Regenerate all bullets")
        print("c) Reorder bullets")
        print("d) View ATS scores")
        print("e) Back to main menu")
        print("="*60)
        
        choice = input("\nSelect option: ").strip().lower()
        
        if choice == 'a':
            edit_bullet(project)
        elif choice == 'b':
            regenerate_all_bullets(project)
        elif choice == 'c':
            reorder_bullets(project)
        elif choice == 'd':
            view_ats_scores(project)
        elif choice == 'e':
            break
        else:
            print("Invalid option. Please try again.")
            input("Press Enter to continue...")


def edit_bullet(project: Project):
    """Edit a specific bullet"""
    bullets_data = db_manager.get_resume_bullets(project.id)
    if not bullets_data:
        print("\nNo bullets found.")
        input("Press Enter to continue...")
        return
    bullets = bullets_data['bullets']
    
    print("\n" + "="*60)
    print("EDIT BULLET")
    print("="*60)
    
    # Show bullets
    for i, bullet in enumerate(bullets, 1):
        print(f"{i}. {bullet}")
    
    # Select bullet to edit
    try:
        choice = input("\nSelect bullet number to edit (or 'c' to cancel): ").strip()
        if choice.lower() == 'c':
            return
        
        bullet_idx = int(choice) - 1
        if bullet_idx < 0 or bullet_idx >= len(bullets):
            print("Invalid bullet number.")
            input("Press Enter to continue...")
            return
    except ValueError:
        print("Invalid input.")
        input("Press Enter to continue...")
        return
    
    # Show current bullet
    print(f"\nCurrent bullet {bullet_idx + 1}:")
    print(f"  {bullets[bullet_idx]}")
    
    # Get new text
    print("\nEnter new bullet text (or press Enter to cancel):")
    new_text = input("> ").strip()
    
    if not new_text:
        print("Edit cancelled.")
        input("Press Enter to continue...")
        return
    
    # Validate new bullet
    if len(new_text.split()) < 5:
        print("❌ Bullet too short (minimum 5 words).")
        input("Press Enter to continue...")
        return
    
    # Show comparison
    print("\n" + "-"*60)
    print(f"OLD: {bullets[bullet_idx]}")
    print(f"NEW: {new_text}")
    print("-"*60)
    
    # Confirm change
    if confirm_action("Save this change?"):
        bullets[bullet_idx] = new_text
        
        # Recalculate ATS score
        scoring = score_all_bullets(bullets, project.project_type)
        
        # Save to database
        success = db_manager.save_resume_bullets(
            project_id=project.id,
            bullets=bullets,
            header=bullets_data['header'],
            ats_score=scoring['overall_score']
        )
        
        if success:
            print("✅ Bullet updated successfully!")
            print(f"New ATS Score: {scoring['overall_score']:.1f}/100")
        else:
            print("❌ Failed to update bullet.")
    else:
        print("Change discarded.")
    
    input("\nPress Enter to continue...")


def regenerate_all_bullets(project: Project):
    """Regenerate all bullets for a project"""
    bullets_data = db_manager.get_resume_bullets(project.id)
    if not bullets_data:
        print("\nNo bullets found.")
        input("Press Enter to continue...")
        return
    old_bullets = bullets_data['bullets']
    num_bullets = len(old_bullets)
    
    print("\n" + "="*60)
    print("REGENERATE ALL BULLETS")
    print("="*60)
    print(f"\nRegenerating {num_bullets} bullets for '{project.name}'...")
    
    try:
        # Get appropriate generator
        generator = get_generator_for_project(project)
        
        # Generate new bullets
        new_bullets = generator.generate_resume_bullets(project, num_bullets)
        header = generator.generate_project_header(project)
        
        # Score new bullets
        new_scoring = score_all_bullets(new_bullets, project.project_type)
        old_scoring = score_all_bullets(old_bullets, project.project_type)
        
        # Show side-by-side comparison
        print("\n" + "="*60)
        print("BULLET COMPARISON")
        print("="*60)
        print(f"{'CURRENT':<45} | {'NEW':<45}")
        print("-"*93)
        
        for i in range(num_bullets):
            old = old_bullets[i] if i < len(old_bullets) else ""
            new = new_bullets[i] if i < len(new_bullets) else ""
            print(f"{i+1}. {old[:42]:<42} | {new[:42]:<42}")
            if len(old) > 42 or len(new) > 42:
                print(f"   {old[42:84] if len(old) > 42 else '':<42} | {new[42:84] if len(new) > 42 else '':<42}")
        
        print("-"*93)
        print(f"ATS Score: {old_scoring['overall_score']:.1f} → {new_scoring['overall_score']:.1f}")
        print()
        
        # Ask to replace
        if confirm_action("Replace current bullets with new ones?"):
            success = db_manager.save_resume_bullets(
                project_id=project.id,
                bullets=new_bullets,
                header=header,
                ats_score=new_scoring['overall_score']
            )
            
            if success:
                print("✅ Bullets regenerated successfully!")
            else:
                print("❌ Failed to save new bullets.")
        else:
            print("Keeping current bullets.")
    
    except Exception as e:
        print(f"❌ Error regenerating bullets: {e}")
    
    input("\nPress Enter to continue...")


def reorder_bullets(project: Project):
    """Reorder bullets by swapping positions"""
    bullets_data = db_manager.get_resume_bullets(project.id)
    if not bullets_data:
        print("\nNo bullets found.")
        input("Press Enter to continue...")
        return
    bullets = bullets_data['bullets']
    
    print("\n" + "="*60)
    print("REORDER BULLETS")
    print("="*60)
    
    # Show bullets
    for i, bullet in enumerate(bullets, 1):
        print(f"{i}. {bullet}")
    
    # Get positions to swap
    try:
        pos1 = input("\nEnter first bullet number (or 'c' to cancel): ").strip()
        if pos1.lower() == 'c':
            return
        pos1 = int(pos1) - 1
        
        pos2 = input("Enter second bullet number: ").strip()
        pos2 = int(pos2) - 1
        
        # Validate positions
        if pos1 < 0 or pos1 >= len(bullets) or pos2 < 0 or pos2 >= len(bullets):
            print("Invalid bullet numbers.")
            input("Press Enter to continue...")
            return
        
        if pos1 == pos2:
            print("Cannot swap bullet with itself.")
            input("Press Enter to continue...")
            return
        
    except ValueError:
        print("Invalid input.")
        input("Press Enter to continue...")
        return
    
    # Show swap preview
    print(f"\nSwapping bullets {pos1+1} and {pos2+1}:")
    print(f"  {pos1+1}. {bullets[pos1]}")
    print(f"  {pos2+1}. {bullets[pos2]}")
    
    # Confirm swap
    if confirm_action("\nConfirm swap?"):
        # Swap bullets
        bullets[pos1], bullets[pos2] = bullets[pos2], bullets[pos1]
        
        # Save to database
        scoring = score_all_bullets(bullets, project.project_type)
        success = db_manager.save_resume_bullets(
            project_id=project.id,
            bullets=bullets,
            header=bullets_data['header'],
            ats_score=scoring['overall_score']
        )
        
        if success:
            print("✅ Bullets reordered successfully!")
        else:
            print("❌ Failed to reorder bullets.")
    else:
        print("Reordering cancelled.")
    
    input("\nPress Enter to continue...")


def view_ats_scores(project: Project):
    """View detailed ATS scores for current bullets"""
    bullets_data = db_manager.get_resume_bullets(project.id)
    if not bullets_data:
        print("\nNo bullets found.")
        input("Press Enter to continue...")
        return
    bullets = bullets_data['bullets']
    
    print("\n" + "="*60)
    print("ATS SCORE ANALYSIS")
    print("="*60)
    
    # Score each bullet
    for i, bullet in enumerate(bullets, 1):
        score_data = calculate_ats_score(bullet, project.project_type)
        print(f"\nBullet {i}: {score_data['score']}/100 ({score_data['grade']})")
        print(f"  {bullet}")
        if score_data['feedback']:
            print(f"  Feedback:")
            for feedback in score_data['feedback']:
                print(f"    {feedback}")
    
    # Overall scoring
    scoring = score_all_bullets(bullets, project.project_type)
    print("\n" + "="*60)
    print(f"Overall ATS Score: {scoring['overall_score']:.1f}/100")
    print(f"Bullets with metrics: {scoring['bullets_with_metrics']}/{len(bullets)}")
    print(f"Unique keywords: {scoring['total_keywords']}")
    
    # Grade distribution
    grade_dist = scoring.get('grade_distribution', {})
    if grade_dist:
        dist_str = ", ".join([f"{grade}: {count}" for grade, count in grade_dist.items() if count > 0])
        print(f"Grade Distribution: {dist_str}")
    
    input("\nPress Enter to continue...")


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
        print("3. Customize Bullets")
        print("4. Generate Full Resume")
        print("5. Delete Stored Bullets")
        print("6. Back to Main Menu")
        print("="*60)
        
        choice = input("Select option: ").strip()
        
        if choice == '1':
            generate_new_bullets()
        elif choice == '2':
            view_stored_bullets()
        elif choice == '3':
            customize_bullets_menu()
        elif choice == '4':
            generate_full_resume()
        elif choice == '5':
            delete_stored_bullets()
        elif choice == '6':
            break
        else:
            print("Invalid option. Please try again.")
            input("Press Enter to continue...")


if __name__ == "__main__":
    run_resume_menu()