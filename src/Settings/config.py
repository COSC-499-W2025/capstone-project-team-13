EXT_SUPERTYPES = {
    # --- code ---
    ".py": "code", ".js": "code", ".ts": "code", ".java": "code",
    ".cpp": "code", ".c": "code", ".rb": "code", ".php": "code",
    ".go": "code", ".rs": "code", ".cs": "code", ".swift": "code",
    ".html": "code", ".css": "code",
    
    # --- text / markup ---
    ".txt": "text", ".md": "text", ".xml": "text", ".pdf": "text", ".doc": "text", ".docx": "text",



    # --- media ---
    ".png": "media", ".jpg": "media", ".jpeg": "media",
    ".gif": "media", ".mp4": "media", ".mov": "media", ".wav": "media",

}
ALLOWED_FORMATS = list(EXT_SUPERTYPES.keys()) + [".zip"]
