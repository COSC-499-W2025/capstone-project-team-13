"""
Integration module for user configuration system
Connects the new config storage with existing consent prompts
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.Databases.database import db_manager


from src.Databases.user_config import ConfigManager, UserConfig
from datetime import datetime, timezone

config_manager = ConfigManager(db_manager)
def request_and_store_basic_consent() -> bool:
    """
    Request basic file access consent and store result in database
    
    Returns:
        bool: True if consent granted, False otherwise
    """
    config = config_manager.get_or_create_config()
    
    # Check if consent already granted
    if config.basic_consent_granted:
        print("✓ You have previously granted file access consent.")
        print(f"  Granted on: {config.basic_consent_timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Ask if they want to change it
        response = input("\nDo you want to revoke this consent? (yes/no): ").strip().lower()
        if response == 'yes':
            config_manager.revoke_basic_consent()
            print("✗ File access consent revoked. Exiting.")
            return False
        return True
    
    # Request new consent
    print("=" * 70)
    print("FILE ACCESS CONSENT REQUIRED")
    print("=" * 70)
    print("\nThis application would like to access your data and computer files.")
    print("\nBy granting consent, you allow the application to:")
    print("  • Read files from folders you specify")
    print("  • Extract metadata (file names, dates, sizes)")
    print("  • Analyze file contents for classification")
    print("  • Store extracted information in a local database")
    print("\nYour data:")
    print("  • Stays on your local machine")
    print("  • Is never transmitted to external servers (unless AI features enabled)")
    print("  • Can be deleted at any time")
    print()
    
    while True:
        response = input("Grant file access consent? (allow/deny): ").strip().lower()
        
        if response in ['allow', 'yes', 'y']:
            config_manager.grant_basic_consent()
            print("\n✓ Access granted. The application can now proceed.")
            return True
        
        elif response in ['deny', 'no', 'n', "don't allow", 'dont allow']:
            config_manager.revoke_basic_consent()
            print("\n✗ Access denied. The application will not access your data.")
            return False
        
        else:
            print("Invalid response. Please type 'allow' or 'deny'")


def request_and_store_ai_consent() -> bool:
    """
    Request AI/LLM service consent and store result in database
    
    Returns:
        bool: True if consent granted, False otherwise
    """
    config = config_manager.get_or_create_config()
    
    # Check if consent already granted
    if config.ai_consent_granted:
        print("✓ You have previously granted AI service consent.")
        print(f"  Granted on: {config.ai_consent_timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"  Current provider: {config.ai_provider}")
        print(f"  Current model: {config.ai_model}")
        
        # Ask if they want to change it
        response = input("\nDo you want to revoke AI consent? (yes/no): ").strip().lower()
        if response == 'yes':
            config_manager.revoke_ai_consent()
            print("✗ AI service consent revoked.")
            return False
        return True
    
    # Request new consent
    print("\n" + "=" * 70)
    print("AI SERVICE CONSENT REQUIRED")
    print("=" * 70)
    print("\nThis software may send text or other inputs to external AI services.")
    print("\nBy proceeding, you agree that:")
    print("  • Data you provide may be temporarily transmitted to an external AI")
    print("  • Data is used solely for analysis within this application")
    print("  • No personal or identifiable information will be shared")
    print("  • You can withdraw consent at any time")
    print("\nAI features enable:")
    print("  • Enhanced project summaries")
    print("  • Intelligent skill extraction")
    print("  • Natural language descriptions")
    print()
    
    while True:
        consent = input("Grant AI service consent? (yes/no): ").strip().lower()
        
        if consent in ['yes', 'y']:
            config_manager.grant_ai_consent()
            print("\n✓ AI consent granted. AI features are now enabled.")
            return True
        
        elif consent in ['no', 'n']:
            config_manager.revoke_ai_consent()
            print("\n✗ AI consent not granted. AI features will be disabled.")
            print("  (Standard analysis features will still work)")
            return False
        
        else:
            print("Invalid response. Please type 'yes' or 'no'")


def configure_privacy_settings():
    """
    Interactive prompt to configure privacy and scanning preferences
    """
    config = config_manager.get_or_create_config()
    
    print("\n" + "=" * 70)
    print("PRIVACY & SCANNING SETTINGS")
    print("=" * 70)
    
    # Anonymous mode
    print("\n1. ANONYMOUS MODE")
    print(f"   Current: {'Enabled' if config.anonymous_mode else 'Disabled'}")
    print("   When enabled: contributor names and personal identifiers are excluded")
    response = input("   Enable anonymous mode? (yes/no/skip): ").strip().lower()
    if response in ['yes', 'y']:
        config_manager.update_config({'anonymous_mode': True})
        print("   ✓ Anonymous mode enabled")
    elif response in ['no', 'n']:
        config_manager.update_config({'anonymous_mode': False})
        print("   ✓ Anonymous mode disabled")
    
    # Storage preferences
    print("\n2. DATA STORAGE PREFERENCES")
    
    response = input("   Store file contents for analysis? (yes/no/skip): ").strip().lower()
    if response in ['yes', 'y']:
        config_manager.update_config({'store_file_contents': True})
    elif response in ['no', 'n']:
        config_manager.update_config({'store_file_contents': False})
    
    response = input("   Store contributor names? (yes/no/skip): ").strip().lower()
    if response in ['yes', 'y']:
        config_manager.update_config({'store_contributor_names': True})
    elif response in ['no', 'n']:
        config_manager.update_config({'store_contributor_names': False})
    
    response = input("   Store full file paths? (yes/no/skip): ").strip().lower()
    if response in ['yes', 'y']:
        config_manager.update_config({'store_file_paths': True})
    elif response in ['no', 'n']:
        config_manager.update_config({'store_file_paths': False})
    
    # Excluded folders
    print("\n3. FOLDER EXCLUSIONS")
    print(f"   Currently excluded: {len(config.excluded_folders)} folders")
    if config.excluded_folders:
        for folder in config.excluded_folders:
            print(f"     - {folder}")
    
    response = input("   Add folders to exclude? (yes/no): ").strip().lower()
    if response in ['yes', 'y']:
        while True:
            folder = input("   Enter folder path (or 'done' to finish): ").strip()
            if folder.lower() == 'done':
                break
            if folder:
                config_manager.add_excluded_folder(folder)
                print(f"   ✓ Added: {folder}")
    
    # Excluded file types
    print("\n4. FILE TYPE EXCLUSIONS")
    print(f"   Currently excluded: {len(config.excluded_file_types)} types")
    if config.excluded_file_types:
        for ext in config.excluded_file_types:
            print(f"     - {ext}")
    
    response = input("   Add file types to exclude? (yes/no): ").strip().lower()
    if response in ['yes', 'y']:
        while True:
            ext = input("   Enter extension (e.g., .log) or 'done': ").strip()
            if ext.lower() == 'done':
                break
            if ext:
                config_manager.add_excluded_file_type(ext)
                print(f"   ✓ Added: {ext}")
    
    # File size limits
    print("\n5. FILE SIZE LIMITS")
    print(f"   Current max size: {config.max_file_size_scan / 1_000_000:.1f} MB")
    response = input("   Change max file size? (yes/no): ").strip().lower()
    if response in ['yes', 'y']:
        try:
            size_mb = float(input("   Enter max size in MB: ").strip())
            size_bytes = int(size_mb * 1_000_000)
            config_manager.update_config({'max_file_size_scan': size_bytes})
            print(f"   ✓ Max file size set to {size_mb} MB")
        except ValueError:
            print("   ✗ Invalid input, keeping current setting")
    
    print("\n✓ Privacy settings configured")


def configure_analysis_preferences():
    """
    Interactive prompt to configure analysis and feature preferences
    """
    config = config_manager.get_or_create_config()
    
    print("\n" + "=" * 70)
    print("ANALYSIS FEATURE PREFERENCES")
    print("=" * 70)
    
    features = {
        'enable_keyword_extraction': 'Keyword Extraction',
        'enable_language_detection': 'Programming Language Detection',
        'enable_framework_detection': 'Framework Detection',
        'enable_collaboration_analysis': 'Collaboration Analysis',
        'enable_duplicate_detection': 'Duplicate File Detection'
    }
    
    print("\nCurrent feature status:")
    for key, name in features.items():
        status = "✓ Enabled" if getattr(config, key) else "✗ Disabled"
        print(f"  {name}: {status}")
    
    print("\nOptions:")
    print("  1. Enable all features")
    print("  2. Disable all features")
    print("  3. Configure individually")
    print("  4. Keep current settings")
    
    choice = input("\nSelect option (1-4): ").strip()
    
    if choice == '1':
        for key in features.keys():
            config_manager.update_config({key: True})
        print("✓ All features enabled")
    
    elif choice == '2':
        for key in features.keys():
            config_manager.update_config({key: False})
        print("✓ All features disabled")
    
    elif choice == '3':
        for key, name in features.items():
            response = input(f"  Enable {name}? (yes/no/skip): ").strip().lower()
            if response in ['yes', 'y']:
                config_manager.update_config({key: True})
            elif response in ['no', 'n']:
                config_manager.update_config({key: False})
    
    print("\n✓ Analysis preferences configured")


def show_current_configuration():
    """
    Display current configuration summary
    """
    config = config_manager.get_or_create_config()
    
    print("\n" + "=" * 70)
    print("CURRENT CONFIGURATION")
    print("=" * 70)
    
    # Consent status
    print("\n📋 CONSENT STATUS:")
    print(f"  File Access: {'✓ Granted' if config.basic_consent_granted else '✗ Not granted'}")
    if config.basic_consent_granted:
        print(f"    Granted: {config.basic_consent_timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
    
    print(f"  AI Services: {'✓ Granted' if config.ai_consent_granted else '✗ Not granted'}")
    if config.ai_consent_granted:
        print(f"    Granted: {config.ai_consent_timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"    Provider: {config.ai_provider}")
        print(f"    Model: {config.ai_model}")
    
    # Privacy settings
    print("\n🔒 PRIVACY SETTINGS:")
    print(f"  Anonymous Mode: {'✓ Enabled' if config.anonymous_mode else '✗ Disabled'}")
    print(f"  Store File Contents: {'Yes' if config.store_file_contents else 'No'}")
    print(f"  Store Contributor Names: {'Yes' if config.store_contributor_names else 'No'}")
    print(f"  Store File Paths: {'Yes' if config.store_file_paths else 'No'}")
    
    if config.excluded_folders:
        print(f"  Excluded Folders: {len(config.excluded_folders)}")
        for folder in config.excluded_folders[:3]:
            print(f"    - {folder}")
        if len(config.excluded_folders) > 3:
            print(f"    ... and {len(config.excluded_folders) - 3} more")
    
    if config.excluded_file_types:
        print(f"  Excluded File Types: {', '.join(config.excluded_file_types)}")
    
    # Scanning preferences
    print("\n🔍 SCANNING PREFERENCES:")
    print(f"  Auto-detect Project Type: {'Yes' if config.auto_detect_project_type else 'No'}")
    print(f"  Scan Nested Folders: {'Yes' if config.scan_nested_folders else 'No'}")
    print(f"  Max Scan Depth: {config.max_scan_depth}")
    print(f"  Max File Size: {config.max_file_size_scan / 1_000_000:.1f} MB")
    print(f"  Skip Hidden Files: {'Yes' if config.skip_hidden_files else 'No'}")
    
    # Analysis features
    print("\n⚙️  ANALYSIS FEATURES:")
    print(f"  Keyword Extraction: {'✓ Enabled' if config.enable_keyword_extraction else '✗ Disabled'}")
    print(f"  Language Detection: {'✓ Enabled' if config.enable_language_detection else '✗ Disabled'}")
    print(f"  Framework Detection: {'✓ Enabled' if config.enable_framework_detection else '✗ Disabled'}")
    print(f"  Collaboration Analysis: {'✓ Enabled' if config.enable_collaboration_analysis else '✗ Disabled'}")
    print(f"  Duplicate Detection: {'✓ Enabled' if config.enable_duplicate_detection else '✗ Disabled'}")
    
    # UI preferences
    print("\n🎨 INTERFACE PREFERENCES:")
    print(f"  Theme: {config.theme}")
    print(f"  Language: {config.language}")
    print(f"  Show Progress Indicators: {'Yes' if config.show_progress_indicators else 'No'}")
    
    # Output preferences
    print("\n📤 OUTPUT PREFERENCES:")
    print(f"  Default Export Format: {config.default_export_format}")
    print(f"  Summary Detail Level: {config.summary_detail_level}")
    print(f"  Resume Max Projects: {config.resume_max_projects}")
    
    print("\n" + "=" * 70)


def quick_setup_wizard():
    """
    Quick setup wizard for first-time users
    """
    print("\n" + "=" * 70)
    print("WELCOME TO DIGITAL ARTIFACT MINING SOFTWARE")
    print("=" * 70)
    print("\nLet's get you set up with a quick configuration...")
    
    # Step 1: Basic consent
    print("\n--- Step 1 of 4: File Access ---")
    if not request_and_store_basic_consent():
        print("\nSetup cancelled. File access is required to use this application.")
        return False
    
    # Step 2: AI consent
    print("\n--- Step 2 of 4: AI Features (Optional) ---")
    print("AI features are optional and can enhance your experience.")
    response = input("Configure AI features now? (yes/no): ").strip().lower()
    if response in ['yes', 'y']:
        request_and_store_ai_consent()
    else:
        print("Skipping AI configuration (can be enabled later)")
    
    # Step 3: Privacy quick config
    print("\n--- Step 3 of 4: Privacy Settings ---")
    print("Do you want to configure privacy settings?")
    print("  1. Use recommended defaults (balanced)")
    print("  2. Maximum privacy (minimal data storage)")
    print("  3. Configure manually")
    print("  4. Skip for now")
    
    choice = input("\nSelect option (1-4): ").strip()
    
    if choice == '1':
        print("✓ Using recommended defaults")
    elif choice == '2':
        config_manager.update_config({
            'anonymous_mode': True,
            'store_file_contents': False,
            'store_contributor_names': False
        })
        print("✓ Maximum privacy settings applied")
    elif choice == '3':
        configure_privacy_settings()
    
    # Step 4: Analysis features
    print("\n--- Step 4 of 4: Analysis Features ---")
    print("Enable all analysis features?")
    print("  (Keyword extraction, language detection, framework detection, etc.)")
    
    response = input("Enable all features? (yes/no): ").strip().lower()
    if response in ['yes', 'y']:
        features = {
            'enable_keyword_extraction': True,
            'enable_language_detection': True,
            'enable_framework_detection': True,
            'enable_collaboration_analysis': True,
            'enable_duplicate_detection': True
        }
        config_manager.update_config(features)
        print("✓ All features enabled")
    else:
        print("Using default feature settings")
    
    print("\n" + "=" * 70)
    print("✓ SETUP COMPLETE!")
    print("=" * 70)
    print("\nYou can modify these settings anytime from the Settings menu.")
    input("\nPress Enter to continue...")
    
    return True


# Convenience functions for checking config status
def has_basic_consent() -> bool:
    """Check if basic file access consent is granted"""
    config = config_manager.get_or_create_config()
    return config.basic_consent_granted


def has_ai_consent() -> bool:
    """Check if AI service consent is granted"""
    config = config_manager.get_or_create_config()
    return config.ai_consent_granted and config.ai_enabled


def is_anonymous_mode() -> bool:
    """Check if anonymous mode is enabled"""
    config = config_manager.get_or_create_config()
    return config.anonymous_mode


def get_ai_config() -> dict:
    """Get AI configuration as dictionary"""
    config = config_manager.get_or_create_config()
    return {
        'enabled': config.ai_enabled,
        'provider': config.ai_provider,
        'model': config.ai_model,
        'cache_enabled': config.ai_cache_enabled,
        'max_tokens': config.ai_max_tokens,
        'temperature': config.ai_temperature
    }


if __name__ == "__main__":
    # Run quick setup wizard if executed directly
    quick_setup_wizard()