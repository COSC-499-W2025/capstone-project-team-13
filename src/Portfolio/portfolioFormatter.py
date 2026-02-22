"""
Portfolio Data Formatter
Prepares project data from database for portfolio display frontend.

Design choice (per your request):
- There is ONLY "portfolio" output.
- A "summary" is INCLUDED inside the portfolio JSON (no separate generate_summary command).

Usage:
    from src.Portfolio.portfolioFormatter import PortfolioFormatter

    formatter = PortfolioFormatter()

    portfolio_data = formatter.get_portfolio_data()
    project_detail = formatter.get_project_detail(project_id=1)
    filtered = formatter.get_filtered_projects(project_type='code', search='python')
"""

import sys
import os
from typing import List, Dict, Any, Optional
from datetime import datetime
from copy import deepcopy

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from src.Databases.database import db_manager, Project

# OPTIONAL: If you have your summarize_projects module, we'll use it to pick "top projects"
# and generate a stronger portfolio summary. If not available, we gracefully fall back.
try:
    from src.Summary.summarizer import summarize_projects  # adjust path if needed
except Exception:
    summarize_projects = None


class PortfolioFormatter:
    """Format database projects into portfolio-ready JSON structures (with embedded summary)."""

    def __init__(self):
        self.db = db_manager

    # -------------------------
    # Helpers
    # -------------------------
    def _as_list(self, value) -> List[str]:
        """Normalize DB values to a clean list of strings."""
        if not value:
            return []
        if isinstance(value, list):
            return [str(v).strip() for v in value if str(v).strip()]
        if isinstance(value, str):
            # supports "a, b, c" storage
            return [v.strip() for v in value.split(",") if v.strip()]
        try:
            return [str(v).strip() for v in list(value) if str(v).strip()]
        except Exception:
            return [str(value).strip()] if str(value).strip() else []

    def _format_date(self, date_obj) -> Optional[str]:
        """Format datetime to readable string."""
        if not date_obj:
            return None
        if hasattr(date_obj, "strftime"):
            return date_obj.strftime("%B %Y")  # e.g., "March 2024"
        return str(date_obj)

    def _format_size(self, size_bytes: Optional[int]) -> str:
        """Format file size to human-readable format."""
        if not size_bytes:
            return "0 B"

        units = ["B", "KB", "MB", "GB", "TB"]
        size = float(size_bytes)
        unit_index = 0

        while size >= 1024 and unit_index < len(units) - 1:
            size /= 1024
            unit_index += 1

        return f"{size:.1f} {units[unit_index]}"

    def _safe_float01(self, x) -> float:
        """Clamp to [0,1]."""
        try:
            v = float(x)
        except Exception:
            v = 0.0
        return max(0.0, min(1.0, v))

    # -------------------------
    # Metrics / Cards / Detail
    # -------------------------
    def _get_project_metrics(self, project: Project) -> Dict[str, Any]:
        """Extract metrics based on project type"""
        metrics = {}

        ptype = (project.project_type or "").lower()

        if ptype == 'code':
            metrics = {
                'lines_of_code': project.lines_of_code or 0,
                'file_count': project.file_count or 0,
                'contributors': len(self.db.get_contributors_for_project(project.id)),
                'languages': len(self._as_list(project.languages))
            }

        elif ptype in ['visual_media', 'media']:
            metrics = {
                'file_count': project.file_count or 0,
                'total_size': self._format_size(project.total_size_bytes),
                'software_tools': len(self._as_list(project.languages)),
                'skills': len(self._as_list(project.skills))
            }

        # TEXT PROJECTS
        elif ptype in ['text', 'text_document', 'document']:
            metrics = {
                'word_count': project.word_count or 0,
                'file_count': project.file_count or 0,
                'document_types': len(self._as_list(project.tags)),
                'skills': len(self._as_list(project.skills))
            }

        # fallback: show anything available
        else:
            metrics = {
                'lines_of_code': project.lines_of_code or 0,
                'word_count': project.word_count or 0,
                'file_count': project.file_count or 0
            }

        return metrics


    def _format_project_card(self, project: Project) -> Dict[str, Any]:
        """Format project for card/list view in portfolio."""

        # Description: prefer AI, then custom, then default, then fallback
        description = None
        ai_desc = getattr(project, "ai_description", None)

        if ai_desc:
            description = ai_desc
        elif getattr(project, "custom_description", None):
            description = project.custom_description
        elif getattr(project, "description", None):
            description = project.description
        else:
            skills = self._as_list(project.skills)
            description = (
                f"A {project.project_type} project showcasing "
                f"{', '.join(skills[:3]) if skills else 'various skills'}."
            )

        # Top skills (limit to 6)
        skills = self._infer_skills(project)
        top_skills = skills[:6]

        # Tech stack (languages + frameworks)
        languages = self._as_list(project.languages)
        frameworks = self._as_list(project.frameworks)
        tech_stack = (languages + frameworks)[:6]


        return {
            "id": project.id,
            "name": project.name,
            "type": project.project_type,
            "description": description,
            "tech_stack": tech_stack,
            "skills": top_skills,
            "metrics": self._get_project_metrics(project),
            "date": self._format_date(project.date_modified or project.date_created),
            "importance_score": project.importance_score or 0,
            "is_featured": bool(project.is_featured),
            "is_hidden": bool(getattr(project, "is_hidden", False)),
            "languages": self._as_list(project.languages),
            "frameworks": self._as_list(project.frameworks),
            "total_size_bytes": project.total_size_bytes,  

        }

    def _format_project_detail(self, project: Project) -> Dict[str, Any]:
        """Format complete project details for detail view."""

        descriptions = {
            "ai_generated": getattr(project, "ai_description", None),
            "custom": getattr(project, "custom_description", None),
            "default": getattr(project, "description", None),
        }

        contributors = self.db.get_contributors_for_project(project.id)
        contributors_data = [
            {
                "name": c.name,
                "commits": c.commit_count,
                "contribution_percent": c.contribution_percent,
            }
            for c in contributors
        ]

        keywords = self.db.get_keywords_for_project(project.id)
        keywords_data = [
            {"keyword": k.keyword, "score": k.score, "category": k.category}
            for k in keywords[:20]
        ]

        bullets_data = None
        if getattr(project, "bullets", None):
            bullets_data = {
                "header": project.bullets.get("header"),
                "bullets": project.bullets.get("bullets", []),
                "ats_score": project.bullets.get("ats_score"),
            }

        return {
            "id": project.id,
            "name": project.name,
            "type": project.project_type,
            "collaboration_type": getattr(project, "collaboration_type", None),

            # Descriptions
            "descriptions": descriptions,

            # Tech details (normalized to lists)
            "languages": self._as_list(project.languages),
            "frameworks": self._as_list(project.frameworks),
            "skills": self._as_list(project.skills),
            "tags": self._as_list(project.tags),

            # Metrics
            "metrics": {
                "lines_of_code": project.lines_of_code,
                "word_count": project.word_count,
                "file_count": project.file_count,
                "total_size": self._format_size(project.total_size_bytes),
                "importance_score": project.importance_score,
            },

            # Dates
            "dates": {
                "created": self._format_date(project.date_created),
                "modified": self._format_date(project.date_modified),
                "scanned": self._format_date(getattr(project, "date_scanned", None)),
            },

            # Additional data
            "contributors": contributors_data,
            "keywords": keywords_data,
            "resume_bullets": bullets_data,
            "user_role": getattr(project, "user_role", None),

            # Flags
            "is_featured": bool(project.is_featured),
            "is_hidden": bool(getattr(project, "is_hidden", False)),
        }

    # -------------------------
    # Embedded portfolio summary (NO separate summary command)
    # -------------------------
    def _build_summary_input(self, projects: List[Project]) -> List[Dict[str, Any]]:
        """
        Builds dicts shaped for summarize_projects(), using DB fields you already have.

        NOTE:
        - summarize_projects expects success_score and contribution_score in [0,1].
        - If you don't have those yet, we derive reasonable defaults so it works today.
        """
        out: List[Dict[str, Any]] = []
        for p in projects:
            ptype = (p.project_type or "unknown").lower()

            # time_spent: use a meaningful intensity measure per type
            if ptype == "code":
                time_spent = float(p.lines_of_code or 0)
                activity_type = "code"
            elif ptype == "text":
                time_spent = float(p.word_count or 0)
                activity_type = "text"
            elif ptype == "visual_media":
                time_spent = float(p.total_size_bytes or 0)
                activity_type = "media"  # summarize_projects prints "media"
            else:
                time_spent = float(p.file_count or 0)
                activity_type = ptype

            # success_score: derive from importance_score (0..100 -> 0..1)
            success_score = self._safe_float01((p.importance_score or 0) / 100.0)

            # contribution_score: if you have contributors, use that count as a weak signal
            # (replace later with real contributor percent/commits logic if you want)
            contrib_count = len(self.db.get_contributors_for_project(p.id))
            # simple clamp: 1 contributor -> 0.4, 2 -> 0.6, 3 -> 0.75, 4+ -> 0.9
            if contrib_count <= 1:
                contribution_score = 0.4
            elif contrib_count == 2:
                contribution_score = 0.6
            elif contrib_count == 3:
                contribution_score = 0.75
            else:
                contribution_score = 0.9

            skills = self._as_list(p.skills)

            out.append(
                {
                    "project_name": p.name,
                    "activity_type": activity_type,
                    "time_spent": time_spent,
                    "success_score": success_score,
                    "contribution_score": contribution_score,
                    "skills": skills,
                    # extra fields if your summarizer uses them
                    "duration_days": None,
                    "first_activity_date": None,
                    "last_activity_date": None,
                }
            )
        return out

    def _generate_portfolio_summary(self, projects: List[Project]) -> Dict[str, Any]:
        if not projects:
            return {"text": "No projects available.", "highlights": []}

        # Category breakdown
        by_type: Dict[str, int] = {}
        for p in projects:
            ptype = (p.project_type or "unknown").lower()
            by_type[ptype] = by_type.get(ptype, 0) + 1

        # Totals
        total_loc = sum(p.lines_of_code or 0 for p in projects)
        total_words = sum(p.word_count or 0 for p in projects)
        total_files = sum(p.file_count or 0 for p in projects)
        total_media_bytes = sum(p.total_size_bytes or 0 for p in projects if (p.project_type or "").lower() == "visual_media")

        # Date range
        dates = []
        for p in projects:
            for d in [p.date_created, p.date_modified, getattr(p, "date_scanned", None)]:
                if d:
                    dates.append(d)
        earliest = min(dates).date().isoformat() if dates else None
        latest = max(dates).date().isoformat() if dates else None

        # Skills (inferred)
        all_skills = []
        for p in projects:
            all_skills.extend(self._infer_skills(p))

        # Unique skills, preserve order
        unique_skills = []
        seen = set()
        for s in all_skills:
            k = s.lower()
            if k not in seen:
                seen.add(k)
                unique_skills.append(s)

        # Top skills by frequency
        freq: Dict[str, int] = {}
        for s in all_skills:
            freq[s.lower()] = freq.get(s.lower(), 0) + 1
        top_skills = sorted(unique_skills, key=lambda s: freq.get(s.lower(), 0), reverse=True)[:10]

        # Top projects by importance
        top_projects = sorted(projects, key=lambda p: p.importance_score or 0, reverse=True)[:3]
        featured = [p for p in projects if p.is_featured]
        featured = sorted(featured, key=lambda p: p.importance_score or 0, reverse=True)[:3]

        # Category mini-insights
        category_insights = []
        for cat, count in sorted(by_type.items(), key=lambda x: x[1], reverse=True):
            # pick a representative project for that category
            sample = next((p for p in projects if (p.project_type or "unknown").lower() == cat), None)
            sample_skills = self._infer_skills(sample)[:5] if sample else []
            cat_name = cat.replace("_", " ").title()
            if sample_skills:
                category_insights.append(f"{cat_name}: {count} project(s) (common: {', '.join(sample_skills)})")
            else:
                category_insights.append(f"{cat_name}: {count} project(s)")

        # Build text (your requested style, but much richer)
        type_phrase = ", ".join([f"{v} {k.replace('_',' ')}" for k, v in by_type.items()])
        skill_count = len(unique_skills)

        text_lines = []
        text_lines.append(
            f"Portfolio showcasing {len(projects)} projects across {len(by_type)} categories."
        )
        text_lines.append(
            f"Category breakdown: {type_phrase}."
        )
        text_lines.append(
            f"Demonstrates {skill_count} technical skills."
        )

        if top_skills:
            text_lines.append(f"Top skills: {', '.join(top_skills[:8])}.")

        # Activity metrics
        metrics_bits = []
        if total_loc:
            metrics_bits.append(f"{total_loc:,} LOC")
        if total_words:
            metrics_bits.append(f"{total_words:,} words")
        if total_files:
            metrics_bits.append(f"{total_files:,} files")
        if total_media_bytes:
            metrics_bits.append(f"{self._format_size(total_media_bytes)} media")
        if metrics_bits:
            text_lines.append("Total activity: " + " • ".join(metrics_bits) + ".")

        if earliest and latest:
            text_lines.append(f"Timeline: {earliest} → {latest}.")

        highlights = []
        if featured:
            highlights.append(f"Featured: {', '.join([p.name for p in featured])}")
        if top_projects:
            highlights.append(f"Top projects: {', '.join([p.name for p in top_projects])}")
        if category_insights:
            highlights.append("Category insights: " + " | ".join(category_insights[:3]))

        return {
            "text": " ".join(text_lines),
            "highlights": highlights,
            "top_projects": [p.name for p in top_projects],
            "featured_projects": [p.name for p in featured],
            "top_skills": top_skills,
            "unique_skills_count": skill_count,
            "timeline": {"earliest": earliest, "latest": latest},
            "totals": {
                "lines_of_code": total_loc,
                "words": total_words,
                "files": total_files,
                "media_bytes": total_media_bytes,
            },
            "by_type": by_type,
        }


    def _calculate_portfolio_stats(self, projects: List[Project]) -> Dict[str, Any]:
        """Calculate overall portfolio statistics."""
        total_projects = len(projects)
        if total_projects == 0:
            return {
                "total_projects": 0,
                "by_type": {},
                "total_lines_of_code": 0,
                "total_files": 0,
                "total_skills": 0,
                "unique_skills": [],
                "avg_importance_score": 0,
                "featured_count": 0,
            }

        by_type: Dict[str, int] = {}
        all_skills = set()

        for p in projects:
            ptype = p.project_type or "unknown"
            by_type[ptype] = by_type.get(ptype, 0) + 1
            all_skills.update(self._as_list(p.skills))

        total_loc = sum(p.lines_of_code or 0 for p in projects)
        total_files = sum(p.file_count or 0 for p in projects)
        avg_importance = sum(p.importance_score or 0 for p in projects) / total_projects

        return {
            "total_projects": total_projects,
            "by_type": by_type,
            "total_lines_of_code": total_loc,
            "total_files": total_files,
            "total_skills": len(all_skills),
            "unique_skills": sorted(list(all_skills)),
            "avg_importance_score": round(avg_importance, 2),
            "featured_count": sum(1 for p in projects if p.is_featured),
        }

    # -------------------------
    # Public API
    # -------------------------
    def get_portfolio_data(self, include_hidden: bool = False) -> Dict[str, Any]:
        """
        Get complete portfolio data (includes an embedded summary).

        Returns:
            {
                'summary': {...},
                'projects': [...],
                'stats': {...},
                'total_projects': int,
                'generated_at': iso str
            }
        """
        projects = self.db.get_all_projects(include_hidden=include_hidden)

        # print("DEBUG projects:", len(projects))
        # if projects:
        #     p = projects[0]
        #     print("DEBUG name:", p.name)
        #     print("DEBUG _skills raw:", getattr(p, "_skills", None))
        #     print("DEBUG skills property:", p.skills)
        #     print("DEBUG _languages raw:", getattr(p, "_languages", None))
        #     print("DEBUG languages property:", p.languages)

        formatted_projects = [self._format_project_card(p) for p in projects]
        formatted_projects.sort(key=lambda x: x["importance_score"], reverse=True)

        stats = self._calculate_portfolio_stats(projects)
        summary = self._generate_portfolio_summary(projects)

        return {
            "summary": summary,  # <-- embedded summary INSIDE portfolio
            "projects": formatted_projects,
            "stats": stats,
            "total_projects": len(formatted_projects),
            "generated_at": datetime.now().isoformat(),
        }

    def get_project_detail(self, project_id: int) -> Optional[Dict[str, Any]]:
        """Get detailed information for a single project."""
        project = self.db.get_project(project_id)
        if not project:
            return None
        return self._format_project_detail(project)

    def get_filtered_projects(
        self,
        project_type: Optional[str] = None,
        search: Optional[str] = None,
        min_importance: Optional[float] = None,
        featured_only: bool = False,
    ) -> Dict[str, Any]:
        """
        Get filtered projects (cards).

        Args:
            project_type: Filter by type ('code', 'visual_media', 'text')
            search: Search in project name, description, skills
            min_importance: Minimum importance score
            featured_only: Only return featured projects
        """
        projects = self.db.get_all_projects(include_hidden=False)
        filtered = projects

        if project_type:
            filtered = [p for p in filtered if (p.project_type or "").lower() == project_type.lower()]

        if featured_only:
            filtered = [p for p in filtered if p.is_featured]

        if min_importance is not None:
            filtered = [p for p in filtered if (p.importance_score or 0) >= min_importance]

        if search:
            s = search.lower()
            filtered = [
                p
                for p in filtered
                if (
                    (p.name and s in p.name.lower())
                    or (getattr(p, "description", None) and s in p.description.lower())
                    or (getattr(p, "custom_description", None) and s in p.custom_description.lower())
                    or (getattr(p, "ai_description", None) and s in p.ai_description.lower())
                    or any(s in skill.lower() for skill in self._as_list(p.skills))
                )
            ]

        formatted = [self._format_project_card(p) for p in filtered]
        formatted.sort(key=lambda x: x["importance_score"], reverse=True)

        return {
            "projects": formatted,
            "total": len(formatted),
            "filters_applied": {
                "type": project_type,
                "search": search,
                "min_importance": min_importance,
                "featured_only": featured_only,
            },
        }

    def export_to_json(self, output_path: str, include_hidden: bool = False) -> str:
        """Export portfolio data to JSON file (includes embedded summary)."""
        import json

        data = self.get_portfolio_data(include_hidden=include_hidden)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        return output_path

    # -------------------------
    # Optional: pretty CLI view
    # -------------------------
    def display_portfolio_view(self):
        """Display portfolio in a beautiful CLI format (portfolio-only, includes embedded summary)."""
        portfolio = self.get_portfolio_data()

        print("\n" + "=" * 80)
        print("📂 PROJECT PORTFOLIO".center(80))
        print("=" * 80 + "\n")

        # Summary
        print("📊 PORTFOLIO SUMMARY")
        print("-" * 80)
        print(f"{portfolio['summary'].get('text', '')}\n")

        highlights = portfolio["summary"].get("highlights", [])
        if highlights:
            print("✨ Highlights:")
            for h in highlights:
                print(f"   • {h}")
            print()

        # Stats
        stats = portfolio["stats"]
        print("📈 STATISTICS")
        print("-" * 80)
        print(f"{'Total Projects:':<30} {stats.get('total_projects', 0)}")
        print(f"{'Featured Projects:':<30} {stats.get('featured_count', 0)}")
        print(f"{'Average Importance Score:':<30} {stats.get('avg_importance_score', 0)}/100")
        print(f"{'Total Lines of Code:':<30} {stats.get('total_lines_of_code', 0):,}")
        print(f"{'Total Files:':<30} {stats.get('total_files', 0):,}")
        print(f"{'Unique Skills:':<30} {stats.get('total_skills', 0)}")

        print(f"\n{'Project Types:':<30}")
        for ptype, count in stats.get("by_type", {}).items():
            emoji = {"code": "💻", "visual_media": "🎨", "text": "📝"}.get(ptype, "📦")
            print(f"   {emoji} {ptype.replace('_', ' ').title():<20} {count}")
        print()

        # Featured first
        print("🏆 FEATURED PROJECTS")
        print("=" * 80 + "\n")

        featured = [p for p in portfolio["projects"] if p.get("is_featured")]
        if not featured:
            print("No featured projects yet.\n")
        else:
            for i, proj in enumerate(featured[:3], 1):
                self._display_project_card(proj, i, featured=True)

        # All projects
        print("\n📋 ALL PROJECTS")
        print("=" * 80 + "\n")
        for i, proj in enumerate(portfolio["projects"][:10], 1):
            self._display_project_card(proj, i, featured=False)

        if len(portfolio["projects"]) > 10:
            print(f"\n... and {len(portfolio['projects']) - 10} more projects")

        # Skills cloud
        unique_skills = stats.get("unique_skills", [])
        if unique_skills:
            print("\n\n🎯 SKILLS PORTFOLIO")
            print("-" * 80)
            skills = unique_skills[:30]
            cols = 3
            rows = (len(skills) + cols - 1) // cols
            for r in range(rows):
                row_skills = []
                for c in range(cols):
                    idx = r + c * rows
                    if idx < len(skills):
                        row_skills.append(f"• {skills[idx]:<25}")
                print("".join(row_skills))

        print("\n" + "=" * 80 + "\n")

    def _display_project_card(self, project: Dict[str, Any], index: int, featured: bool = False):
        """Display a single project card in a portfolio-like CLI layout."""

        # Type emoji
        type_emoji = {
            "code": "💻",
            "visual_media": "🎨",
            "text": "📝"
        }.get(project.get("type"), "📦")

        star = "⭐ " if featured else ""
        name = project.get("name", "<unnamed>")
        desc = (project.get("description") or "").strip()
        ptype = (project.get("type") or "").lower()

        metrics = project.get("metrics", {}) or {}
        skills = project.get("skills", []) or []
        languages = project.get("languages", []) or []
        frameworks = project.get("frameworks", []) or []

        date_str = project.get("date")
        importance = project.get("importance_score", 0) or 0

        # Helper
        def _fmt_list(items, empty="—", max_items=10):
            if not items:
                return empty
            items = [str(x).strip() for x in items if str(x).strip()]
            if not items:
                return empty
            if len(items) > max_items:
                return ", ".join(items[:max_items]) + f", +{len(items) - max_items} more"
            return ", ".join(items)

        # Header
        print(f"{star}{type_emoji} {index}. {name}")
        print("─" * 80)

        # Description
        if desc:
            if len(desc) > 220:
                desc = desc[:217] + "..."
            print(desc)
            print()

        # Skills always shown
        print(f"Skills: { _fmt_list(skills) }")

        # Only show languages/frameworks for CODE projects
        if ptype == "code":
            print(f"Languages: { _fmt_list(languages) }")
            print(f"Frameworks: { _fmt_list(frameworks) }")

        print()

        # Dates
        print("Dates")
        print(f"  • Display Date: {date_str or '—'}")
        print()

        # Metrics
        print("Metrics")

        loc = metrics.get("lines_of_code", 0) or 0
        wc = metrics.get("word_count", 0) or 0
        file_count = metrics.get("file_count", 0) or 0
        total_size = metrics.get("total_size")

        # Show only relevant metrics per type
        if ptype == "code":
            print(f"  • Lines of Code:     {loc:,}")
            print(f"  • Number of Files:   {file_count:,}")
            if total_size:
                print(f"  • Total File Size:   {total_size}")

        elif ptype == "text":
            print(f"  • Word Count:        {wc:,}")
            print(f"  • Number of Files:   {file_count:,}")

        elif ptype == "visual_media":
            print(f"  • Number of Files:   {file_count:,}")
            if total_size:
                print(f"  • Total File Size:   {total_size}")

        else:
            # fallback for unknown types
            print(f"  • Number of Files:   {file_count:,}")



    def _infer_skills(self, project: Project) -> List[str]:
        """
        Build a richer skill list without using keywords.
        Uses only:
        - project.skills
        - project.languages
        - project.frameworks
        """
        raw = []
        raw.extend(self._as_list(getattr(project, "skills", None)))
        raw.extend(self._as_list(getattr(project, "languages", None)))
        raw.extend(self._as_list(getattr(project, "frameworks", None)))

        # Normalize + de-dup (preserve order)
        cleaned = []
        seen = set()
        for s in raw:
            s = str(s).strip()
            if not s:
                continue
            key = s.lower()
            if key in seen:
                continue
            seen.add(key)
            cleaned.append(s)

        return cleaned[:20]
    def get_projects_for_summary_input(self, include_hidden: bool = False) -> List[Dict[str, Any]]:
        """
        Returns project dicts in the shape summarize_projects() expects.
        Uses ONLY DB fields (no keywords).
        """
        projects = self.db.get_all_projects(include_hidden=include_hidden)

        out = []
        for p in projects:
            ptype = (p.project_type or "unknown").lower()

            # activity_type + time_spent mapping
            if ptype == "code":
                activity_type = "code"
                time_spent = float(p.lines_of_code or 0)
            elif ptype == "text":
                activity_type = "text"
                time_spent = float(p.word_count or 0)
            elif ptype == "visual_media":
                activity_type = "media"
                time_spent = float(p.total_size_bytes or 0)
            else:
                activity_type = ptype
                time_spent = float(p.file_count or 0)

            # IMPORTANT: no keywords
            skills = self._as_list(p.skills)

            # If skills is empty, fall back to languages/frameworks ONLY for code projects
            # (still no keywords)
            if not skills and ptype == "code":
                skills = self._as_list(p.languages) + self._as_list(p.frameworks)

            # duration window (you already have a DB function)
            first_date, last_date, duration_days = self.db.get_project_duration(p.id)

            out.append({
                "project_id": p.id,
                "project_name": p.name,
                "activity_type": activity_type,
                "time_spent": time_spent,
                "skills": skills,

                # these are expected by summarize_projects (defaults if missing)
                "success_score": float((p.importance_score or 0) / 100.0),  # 0..1
                "contribution_score": float((p.user_contribution_percent or 100) / 100.0),  # 0..1

                "first_activity_date": first_date,
                "last_activity_date": last_date,
                "duration_days": duration_days,
            })

        return out


if __name__ == "__main__":
    formatter = PortfolioFormatter()
    formatter.display_portfolio_view()
