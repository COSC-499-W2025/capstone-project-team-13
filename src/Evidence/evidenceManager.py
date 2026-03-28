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
        try:
            from src.Evidence.autoExtractor import AutoEvidenceExtractor
        except ImportError:
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
    
    def extract_and_store_evidence_text_noai(self, project) -> Dict[str, Any]:
        """Extract evidence from a text project without AI, using file metadata only."""
        from pathlib import Path

        extracted: Dict[str, Any] = {}

        word_count = getattr(project, "word_count", None) or 0
        if word_count:
            extracted["word_count"] = word_count
            extracted["estimated_reading_time_min"] = max(1, round(word_count / 200))

        # Infer document type from file extension
        _ext_to_type = {
            ".pdf": "pdf", ".docx": "word", ".doc": "word",
            ".txt": "text", ".md": "markdown", ".tex": "latex",
            ".rtf": "rtf", ".odt": "odt",
        }
        try:
            if project.file_path:
                p = Path(project.file_path)
                if p.is_file():
                    doc_type = _ext_to_type.get(p.suffix.lower())
                    if doc_type:
                        extracted["document_type"] = doc_type
                elif p.is_dir():
                    for f in sorted(p.rglob("*")):
                        if f.is_file() and f.suffix.lower() in _ext_to_type:
                            extracted["document_type"] = _ext_to_type[f.suffix.lower()]
                            break
        except Exception:
            pass

        if extracted:
            self.store_evidence(project.id, extracted)
        return extracted

    def extract_and_store_evidence_media_noai(self, project) -> Dict[str, Any]:
        """Extract evidence from a media project without AI, using file metadata only."""
        from pathlib import Path

        extracted: Dict[str, Any] = {}

        # Tools already detected by the media scanner and stored in project.languages
        tools = getattr(project, "languages", None) or []
        if isinstance(tools, list) and tools:
            extracted["tools_used"] = tools

        # Infer media type and collect file formats from the project path
        _ext_to_media = {
            ".jpg": "image", ".jpeg": "image", ".png": "image", ".gif": "image",
            ".bmp": "image", ".tiff": "image", ".tif": "image", ".webp": "image",
            ".svg": "image", ".psd": "design", ".ai": "design", ".sketch": "design",
            ".xd": "design", ".figma": "design", ".indd": "design",
            ".mp4": "video", ".mov": "video", ".avi": "video", ".mkv": "video",
            ".wmv": "video", ".flv": "video", ".webm": "video",
            ".mp3": "audio", ".wav": "audio", ".flac": "audio", ".aac": "audio",
            ".ogg": "audio", ".m4a": "audio",
            ".blend": "3d", ".obj": "3d", ".fbx": "3d", ".c4d": "3d",
            ".stl": "3d", ".maya": "3d", ".ma": "3d", ".mb": "3d",
        }
        type_counts: Dict[str, int] = {}
        formats: set = set()
        try:
            if project.file_path:
                p = Path(project.file_path)
                files = [p] if p.is_file() else list(p.rglob("*"))
                for f in files:
                    if f.is_file():
                        ext = f.suffix.lower()
                        if ext in _ext_to_media:
                            formats.add(ext.lstrip("."))
                            mtype = _ext_to_media[ext]
                            type_counts[mtype] = type_counts.get(mtype, 0) + 1
        except Exception:
            pass

        if type_counts:
            extracted["media_type"] = max(type_counts, key=type_counts.get)
        if formats:
            extracted["file_formats"] = sorted(formats)

        if extracted:
            self.store_evidence(project.id, extracted)
        return extracted

    def extract_and_store_evidence_text(self, project) -> Dict[str, Any]:
        """Extract evidence from a text project using AI."""
        from src.AI.ai_service import get_ai_service
        import re

        ai = get_ai_service()

        # Gather what we know about the project
        word_count = getattr(project, "word_count", None) or 0
        description = getattr(project, "description", "") or ""
        ai_description = getattr(project, "ai_description", "") or ""
        name = project.name or "Untitled"

        # Try to read content from file for richer extraction
        content_sample = ""
        try:
            if project.file_path:
                from pathlib import Path
                p = Path(project.file_path)
                if p.is_file():
                    content_sample = p.read_text(encoding="utf-8", errors="ignore")[:3000]
                elif p.is_dir():
                    for f in sorted(p.rglob("*"))[:5]:
                        if f.is_file() and f.suffix.lower() in (".txt", ".md", ".docx", ".pdf", ".rtf"):
                            try:
                                content_sample += f.read_text(encoding="utf-8", errors="ignore")[:600]
                            except Exception:
                                pass
        except Exception:
            pass

        context = content_sample or ai_description or description or name

        prompt = f"""Analyze this text/writing project and extract concrete evidence of quality and effort.

Project: {name}
Word count: {word_count if word_count else "unknown"}
Content sample: {context[:2000]}

Return ONLY valid JSON with these fields (omit any field you cannot determine):
{{
  "word_count": <integer or null>,
  "document_type": "<essay|report|thesis|article|story|script|other>",
  "topics": ["<topic1>", "<topic2>"],
  "writing_strengths": ["<strength1>", "<strength2>"],
  "estimated_reading_time_min": <integer>,
  "complexity": "<introductory|intermediate|advanced>",
  "audience": "<general|academic|technical|creative>"
}}"""

        try:
            raw = ai.generate_text(prompt, temperature=0.3)
            text = raw.strip()
            if text.startswith("```"):
                text = text.split("```")[1]
                if text.startswith("json"):
                    text = text[4:]
            extracted = json.loads(text.strip())
        except Exception:
            extracted = {}

        # Always include word_count from DB if AI didn't return one
        if word_count and not extracted.get("word_count"):
            extracted["word_count"] = word_count

        if extracted:
            self.store_evidence(project.id, extracted)
        return extracted

    def extract_and_store_evidence_media(self, project) -> Dict[str, Any]:
        """Extract evidence from a media project using AI."""
        from src.AI.ai_service import get_ai_service

        ai = get_ai_service()
        name = project.name or "Untitled"
        description = getattr(project, "ai_description", "") or getattr(project, "description", "") or ""

        prompt = f"""Analyze this media/creative project and extract concrete evidence of quality and effort.

Project: {name}
Description: {description[:1000]}

Return ONLY valid JSON with these fields (omit any you cannot determine):
{{
  "media_type": "<image|video|audio|animation|other>",
  "themes": ["<theme1>", "<theme2>"],
  "creative_strengths": ["<strength1>", "<strength2>"],
  "tools_used": ["<tool1>"],
  "complexity": "<simple|moderate|complex>"
}}"""

        try:
            raw = ai.generate_text(prompt, temperature=0.3)
            text = raw.strip()
            if text.startswith("```"):
                text = text.split("```")[1]
                if text.startswith("json"):
                    text = text[4:]
            extracted = json.loads(text.strip())
        except Exception:
            extracted = {}

        if extracted:
            self.store_evidence(project.id, extracted)
        return extracted

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