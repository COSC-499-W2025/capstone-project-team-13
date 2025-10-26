EXT_SUPERTYPES = {
    # --- code ---
    ".py": "code", ".js": "code", ".ts": "code", ".java": "code",
    ".cpp": "code", ".c": "code", ".rb": "code", ".php": "code",
    ".go": "code", ".rs": "code", ".cs": "code", ".swift": "code",
    
    # --- text / markup ---
    ".txt": "text", ".md": "text", ".html": "text", ".css": "text",
    ".xml": "text",

    # --- data files ---
    ".json": "data", ".csv": "data", ".xlsx": "data", ".sql": "data",

    # --- media ---
    ".png": "media", ".jpg": "media", ".jpeg": "media",
    ".gif": "media", ".mp4": "media", ".mov": "media", ".wav": "media",

    # --- archives ---
    ".zip": "archive", ".rar": "archive", ".7z": "archive",
}
ALLOWED_FORMATS = list(EXT_SUPERTYPES.keys())
