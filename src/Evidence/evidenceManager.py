"""
Evidence Manager - Orchestrates evidence extraction and management
Handles both automatic extraction and manual entry of success metrics
"""

import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from pathlib import Path

# Use relative import for your project structure
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from Databases.database import db_manager, Project


class EvidenceManager:
    """
    Manages evidence extraction and storage for projects
    
    Provides methods to:
    - Extract evidence automatically from project files
    - Store and retrieve evidence
    - Add manual metrics, feedback, and achievements
    - Generate evidence summaries
    """
    
    def __init__(self, db=None):
        """
        Initialize evidence manager
        
        Args:
            db: Database manager instance (defaults to global db_manager)
        """
        self.db = db or db_manager
    
    def extract_and_store_evidence(self, project: Project, project_path: str) -> Dict[str, Any]:
        """
        Extract evidence from project files and store in database
        
        Args:
            project: Project object
            project_path: Path to project directory
            
        Returns:
            Dictionary of extracted evidence
        """
        from Evidence.autoExtractor import AutoEvidenceExtractor
        
        try:
            # Extract evidence
            extractor = AutoEvidenceExtractor(project_path)
            evidence = extractor.extract_all_evidence()
            
            # Store in database
            if evidence:
                self.store_evidence(project.id, evidence)
            
            return evidence
        except Exception as e:
            print(f"Error extracting evidence: {e}")
            return {}
    
    def store_evidence(self, project_id: int, evidence: Dict[str, Any]) -> bool:
        """
        Store evidence in database
        
        Args:
            project_id: Project ID
            evidence: Evidence dictionary
            
        Returns:
            True if successful
        """
        # Get existing evidence
        existing = self.get_evidence(project_id)
        
        # Merge with existing evidence
        if existing:
            merged = self._merge_evidence(existing, evidence)
        else:
            merged = evidence
        
        # Convert to JSON string
        evidence_json = json.dumps(merged)
        
        # Update project
        return self.db.update_project(project_id, {'success_evidence': evidence_json})
    
    def get_evidence(self, project_id: int) -> Optional[Dict[str, Any]]:
        """
        Retrieve evidence for a project
        
        Args:
            project_id: Project ID
            
        Returns:
            Evidence dictionary or None
        """
        project = self.db.get_project(project_id)
        if not project or not project.success_evidence:
            return None
        
        try:
            return json.loads(project.success_evidence)
        except json.JSONDecodeError:
            return None
    
    def has_evidence(self, project_id: int) -> bool:
        """
        Check if project has any evidence
        
        Args:
            project_id: Project ID
            
        Returns:
            True if evidence exists
        """
        evidence = self.get_evidence(project_id)
        return evidence is not None and len(evidence) > 0
    
    def _merge_evidence(self, existing: Dict[str, Any], new: Dict[str, Any]) -> Dict[str, Any]:
        """
        Merge new evidence with existing, preferring new values
        
        Args:
            existing: Existing evidence dictionary
            new: New evidence to merge
            
        Returns:
            Merged evidence dictionary
        """
        merged = existing.copy()
        
        for key, value in new.items():
            if key in merged:
                # For lists, extend rather than replace
                if isinstance(value, list) and isinstance(merged[key], list):
                    merged[key].extend(value)
                # For dicts, merge recursively
                elif isinstance(value, dict) and isinstance(merged[key], dict):
                    merged[key].update(value)
                else:
                    # Replace with new value
                    merged[key] = value
            else:
                merged[key] = value
        
        return merged
    
    def add_manual_metric(self, project_id: int, metric_name: str, 
                         value: Any, description: str = "") -> bool:
        """
        Add a manual metric to project evidence
        
        Args:
            project_id: Project ID
            metric_name: Name of metric
            value: Metric value
            description: Optional description
            
        Returns:
            True if successful
        """
        evidence = self.get_evidence(project_id) or {}
        
        if 'manual_metrics' not in evidence:
            evidence['manual_metrics'] = {}
        
        evidence['manual_metrics'][metric_name] = {
            'value': value,
            'description': description,
            'added_at': datetime.now(timezone.utc).isoformat()
        }
        
        return self.store_evidence(project_id, evidence)
    
    def add_feedback(self, project_id: int, text: str, 
                     source: str = "", rating: int = None) -> bool:
        """
        Add feedback/testimonial to project evidence
        
        Args:
            project_id: Project ID
            text: Feedback text
            source: Source of feedback (e.g., "Professor Smith")
            rating: Optional rating (1-5)
            
        Returns:
            True if successful
        """
        evidence = self.get_evidence(project_id) or {}
        
        if 'feedback' not in evidence:
            evidence['feedback'] = []
        
        evidence['feedback'].append({
            'text': text,
            'source': source,
            'rating': rating,
            'added_at': datetime.now(timezone.utc).isoformat()
        })
        
        return self.store_evidence(project_id, evidence)
    
    def add_achievement(self, project_id: int, description: str, 
                       date: str = None) -> bool:
        """
        Add achievement/award to project evidence
        
        Args:
            project_id: Project ID
            description: Achievement description
            date: Date of achievement (YYYY-MM-DD format)
            
        Returns:
            True if successful
        """
        evidence = self.get_evidence(project_id) or {}
        
        if 'achievements' not in evidence:
            evidence['achievements'] = []
        
        evidence['achievements'].append({
            'description': description,
            'date': date,
            'added_at': datetime.now(timezone.utc).isoformat()
        })
        
        return self.store_evidence(project_id, evidence)
    
    def get_summary(self, project_id: int) -> str:
        """
        Generate a human-readable summary of evidence
        
        Args:
            project_id: Project ID
            
        Returns:
            Formatted summary string
        """
        evidence = self.get_evidence(project_id)
        if not evidence:
            return "No evidence recorded for this project."
        
        lines = []
        lines.append("=== PROJECT EVIDENCE SUMMARY ===\n")
        
        # Automatic metrics
        if 'test_coverage' in evidence:
            lines.append(f"Test Coverage: {evidence['test_coverage']}%")
        
        if 'code_quality' in evidence:
            lines.append(f"Code Quality Grade: {evidence['code_quality']}")
        
        # Note: Git statistics (commits, contributors) are shown in the project's
        # existing Git insights and are not duplicated here
        
        if 'readme_badges' in evidence and evidence['readme_badges']:
            lines.append(f"\nBadges: {len(evidence['readme_badges'])} found")
            for badge in evidence['readme_badges']:
                badge_type = f" ({badge.get('type', 'unknown')})" if badge.get('type') else ""
                lines.append(f"  - {badge.get('alt', 'Badge')}{badge_type}")
        
        # Manual metrics
        if 'manual_metrics' in evidence:
            lines.append("\n--- Manual Metrics ---")
            for name, data in evidence['manual_metrics'].items():
                desc = f" - {data['description']}" if data['description'] else ""
                lines.append(f"{name}: {data['value']}{desc}")
        
        # Feedback
        if 'feedback' in evidence and evidence['feedback']:
            lines.append(f"\n--- Feedback ({len(evidence['feedback'])} entries) ---")
            for fb in evidence['feedback']:
                source = f" ({fb['source']})" if fb['source'] else ""
                rating = f" [{fb['rating']}/5]" if fb.get('rating') else ""
                # Truncate long feedback to 100 chars
                text = fb['text'][:100] + '...' if len(fb['text']) > 100 else fb['text']
                lines.append(f"  {text}{source}{rating}")
        
        # Achievements
        if 'achievements' in evidence and evidence['achievements']:
            lines.append(f"\n--- Achievements ({len(evidence['achievements'])} entries) ---")
            for ach in evidence['achievements']:
                date_str = f" ({ach['date']})" if ach.get('date') else ""
                lines.append(f"  - {ach['description']}{date_str}")
        
        return "\n".join(lines)
    
    def clear_evidence(self, project_id: int) -> bool:
        """
        Clear all evidence for a project
        
        Args:
            project_id: Project ID
            
        Returns:
            True if successful
        """
        return self.db.update_project(project_id, {'success_evidence': None})
    
    def get_metric_value(self, project_id: int, metric_name: str) -> Optional[Any]:
        """
        Get a specific metric value from evidence
        
        Args:
            project_id: Project ID
            metric_name: Name of metric to retrieve
            
        Returns:
            Metric value or None
        """
        evidence = self.get_evidence(project_id)
        if not evidence:
            return None
        
        # Check manual metrics first
        if 'manual_metrics' in evidence and metric_name in evidence['manual_metrics']:
            return evidence['manual_metrics'][metric_name]['value']
        
        # Check automatic metrics
        if metric_name in evidence:
            return evidence[metric_name]
        
        # Check nested metrics
        for category in ['readme_metrics', 'git_stats', 'ci_metrics', 'documentation', 'package_info']:
            if category in evidence and isinstance(evidence[category], dict):
                if metric_name in evidence[category]:
                    return evidence[category][metric_name]
        
        return None


# Global instance
evidence_manager = EvidenceManager()