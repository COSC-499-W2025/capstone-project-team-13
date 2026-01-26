import os
import re
from collections import defaultdict
from PyPDF2 import PdfReader
from docx import Document



# Skill dictionary
SKILL_KEYWORDS = {
    "writing_mechanics": [
        "grammar", "syntax", "sentence structure", "paragraph development",
        "clarity", "conciseness", "tone", "voice", "vocabulary", "punctuation",
        "cohesion", "coherence", "transitions", "editing", "proofreading",
        "revising", "spelling", "style consistency", "formatting"
    ],
    "creative_writing": [
        "storytelling", "narrative", "character development", "dialogue",
        "world-building", "imagery", "description", "symbolism", "theme",
        "voice", "perspective", "scene construction", "conflict", "resolution",
        "poetic devices", "metaphor", "alliteration", "emotion", "engagement"
    ],
    "research_writing": [
        "research", "data collection", "analysis",
        "synthesis", "argumentation", "reasoning", "thesis", "evidence",
        "citation", "referencing", "literature review", "methodology",
        "results", "discussion", "conclusion", "formal tone", "academic"
    ],
    "content_writing": [
        "SEO", "keywords", "blog", "article", "headline", "hook",
        "copywriting", "CTA", "call to action", "audience", "brand voice",
        "social media", "marketing", "readability", "repurposing", "web content"
    ],
    "critical_thinking": [
        "analyze", "evaluate", "synthesize", "compare", "contrast", "draw conclusions", 
        "critically assess", "critical thinking"
    ],
    "communication": [
        "feedback", "peer review", "collaboration", "discussion",
        "clarity", "audience awareness", "tone adjustment", "response",
        "adaptability"
    ],
    "technical_writing": [
        "manual", "instructions", "specification", "process", "policy",
        "documentation", "procedure", "simplify", "technical", "software"
    ],
    "journalistic_writing": [
        "interview", "fact-checking", "reporting", "objectivity",
        "source evaluation", "news", "event summary", "investigation"
    ],
    "organization": [
        "outline", "planning", "hierarchy", "logical flow",
        "structure", "draft tracking", "version control",
        "deadline", "revision management", "prioritization", "portfolio"
    ]
}

def extract_text(file_path):
    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".txt":
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    elif ext == ".docx":
        try:
            doc = Document(file_path)
            return "\n".join([p.text for p in doc.paragraphs])
        except Exception as e:
            print(f"Error reading DOCX {file_path}: {e}")
            return ""
    elif ext == ".pdf":
        try:
            reader = PdfReader(file_path)
            text = ""
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
            return text
        except Exception as e:
            print(f"Error reading PDF {file_path}: {e}")
            return ""
    else:
        return ""


def count_keyword_matches(text: str, keywords: list[str]) -> int:
    """
    Counts both single-word and multi-word keyword occurrences in text.
    """
    text = text.lower()
    count = 0

    for kw in keywords:
        kw = kw.lower()
        if " " in kw:
            # Match full phrase
            count += len(re.findall(rf"\b{re.escape(kw)}\b", text))
        else:
            # Match single word
            count += len(re.findall(rf"\b{kw}\b", text))

    return count

def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower()).strip()


# Skill Analysis - Single Document

def analyze_document_for_skills(file_path):
    """
    Analyze a single document and return ranked skill list.
    
    Args:
        file_path: Path to a single document file
    
    Returns:
        List of tuples: [(skill, count), ...] sorted by count descending
    """
    skill_counts = defaultdict(int)
    
    # Extract text from the document
    text = extract_text(file_path)
    
    if not text:
        return []
    
    words = re.findall(r"\b[a-z]+\b", text.lower())
    
    # Count matches for each skill
    for skill, keywords in SKILL_KEYWORDS.items():
        lower_keywords = [k.lower() for k in keywords]
        matches = count_keyword_matches(text, keywords)
        if matches > 0:
            skill_counts[skill] = matches
    
    # Filter zero-count skills and sort
    final_skills = sorted(
        [(s, c) for s, c in skill_counts.items() if c > 0],
        key=lambda x: x[1],
        reverse=True
    )
    
    return final_skills


# Skill Analysis - Folder

def analyze_folder_for_skills(folder_path):
    """
    Analyze all documents in a folder and return ranked skill list.
    Implements:
        - Words can count for multiple skills
        - Between overlapping skills sharing words, keep only the highest count
    Returns a list of tuples: [(skill, count), ...] sorted by count descending
    """
    skill_counts = defaultdict(int)
    word_to_skills = defaultdict(list)

    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        if not os.path.isfile(file_path):
            continue
        if file_path.endswith((".txt", ".pdf", ".docx")):
            text = extract_text(file_path)
            words = re.findall(r"\b[a-z]+\b", text.lower())

            # Count matches for each skill
            for skill, keywords in SKILL_KEYWORDS.items():
                lower_keywords = [k.lower() for k in keywords]
                matches = sum(word in lower_keywords for word in words)
                if matches > 0:
                    skill_counts[skill] += matches
                    for word in set(words) & set(lower_keywords):
                        word_to_skills[word].append(skill)

    # Handle overlapping skills: only keep the highest count in overlapping groups
    overlapping_groups = []
    seen_skills = set()
    for skills in word_to_skills.values():
        skills_set = set(skills)
        if len(skills_set) > 1 and not skills_set.issubset(seen_skills):
            overlapping_groups.append(skills_set)
            seen_skills.update(skills_set)

    for group in overlapping_groups:
        max_skill = max(group, key=lambda s: skill_counts[s])
        for s in group:
            if s != max_skill:
                skill_counts[s] = 0

    # Filter zero-count skills and sort
    final_skills = sorted(
        [(s, c) for s, c in skill_counts.items() if c > 0],
        key=lambda x: x[1],
        reverse=True
    )

    return final_skills